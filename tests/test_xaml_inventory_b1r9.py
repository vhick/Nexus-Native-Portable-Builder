"""b1r9: exhaustive-in-scope, source-safe WPF control inventory regression tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    spec = importlib.util.spec_from_file_location(name,ROOT/file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

audit = load('nexus_ui_inventory_b1r9', 'scripts/audit_xaml_controls.py')
fixtures = load('nexus_list_fixtures_b1r8', 'tests/test_shared_list_hover_b1r8.py')
patch = load('nexus_ui_patch_b1r9', 'scripts/apply_portable.py')


class FullApplicationXamlAuditTests(unittest.TestCase):
    def make(self, root):
        return fixtures.fixture(root)

    def test_unpatched_known_six_are_detected_and_reported(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            data=audit.collect(root,'upstream')
            self.assertEqual(len(data['blockers']),0)
            self.assertEqual(data['counts']['ListView'],5)
            self.assertEqual(data['counts']['ListBox'],1)
            self.assertEqual(len(data['xaml_files']),2)
            self.assertTrue(any(x['items_source']=='Processes' and x['explicit_item_container_style']
                                for x in data['controls']))

    def test_patched_full_theme_is_checked_without_modifying_source(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            patch.patch_shared_dark_list_rows(root)
            patch.patch_dark_grid_headers(root)
            before={p:p.read_bytes() for p in root.rglob('*.xaml')}
            report=audit.run(root,'patched',root/'ui-audit')
            self.assertFalse(report['blockers'])
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*.xaml')})
            self.assertTrue((root/'ui-audit/patched.md').is_file())
            self.assertEqual(json.loads((root/'ui-audit/patched.json').read_text())['phase'],'patched')

    def test_unreviewed_list_in_additional_window_fails_closed(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            path=root/'src/Nexus.App/SettingsWindow.xaml'
            path.write_text('<Window xmlns="'+audit.P+'"><ListView ItemsSource="{Binding UnknownItems}"/></Window>',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertTrue(any('UnknownItems' in x for x in data['blockers']))
            with self.assertRaisesRegex(RuntimeError,'Unreviewed selectable'):
                audit.run(root,'upstream',root/'reports')
            self.assertTrue((root/'reports/upstream.md').exists())

    def test_datagrid_and_treeview_require_specific_review(self):
        for control in ('DataGrid','TreeView'):
            with self.subTest(control=control), TemporaryDirectory() as d:
                root=Path(d); self.make(root)
                (root/'src/Nexus.App/Other.xaml').write_text(
                    f'<UserControl xmlns="{audit.P}"><{control} ItemsSource="{{Binding Nodes}}"/></UserControl>',encoding='utf-8')
                self.assertTrue(any(control in x for x in audit.collect(root,'upstream')['blockers']))

    def test_custom_control_and_nonselectable_itemscontrol_are_reported_not_retemplated(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            (root/'src/Nexus.App/SettingsWindow.xaml').write_text('''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
              xmlns:app="clr-namespace:Nexus.App.Controls">
              <StackPanel><ItemsControl ItemsSource="{Binding SecurityWarnings}"><ItemsControl.ItemTemplate><DataTemplate><TextBlock Text="{Binding Message}"/></DataTemplate></ItemsControl.ItemTemplate></ItemsControl>
              <ComboBox ItemsSource="{Binding Choices}"/><app:CustomTile/></StackPanel></Window>''',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertFalse(data['blockers'])
            self.assertTrue(data['custom_xaml_elements'])
            self.assertEqual(data['counts']['ItemsControl'],1)
            self.assertEqual(data['counts']['ComboBox'],1)
            self.assertTrue(any('ComboBox' in n for n in data['review_notes']))

    def test_non_gridview_is_incompatible_with_shared_global_row_template(self):
        with TemporaryDirectory() as d:
            root=Path(d); window,_=self.make(root)
            window.write_text(window.read_text().replace(
               '<ListView.View><GridView><GridViewColumn Header="Message"/></GridView></ListView.View>',
               '<ListView.ItemTemplate><DataTemplate><TextBlock/></DataTemplate></ListView.ItemTemplate>'),encoding='utf-8')
            self.assertTrue(any('not GridView-backed' in b for b in audit.collect(root,'upstream')['blockers']))

    def test_known_binding_drift_is_caught(self):
        with TemporaryDirectory() as d:
            root=Path(d); window,_=self.make(root)
            window.write_text(window.read_text().replace('{Binding Games}','{Binding NewGames}'),encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertGreaterEqual(len(data['blockers']),2)
            self.assertTrue(any('Known selector missing' in b for b in data['blockers']))

    def test_duplicate_known_list_identity_blocked(self):
        with TemporaryDirectory() as d:
            root=Path(d); window,_=self.make(root)
            markup=window.read_text().replace('</Grid></Window>',
                    '<ListBox ItemsSource="{Binding Restrained}"/></Grid></Window>')
            window.write_text(markup,encoding='utf-8')
            self.assertTrue(any('Duplicate' in b for b in audit.collect(root,'upstream')['blockers']))

    def test_malformed_xml_rejected_with_real_line(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            (root/'src/Nexus.App/Broken.xaml').write_text('<Window>\n<ListView>\n</Window>',encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'Malformed XAML'):
                audit.collect(root,'upstream')

    def test_code_created_lists_and_xaml_loader_flagged_for_review(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            (root/'src/Nexus.App/NewPanel.cs').write_text('''using System.Windows.Controls;
class X { void F(){ var v = new ListView(); var w = XamlReader.Parse("x"); } }''',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertEqual(len(data['dynamic_candidates']),1)
            self.assertTrue(any('C# creates an unreviewed' in b for b in data['blockers']))
            self.assertTrue(any('dynamic-control' in x for x in data['review_notes']))

    def test_reports_do_not_fake_runtime_validation(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            md=audit.markdown(audit.collect(root,'upstream'))
            self.assertIn('STATIC ONLY',md)
            self.assertIn('manual',md.lower())
            self.assertIn('src/Nexus.App/MainWindow.xaml',md)

    def test_patched_theme_drift_fails_even_if_controls_unchanged(self):
        with TemporaryDirectory() as d:
            root=Path(d); _,theme=self.make(root)
            patch.patch_shared_dark_list_rows(root)
            patch.patch_dark_grid_headers(root)
            theme.write_text(theme.read_text().replace('#FF2C374B','#FFFFFFFF'),encoding='utf-8')
            self.assertTrue(any('hover/list content marker' in b for b in audit.collect(root,'patched')['blockers']))

    def test_selectable_list_instantiated_from_data_template_is_not_skipped(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            (root/'src/Nexus.App/Templates.xaml').write_text('''<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation">
            <DataTemplate x:Key="Grid" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
              <ListBox ItemsSource="{Binding DynamicRows}"/>
            </DataTemplate></ResourceDictionary>''',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertTrue(any('inside a template' in b for b in data['blockers']))

    def test_source_report_does_not_include_generated_obj_folder(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            obj=root/'src/Nexus.App/obj';obj.mkdir(parents=True)
            (obj/'Generated.xaml').write_text('<View xmlns="'+audit.P+'"><DataGrid/></View>',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertFalse(data['blockers'])
            self.assertFalse(any('obj' in f for f in data['xaml_files']))

    def test_workflow_integrates_both_audits_and_packages_the_reports(self):
        yml=(ROOT/'.github/workflows/build-native.yml').read_text()
        pkg=(ROOT/'scripts/package_native.py').read_text()
        self.assertIn('--phase upstream --output-dir ui-audit',yml)
        self.assertIn('--phase patched --output-dir ui-audit',yml)
        self.assertIn('--ui-audit-dir ui-audit',yml)
        self.assertIn('if: always()',yml)
        self.assertIn('default: r10',yml)
        self.assertIn("for phase in ('upstream', 'patched'):",pkg)
        self.assertIn("'ui_source_inventory_sha256': audit_hashes",pkg)
        self.assertNotIn('AppNamePortable.exe',yml)

    def test_scans_nested_xaml_under_the_app_directory(self):
        with TemporaryDirectory() as d:
            root=Path(d); self.make(root)
            path=root/'src/Nexus.App/Views/Sub/Panel.xaml'
            path.parent.mkdir(parents=True)
            path.write_text('<UserControl xmlns="'+audit.P+'"><ItemsControl ItemsSource="{Binding Extra}"/></UserControl>',encoding='utf-8')
            data=audit.collect(root,'upstream')
            self.assertEqual(len(data['xaml_files']),3)
            self.assertTrue(any(c['file'].endswith('Views/Sub/Panel.xaml') for c in data['controls']))


if __name__=='__main__': unittest.main()
