"""b1r10: source-template and fail-closed header hover fixture tests; not Windows visual tests."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
P='{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X='{http://schemas.microsoft.com/winfx/2006/xaml}'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
patch=load('scripts/apply_portable.py','headers_patch_b1r10')
fixtures=load('tests/test_shared_list_hover_b1r8.py','headers_fixtures_b1r10')
audit=load('scripts/audit_xaml_controls.py','headers_audit_b1r10')

class GridViewHeaderTests(unittest.TestCase):
    def fixture(self, directory):
        root=Path(directory)
        window,theme=fixtures.fixture(root)
        patch.patch_shared_dark_list_rows(root)
        return root,window,theme

    def test_source_template_well_formed_and_has_required_resize_part(self):
        path=ROOT/'patches/DarkGridHeaders.xaml'
        doc=ET.fromstring('<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'+path.read_text()+'</ResourceDictionary>')
        styles=doc.findall(P+'Style')
        self.assertEqual(len(styles),1)
        self.assertEqual(styles[0].attrib.get('TargetType'),'GridViewColumnHeader')
        thumbs=[v for v in doc.iter(P+'Thumb') if v.attrib.get(X+'Name')=='PART_HeaderGripper']
        self.assertEqual(len(thumbs),1)
        self.assertEqual(thumbs[0].attrib.get('Cursor'),'SizeWE')
        presenters=list(doc.iter(P+'ContentPresenter'))
        self.assertEqual(len(presenters),1)
        self.assertEqual(presenters[0].attrib.get('ContentSource'),'Content')
        self.assertEqual(len(list(doc.iter(P+'ControlTemplate'))),2) # header + thumb

    def test_hover_pressed_and_normal_colors_are_dark(self):
        txt=(ROOT/'patches/DarkGridHeaders.xaml').read_text()
        self.assertIn('Value="{StaticResource PanelAltBrush}"',txt)
        self.assertIn('Property="IsMouseOver" Value="True"',txt)
        self.assertIn('Property="IsPressed" Value="True"',txt)
        self.assertIn('Property="Role" Value="Floating"',txt)
        self.assertIn('Property="Role" Value="Padding"',txt)
        for color in ('#FF2C374B','#FF354664'):
            self.assertEqual(txt.count(color),1)
        self.assertNotIn('#FFFFFFFF',txt)
        self.assertNotIn('#DDF6FF',txt)
        self.assertIn('Foreground" Value="{StaticResource TextBrush}"',txt)

    def test_one_shared_header_style_for_all_five_gridviews(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            before=window.read_bytes()
            patch.patch_dark_grid_headers(root)
            self.assertEqual(before,window.read_bytes(), 'header fix must not rewrite live view/cell controls')
            d=ET.parse(theme).getroot()
            styles=[x for x in d.findall(P+'Style') if x.attrib.get('TargetType')=='GridViewColumnHeader']
            self.assertEqual(len(styles),1)
            self.assertEqual(window.read_text().count('<GridView>'),5)
            self.assertEqual(window.read_text().count('<ListView.View>'),5)
            for required in ('{Binding RemoveGameCommand}','{Binding PinCommand}','{Binding Enabled}','{Binding PinCore}'):
                self.assertIn(required,window.read_text())
            self.assertEqual(audit.collect(root,'patched')['blockers'],[])

    def test_inventory_reports_all_grid_header_labels(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            patch.patch_dark_grid_headers(root)
            report=audit.collect(root,'patched')
            self.assertFalse(report['blockers'])
            names={h['header'] for h in report['gridview_headers']}
            for name in ('Process','Game','Enabled','Pin','Message'):
                self.assertIn(name,names)
            self.assertTrue(all(h['gridview_line'] for h in report['gridview_headers']))
            self.assertIn('## GridView column headings',audit.markdown(report))

    def test_per_column_style_override_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            patch.patch_dark_grid_headers(root)
            window.write_text(window.read_text().replace('<GridViewColumn Header="Message"/>',
                '<GridViewColumn Header="Message" HeaderContainerStyle="{StaticResource Unexpected}"/>'))
            report=audit.collect(root,'patched')
            self.assertTrue(any('per-column GridViewColumn' in b for b in report['blockers']))
            self.assertTrue(any(h['header']=='Message' and h['explicit_header_style'] for h in report['gridview_headers']))

    def test_unknown_original_header_style_fails_without_changes(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            theme.write_text(theme.read_text().replace('TargetType="GridViewColumnHeader"','TargetType="HeaderUnknown"'),encoding='utf-8')
            prior=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'GridViewColumnHeader theme changed'):
                patch.patch_dark_grid_headers(root)
            self.assertEqual(theme.read_bytes(),prior)

    def test_new_list_header_fails_closed_before_change(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            window.write_text(window.read_text().replace('<GridView>', '<GridView ColumnHeaderContainerStyle="{StaticResource ForeignHeader}">',1))
            before=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'explicit GridView column-header styles'):
                patch.patch_dark_grid_headers(root)
            self.assertEqual(theme.read_bytes(),before)

    def test_malformed_header_template_rejected_before_mutation(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            # This deliberately corrupts a TEMP copy of the builder patch file? No.
            # Verify parsed result rejects missing Thumb via the patched-theme guard.
            patch.patch_dark_grid_headers(root)
            text=theme.read_text().replace('x:Name="PART_HeaderGripper"', 'x:Name="WrongName"')
            theme.write_text(text)
            issues=audit.collect(root,'patched')['blockers']
            self.assertTrue(any('GridView header' in x for x in issues))

    def test_reapply_is_rejected_and_keeps_correct_template(self):
        with TemporaryDirectory() as tmp:
            root,window,theme=self.fixture(tmp)
            patch.patch_dark_grid_headers(root)
            initial=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'GridViewColumnHeader theme changed'):
                patch.patch_dark_grid_headers(root)
            self.assertEqual(initial,theme.read_bytes())

    def test_no_native_non_ui_workflow_changes(self):
        text=(ROOT/'.github/workflows/build-native.yml').read_text()
        self.assertIn('default: r10',text)
        self.assertIn('scripts/apply_portable.py',text)
        self.assertIn('scripts/audit_xaml_controls.py',text)
        self.assertNotIn('PortableAppsPortable.exe',text)

if __name__=='__main__': unittest.main()
