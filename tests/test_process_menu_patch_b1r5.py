"""Integration fixture: apply audited XAML/code-behind patch to source-shaped files."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nexus_portable_patch', ROOT/'scripts/apply_portable.py')
patcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

XAML='''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
 <Grid>
 <ListView Grid.Row="1" ItemsSource="{Binding Processes}">
   <ListView.ContextMenu>
                        <ContextMenu>
                            <MenuItem Header="Set priority (now)">
                                <MenuItem Header="High" Command="{Binding SetPriorityCommand}"/>
                            </MenuItem>
                        </ContextMenu>
   </ListView.ContextMenu>
 </ListView>
 </Grid>
</Window>
'''
CS='''using System.ComponentModel;
using System.Windows;
using System.Windows.Media.Animation;
namespace Nexus.App;
public partial class MainWindow : Window
{
    private void Refresh()
    {
    }
}
'''

class ProcessMenuPatchTests(unittest.TestCase):
    def test_apply_ui_patch_is_well_formed_and_preserves_command(self):
        with TemporaryDirectory() as d:
            base=Path(d)
            app=base/'src/Nexus.App'
            app.mkdir(parents=True)
            (app/'MainWindow.xaml').write_text(XAML)
            (app/'MainWindow.xaml.cs').write_text(CS)
            patcher.patch_process_context_menu(base)
            doc=(app/'MainWindow.xaml').read_text()
            code=(app/'MainWindow.xaml.cs').read_text()
            ET.fromstring(doc)
            self.assertIn('Command="{Binding SetPriorityCommand}"',doc)
            self.assertIn('PlacementTarget.DataContext',doc)
            self.assertIn('PreviewMouseRightButtonDown="SelectProcessOnRightClick"',doc)
            self.assertIn('PART_Popup',doc)
            self.assertIn('using System.Windows.Input;',code)
            self.assertIn('ItemsControl.ContainerFromElement(list, element)',code)

    def test_fails_closed_when_upstream_menu_changes(self):
        with TemporaryDirectory() as d:
            base=Path(d)
            app=base/'src/Nexus.App'
            app.mkdir(parents=True)
            (app/'MainWindow.xaml').write_text(XAML.replace('Header="Set priority (now)"','Header="Different menu"'))
            (app/'MainWindow.xaml.cs').write_text(CS)
            with self.assertRaisesRegex(AssertionError,'Process ContextMenu changed upstream'):
                patcher.patch_process_context_menu(base)

if __name__=='__main__': unittest.main()
