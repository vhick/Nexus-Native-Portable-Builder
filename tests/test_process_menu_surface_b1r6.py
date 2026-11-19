"""Regression tests for b1r6 default ContextMenu gutter removal."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nexus_patch',ROOT/'scripts/apply_portable.py')
patcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

UPSTREAM_XAML='''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
<Grid><ListView Grid.Row="1" ItemsSource="{Binding Processes}">
<ListView.ContextMenu>
                        <ContextMenu>
                            <MenuItem Header="Set priority (now)"><MenuItem Header="High" Command="{Binding SetPriorityCommand}"/></MenuItem>
                        </ContextMenu>
</ListView.ContextMenu>
</ListView></Grid></Window>'''
UPSTREAM_CS='''using System.ComponentModel;
using System.Windows;
namespace Nexus.App;
public partial class MainWindow : Window
{
    private void Refresh()
    {
    }
}'''

class MenuSurfaceTests(unittest.TestCase):
    def test_menu_surface_is_xml_and_instance_scoped(self):
        template=(ROOT/'patches/ProcessMenuSurface.xaml').read_text(encoding='utf-8')
        fixture='<ContextMenu xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'+template+'<MenuItem Header="A"/></ContextMenu>'
        ET.fromstring(fixture)
        self.assertEqual(template.count('<ContextMenu.Template>'),1)
        self.assertEqual(template.count('<ItemsPresenter '),1)
        self.assertIn('TemplateBinding Background',template)
        self.assertNotIn('IconPresenter',template)
        self.assertNotIn('Grid.Column="2"',template)

    def test_upstream_fixture_preserves_commands_and_has_no_default_popup_template(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            folder=root/'src/Nexus.App';folder.mkdir(parents=True)
            (folder/'MainWindow.xaml').write_text(UPSTREAM_XAML,encoding='utf-8')
            (folder/'MainWindow.xaml.cs').write_text(UPSTREAM_CS,encoding='utf-8')
            patcher.patch_process_context_menu(root)
            output=(folder/'MainWindow.xaml').read_text(encoding='utf-8')
            ET.fromstring(output)
            self.assertEqual(output.count('<ContextMenu.Template>'),1)
            self.assertIn('<ControlTemplate TargetType="{x:Type ContextMenu}">',output)
            self.assertIn('<ItemsPresenter KeyboardNavigation.DirectionalNavigation="Cycle"/>',output)
            self.assertIn('Command="{Binding SetPriorityCommand}"',output)
            self.assertIn('DataContext="{Binding PlacementTarget.DataContext',output)
            self.assertIn('PreviewMouseRightButtonDown="SelectProcessOnRightClick"',output)
            self.assertIn('PART_Popup',output)
            self.assertNotIn('<ContextMenu.Resources>\n                        <ContextMenu.Template>',output)

    def test_no_autostart_modification(self):
        code=(ROOT/'patches/AutostartService.cs').read_text(encoding='utf-8')
        self.assertIn('folder.GetTasks(1)',code)
        self.assertIn('Owned(existing)',code)
        self.assertNotIn('folder.GetTask(TaskName)',code)

if __name__=='__main__': unittest.main()
