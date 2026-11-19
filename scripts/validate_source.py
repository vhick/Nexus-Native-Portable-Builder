#!/usr/bin/env python3
"""Fail-closed checks on the exact Nexus portable source adaptation."""
from pathlib import Path
import argparse,sys,re,json

def validate_native_identity_source(identity_source):
    """Validate WPF helper imports before the costly Windows app compilation."""
    assert re.search(r'^using\s+System\.IO\s*;', identity_source, re.MULTILINE), (
        'NativePortableIdentity.cs uses Path but is missing explicit using System.IO;'
    )
    assert 'Path.GetFullPath(AppContext.BaseDirectory)' in identity_source, (
        'Portable instance ID must derive from running executable location'
    )

def check(root):
    p=root/'src/Nexus.Core/Persistence/NexusPaths.cs'
    t=p.read_text(encoding='utf-8')
    assert 'Path.Combine(AppContext.BaseDirectory, "Data")' in t, 'Native data root is not executable-relative'
    assert 'Environment.SpecialFolder.ApplicationData), "Nexus"' not in t, 'Host user profile data root still exists'
    assert 'public string QuarantineDirectory' in t and 'public string RegistryBackupDirectory' in t, 'Upstream storage contract changed'
    s=(root/'src/Nexus.Core/Models/AppSettings.cs').read_text(encoding='utf-8')
    assert 'public bool RansomwareWatch { get; set; } = false;' in s, 'Unconsented canary writes enabled'
    a=(root/'src/Nexus.App/Services/AutostartService.cs').read_text(encoding='utf-8')
    assert 'private static readonly string StateDirectory = Path.Combine(AppContext.BaseDirectory, "Data", "Integrations")' in a
    assert 'Nexus Native Portable-' in a and 'Owned(existing)' in a
    # b1r5: do not regress to throwing GetTask(name) on first run.
    assert 'folder.GetTasks(1)' in a and 'return null; // no matching task' in a, 'Autostart missing-task handling regressed'
    assert 'folder.GetTask(TaskName)' not in a, 'Throwing COM task lookup reintroduced'
    assert 'Owned(existing)' in a and '"__FOREIGN__"' in a, 'Task ownership check removed'
    theme=(root/'src/Nexus.App/MainWindow.xaml').read_text(encoding='utf-8')
    assert 'PlacementTarget.DataContext' in theme and 'PART_Popup' in theme, 'Process menu binding or style missing'
    # b1r6: the default Windows ContextMenu template retains a light icon gutter.
    # Require an instance-scoped replacement with an ItemsPresenter and preserve
    # native item UI behavior in the separate MenuItem style.
    assert theme.count('<ContextMenu.Template>') == 1, 'Process ContextMenu must have a custom popup template'
    assert '<ControlTemplate TargetType="{x:Type ContextMenu}">' in theme, 'Process popup theme template missing'
    assert '<ItemsPresenter KeyboardNavigation.DirectionalNavigation="Cycle"/>' in theme, 'Popup must host menu items'
    assert 'PreviewMouseRightButtonDown="SelectProcessOnRightClick"' in theme, 'Right-click selection handler missing'
    # b1r7: scope the hover fix to the Processes ListView. WPF's default row
    # template would otherwise paint a nearly white system hover background.
    assert theme.count('<ListView.ItemContainerStyle>') == 1, 'Process-only row template missing or duplicated'
    assert '<GridViewRowPresenter Content="{TemplateBinding Content}"' in theme, 'GridView column presenter lost'
    assert 'Property="IsMouseOver" Value="True"' in theme, 'Dark process hover trigger missing'
    assert 'Property="IsSelected" Value="True"' in theme and '<MultiTrigger>' in theme, 'Selected-row states lost'
    assert '#FF2C374B' in theme and '#FF405878' in theme, 'Dark process hover colors missing'
    assert 'Columns="{TemplateBinding GridView.ColumnCollection}"' in theme, 'Process grid columns lost'
    codebehind=(root/'src/Nexus.App/MainWindow.xaml.cs').read_text(encoding='utf-8')
    assert 'ItemsControl.ContainerFromElement(list, element)' in codebehind, 'Right-click row selection missing'
    # XML parsing catches broken XAML tag nesting before the WPF compiler runs.
    import xml.etree.ElementTree as ET
    ET.fromstring(theme)
    h=(root/'src/Nexus.App/Services/Security/ShellIntegrationService.cs').read_text(encoding='utf-8')
    assert 'Nexus.NativePortable.ScanWithNexus' in h
    assert 'never overwrite any existing registration' in h
    assert 'StringComparison.OrdinalIgnoreCase' in h
    w=(root/'src/Nexus.App/App.xaml.cs').read_text(encoding='utf-8')
    assert 'var paths = NexusPaths.Default();' in w, 'Upstream application composition changed'
    assert 'Global\\Nexus.NativePortable.{NativePortableIdentity.Suffix}' in w, 'Native instance mutex not unique'
    pipe=(root/'src/Nexus.App/Services/ScanRequestChannel.cs').read_text(encoding='utf-8')
    assert 'Nexus.NativePortable.ScanRequest.' in pipe, 'Scan IPC collides with installed Nexus'
    identity = root/'src/Nexus.App/Services/NativePortableIdentity.cs'
    assert identity.is_file(), 'Missing in-process identity source'
    identity_source = identity.read_text(encoding='utf-8-sig')
    # WPF's temporary compile project does not necessarily inherit implicit
    # global usings. In b1r3, an unqualified Path triggered three CS0103
    # errors during the win-x64 app publish despite passing Core tests.
    validate_native_identity_source(identity_source)
    assert 'new ScannerPool(' in w, 'Scanner integration changed'
    csproj=(root/'src/Nexus.App/Nexus.App.csproj').read_text(encoding='utf-8')
    assert '<AssemblyName>Nexus</AssemblyName>' in csproj
    assert 'Nexus.Scanner.exe' in csproj
    adapted=(root/'tests/Nexus.Core.Tests/SettingsUpgradeTests.cs').read_text(encoding='utf-8')
    assert 'Assert.False(settings.Security.RansomwareWatch); // Native portable: opt-in default' in adapted, 'Default-off migration assertion missing'
    assert 'Native_portable_explicit_ransomware_watch_opt_in_is_preserved' in adapted, 'Explicit opt-in preservation test missing'
    # Report possible extra direct absolute path calls; these are not automatically failures:
    # many are intentional read-only system inspection or explicitly consented system actions.
    hits=[]
    for f in sorted((root/'src').rglob('*.cs')):
        rel=f.relative_to(root).as_posix()
        for n,line in enumerate(f.read_text(encoding='utf-8-sig').splitlines(),1):
            if any(w in line for w in ('Environment.SpecialFolder.', 'Registry.CurrentUser.CreateSubKey',
                    'Registry.LocalMachine.CreateSubKey', 'File.WriteAllText(', 'File.Create(',
                    'Directory.CreateDirectory(', 'schtasks', 'File.Move(', 'File.Delete(')):
                hits.append({'file':rel,'line':n,'content':line.strip()[:200]})
    (root/'source-write-audit.json').write_text(json.dumps(hits,indent=2),encoding='utf-8')
    print(f'SOURCE STATIC CHECK PASSED; {len(hits)} source write/path candidates inventoried (not proven runtime-contained)')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('upstream');args=ap.parse_args()
    try:check(Path(args.upstream))
    except Exception as e:print('SOURCE CHECK FAILED:',str(e),file=sys.stderr);sys.exit(1)
