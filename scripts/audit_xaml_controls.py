#!/usr/bin/env python3
"""Nexus application-wide static WPF/XAML inventory and conservative theme guard.

Scans *every* .xaml and .cs file in src/Nexus.App at the EXACT checked-out
upstream source commit. Never changes app source. Not a screenshot or runtime test.

Fail closed when new selectable controls could inherit the b1r8 shared GridView
row template. Nonselectable ItemsControl and dropdowns are inventory/review
findings, not targets for broad auto-retemplating.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path
import re
import sys
from xml.parsers import expat

P = 'http://schemas.microsoft.com/winfx/2006/xaml/presentation'
X = 'http://schemas.microsoft.com/winfx/2006/xaml'
SELECTORS = ('ListView', 'ListBox', 'DataGrid', 'TreeView')
DISPLAY = ('ListView', 'ListBox', 'ItemsControl', 'DataGrid', 'TreeView', 'ComboBox',
           'ContextMenu', 'MenuItem', 'TabControl', 'TabItem')
EXPECTED_SELECTOR_BINDINGS = {
    ('src/Nexus.App/MainWindow.xaml', 'ListView', name) for name in
    ('Processes', 'Games', 'StartupEntries', 'Devices', 'Entries')
} | {('src/Nexus.App/MainWindow.xaml', 'ListBox', 'Restrained')}
DYNAMIC = re.compile(
    r'\bnew\s+(?:[\w.]+\.)?(ListView|ListBox|DataGrid|TreeView|ComboBox|ItemsControl|ContextMenu|MenuItem)\s*[({]'
    r'|\b(?:XamlReader\s*\.\s*(?:Load|Parse)|FrameworkElementFactory)\b'
)
BINDING = re.compile(r'^\{Binding\s+([^,}\s]+)')


def local(qname):
    return qname.rsplit('}', 1)[-1]


class Node:
    __slots__ = ('tag', 'ns', 'attrs', 'children', 'parent', 'line')
    def __init__(self, tag, attrs, parent, line):
        self.tag = local(tag)
        self.ns = tag.rsplit('}', 1)[0] if '}' in tag else ''
        self.attrs = {local(k): v for k, v in attrs.items()}
        self.children = []
        self.parent = parent
        self.line = line
    def descendants(self, tag=None):
        for child in self.children:
            if tag is None or child.tag == tag:
                yield child
            yield from child.descendants(tag)
    def direct(self, tag):
        return any(child.tag == tag for child in self.children)


def parse_xaml(path):
    """Expat gives actual source line numbers; standard library only."""
    parser = expat.ParserCreate(namespace_separator='}')
    stack, roots = [], []
    def start(tag, attrs):
        parent = stack[-1] if stack else None
        node = Node(tag, attrs, parent, parser.CurrentLineNumber)
        if parent is not None:
            parent.children.append(node)
        else:
            roots.append(node)
        stack.append(node)
    def end(tag):
        stack.pop()
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    try:
        parser.Parse(path.read_bytes(), True)
    except expat.ExpatError as exc:
        raise RuntimeError(f'Malformed XAML {path}: {exc}') from exc
    if len(roots) != 1:
        raise RuntimeError(f'Expected exactly one XAML document element: {path}')
    return roots[0]


def binding(node):
    value = node.attrs.get('ItemsSource', '')
    match = BINDING.match(value.strip())
    return match.group(1) if match else value or '(none)'


def is_styled(node, phase):
    """Textual static theme evidence, not a guarantee of runtime style resolution."""
    local_override = (node.direct(node.tag + '.ItemContainerStyle')
                      or 'ItemContainerStyle' in node.attrs)
    if node.tag in ('ListView', 'ListBox'):
        return ('local override + app-wide theme' if local_override else
                'app-wide patched theme' if phase == 'patched' else
                'upstream implicit theme (hover may be pale)')
    if node.tag == 'ItemsControl':
        return 'custom DataTemplate / panel; no built-in selection hover'
    if node.tag in ('ComboBox', 'ContextMenu', 'MenuItem'):
        return 'separate popup/selector theme; manually verify'
    return 'review control-specific row/item template'


def collect(root: Path, phase='patched'):
    app = root/'src/Nexus.App'
    if not app.is_dir():
        raise RuntimeError('Expected checked-out Nexus application root src/Nexus.App')
    paths = sorted(p for p in app.rglob('*.xaml')
                   if not any(x.lower() in ('obj', 'bin') for x in p.relative_to(app).parts))
    if not paths:
        raise RuntimeError('No Nexus application .xaml files found; refusing empty audit')
    controls, source_files, custom, theme_styles, warnings, blockers = [], [], [], {}, [], []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        doc = parse_xaml(path)
        source_files.append(rel)
        all_nodes = [doc, *doc.descendants()]
        for node in all_nodes:
            # Only instance controls, not a ControlTemplate's named prototype or a
            # resource Style/Setter. These are still parsed for styling evidence.
            if node.tag == 'Style' and 'TargetType' in node.attrs and not node.attrs.get('Key'):
                theme_styles.setdefault(node.attrs['TargetType'].strip('{}'), []).append(rel)
            if node.ns != P:
                if node.ns.startswith('clr-namespace:') and '.' not in node.tag:
                    custom.append({'file': rel, 'line': node.line, 'type': node.tag})
                continue
            if node.tag not in DISPLAY:
                continue
            # Don't count display controls within templates as live source instances.
            # Mark these separately in the report when encountered in a template.
            parent = node.parent
            template_defined = False
            while parent:
                if parent.tag in ('DataTemplate', 'ControlTemplate', 'ItemsPanelTemplate'):
                    template_defined = True
                    break
                parent = parent.parent
            record = {
                'file': rel, 'line': node.line, 'type': node.tag,
                'name': node.attrs.get('Name') or node.attrs.get('Uid') or '',
                'items_source': binding(node) if node.tag in SELECTORS + ('ItemsControl','ComboBox') else '',
                'template_defined': template_defined,
                'style': is_styled(node, phase),
                'explicit_item_container_style': node.direct(node.tag + '.ItemContainerStyle') or 'ItemContainerStyle' in node.attrs,
                'has_gridview': node.direct('ListView.View') and any(v.tag == 'GridView' for v in node.descendants('GridView')),
                'has_item_template': node.direct(node.tag + '.ItemTemplate'),
                'interactive_cells': sum(1 for v in node.descendants() if v.tag in ('Button', 'CheckBox', 'TextBox', 'ComboBox')),
            }
            controls.append(record)
    # Source scan is only a heuristic for code-created/dynamic views. It cannot
    # prove every dynamically instantiated UI element has been discovered.
    dynamic = []
    for p in sorted(app.rglob('*.cs')):
        if any(x.lower() in ('bin','obj') for x in p.relative_to(app).parts):
            continue
        for n, line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(), 1):
            if DYNAMIC.search(line):
                dynamic.append({'file':p.relative_to(root).as_posix(), 'line':n,
                                'sample':line.strip()[:180]})
    # This guard deliberately relies only on each selectable list's *concrete* XAML
    # type + ItemsSource and its path: a fresh list in another window must not silently
    # inherit the global GridViewRowPresenter style intended for five known views.
    known = [c for c in controls if c['type'] in SELECTORS and not c['template_defined']]
    identities = [(c['file'], c['type'], c['items_source']) for c in known]
    count = collections.Counter(identities)
    missing = sorted(EXPECTED_SELECTOR_BINDINGS - set(identities))
    extra = sorted(set(identities) - EXPECTED_SELECTOR_BINDINGS)
    for item in missing:
        blockers.append(f'Known selector missing/changed: {item}. Review upstream before applying shared row template.')
    for item in extra:
        blockers.append(f'Unreviewed selectable control: {item}. Check its row/template before build.')
    for item in sorted(k for k, v in count.items() if v > 1):
        blockers.append(f'Duplicate selectable identity {item}; cannot ensure which item is styled.')
    templated_selectors = [c for c in controls if c['type'] in SELECTORS and c['template_defined']]
    for c in templated_selectors:
        blockers.append(f'{c["file"]}:{c["line"]} Selectable list inside a template is not in the six reviewed views; assess the instantiated row template.')
    if len(known) != 6:
        blockers.append(f'Expected six reviewed selectable controls across all application XAML, found {len(known)}.')
    for c in known:
        if c['type'] == 'ListView' and not c['has_gridview']:
            blockers.append(f'{c["file"]}:{c["line"]} ListView is not GridView-backed; shared template is incompatible.')
        if c['type'] in ('ListView','ListBox') and c['explicit_item_container_style'] and c['items_source'] != 'Processes':
            blockers.append(f'{c["file"]}:{c["line"]} New explicit row style needs reviewed precedence.')
    # Source-created selectors cannot be safely assumed to be GridView-backed.
    # This is deliberately a narrow literal-constructor guard, not a claim to
    # understand arbitrary reflection or dynamically loaded XAML.
    constructor = re.compile(r'\bnew\s+(?:[\w.]+\.)?(ListView|ListBox|DataGrid|TreeView)\s*[({]')
    for entry in dynamic:
        if constructor.search(entry['sample']):
            blockers.append(f'{entry["file"]}:{entry["line"]} C# creates an unreviewed selectable list; verify its item template before inheriting shared theme.')
    if phase == 'patched':
        theme = app/'Themes/Dark.xaml'
        if not theme.is_file():
            blockers.append('Expected globally merged Themes/Dark.xaml missing.')
        else:
            dark = theme.read_text(encoding='utf-8-sig')
            for token in ('NexusSharedRowSurface', 'NexusSharedListBoxSurface',
                          'GridViewRowPresenter', 'ContentPresenter',
                          '#FF2C374B', '#FF354664', '#FF405878'):
                if token not in dark:
                    blockers.append(f'Patched theme lacks reviewed hover/list content marker: {token}')
            if dark.count('<Style TargetType="ListViewItem">') != 1 or dark.count('<Style TargetType="ListBoxItem">') != 1:
                blockers.append('Shared row style identity/count changed; manual review required.')
        window = app/'MainWindow.xaml'
        if not window.is_file() or 'ProcessRowSurface' not in window.read_text(encoding='utf-8-sig'):
            blockers.append('Working b1r7 Processes row override is missing.')
    for c in controls:
        if c['type'] in ('ItemsControl', 'ComboBox', 'ContextMenu'):
            warnings.append(f'{c["file"]}:{c["line"]} {c["type"]}: review hover/selection and nested controls on live Windows; not auto-patched.')
    if custom:
        warnings.append(f'{len(custom)} custom namespace XAML elements (may include converters/resources): inspect visual controls for custom-drawn hover states as applicable.')
    if dynamic:
        warnings.append(f'{len(dynamic)} C# dynamic-control creation/loader candidates: require manual source/runtime review.')
    return {
        'title':'Nexus application-wide XAML control inventory', 'phase':phase,
        'scope':'Every .xaml and .cs file under checked-out src/Nexus.App (excluding obj/bin)',
        'xaml_files':source_files,
        'counts':dict(sorted(collections.Counter(c['type'] for c in controls).items())),
        'implicit_style_declarations':{k: sorted(v) for k,v in sorted(theme_styles.items())},
        'controls':controls, 'custom_xaml_elements':custom, 'dynamic_candidates':dynamic,
        'blockers':blockers, 'review_notes':warnings,
        'limitations':[
            'STATIC ONLY: source markup and simple code construction patterns are inspected; no WPF visual tree or Win32 runtime UI enumeration.',
            'ItemsControl, ComboBox, ContextMenu and custom panels are cataloged but NOT automatically restyled.',
            'Dynamic XAML, third-party controls, templates instantiated at runtime and Windows theme behavior need interactive Windows acceptance.',
            'Style presence does not prove actual text contrast; manual hover/selection testing remains mandatory.',
        ]
    }


def markdown(data):
    lines = [f'# {data["title"]} — {data["phase"]}', '',
             f'**Scope:** {data["scope"]}', '',
             f'**XAML files parsed:** {len(data["xaml_files"])}',
             f'**Selectable-layout blockers:** {len(data["blockers"])}',
             '**Control counts:** ' + ', '.join(f'{k}={v}' for k, v in data['counts'].items()), '',
             '## Inventory', '',
             '| File:line | Control | ItemsSource | Styling assessment | Interactive cells |',
             '|---|---|---|---|---:|']
    for c in data['controls']:
        parts = (f'{c["file"]}:{c["line"]}', c['type'], c['items_source'] or '—',
                 c['style'], str(c['interactive_cells']))
        lines.append('| ' + ' | '.join(x.replace('|','\\|').replace('\n',' ') for x in parts) + ' |')
    lines += ['', '## Fail-closed blockers', '']
    lines += ['- '+msg for msg in data['blockers']] or ['None for audited source.']
    lines += ['', '## Manual-review candidates (not automatically modified)', '']
    lines += ['- '+msg for msg in data['review_notes']] or ['No additional candidates identified by static rules.']
    lines += ['', '## Dynamic C# candidates', '']
    lines += [f'- {e["file"]}:{e["line"]}: `{e["sample"].replace("`", "")}`' for e in data['dynamic_candidates']] or ['No matches for implemented source patterns.']
    lines += ['', '## Limitations', '']
    lines += ['- '+item for item in data['limitations']]
    return '\n'.join(lines)+'\n'


def run(root:Path, phase:str, out:Path, enforce=True):
    data=collect(root,phase)
    out.mkdir(parents=True,exist_ok=True)
    (out/(phase+'.json')).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/(phase+'.md')).write_text(markdown(data),encoding='utf-8')
    print(f'XAML INVENTORY ({phase}): {len(data["xaml_files"])} XAML files, '
          f'{len(data["controls"])} displayed/list-style declarations, '
          f'{len(data["blockers"])} blockers, {len(data["review_notes"])} review notes')
    for message in data['blockers']:
        print('BLOCKER:',message,file=sys.stderr)
    print('Full findings:',out/(phase+'.md'))
    if enforce and data['blockers']:
        raise RuntimeError('Unreviewed selectable controls or theme regression; see inventory report. '
                           'Do not apply global templates to unknown views.')
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream',type=Path)
    parser.add_argument('--phase',choices=('upstream','patched'),required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('ui-audit'))
    parser.add_argument('--no-enforce',action='store_true',help='Produce report without failing on unreviewed selector (diagnostics only)')
    args=parser.parse_args()
    try:
        run(args.upstream,args.phase,args.output_dir,not args.no_enforce)
    except Exception as exc:
        print('XAML INVENTORY FAILED:',exc,file=sys.stderr)
        sys.exit(1)
