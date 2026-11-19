"""b1r7 regression: scope dark mouse-over to actual Processes ListView rows."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nexus_portable_patch_b1r7', ROOT/'scripts/apply_portable.py')
patch=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

XAML='''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"><Grid>
 <ListView Grid.Row="1" ItemsSource="{Binding Processes}"
           SelectedItem="{Binding Selected}"
           VirtualizingPanel.IsVirtualizing="True">
   <ListView.View><GridView><GridViewColumn Header="Process" DisplayMemberBinding="{Binding ExeName}"/><GridViewColumn Header="PID" DisplayMemberBinding="{Binding Pid}"/></GridView></ListView.View>
   <ListView.ContextMenu>
                        <ContextMenu>
                            <MenuItem Header="Set priority (now)">
                                <MenuItem Header="High" Command="{Binding SetPriorityCommand}"/>
                            </MenuItem>
                        </ContextMenu>
   </ListView.ContextMenu>
 </ListView>
 <ListView Grid.Row="1" ItemsSource="{Binding Entries}"><ListView.View><GridView><GridViewColumn Header="Other"/></GridView></ListView.View></ListView>
 </Grid></Window>'''
CODE='''using System.Windows;
namespace Nexus.App;
public partial class MainWindow : Window
{
    private void Refresh()
    {
    }
}
'''
NS='{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'

def make_fixture(where, xaml=XAML):
    app=where/'src/Nexus.App'; app.mkdir(parents=True)
    (app/'MainWindow.xaml').write_text(xaml,encoding='utf-8')
    (app/'MainWindow.xaml.cs').write_text(CODE,encoding='utf-8')
    return app

class ProcessHoverTests(unittest.TestCase):
    def test_row_template_is_valid_xml_and_has_grid_presenter(self):
        style=(ROOT/'patches/ProcessRowStyle.xaml').read_text(encoding='utf-8')
        ET.fromstring('<ListView xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'+style+'</ListView>')
        self.assertEqual(style.count('<GridViewRowPresenter '),1)
        self.assertIn('Columns="{TemplateBinding GridView.ColumnCollection}"',style)
        self.assertIn('Content="{TemplateBinding Content}"',style)
        self.assertEqual(style.count('<ControlTemplate TargetType="{x:Type ListViewItem}">'),1)

    def test_dark_hover_selected_combined_and_keyboard_focus(self):
        style=(ROOT/'patches/ProcessRowStyle.xaml').read_text(encoding='utf-8')
        for text in ['Property="IsMouseOver" Value="True"','Property="IsSelected" Value="True"',
                     'Property="IsKeyboardFocusWithin" Value="True"', '#FF2C374B','#FF354664','#FF405878',
                     '{StaticResource TextBrush}','<MultiTrigger>']:
            self.assertIn(text,style)
        self.assertLess(style.index('<Trigger Property="IsSelected"'),style.index('<MultiTrigger>'))
        self.assertNotIn('White',style)

    def test_scoped_to_processes_and_commands_survive(self):
        with TemporaryDirectory() as tmp:
            app=make_fixture(Path(tmp))
            patch.patch_process_context_menu(Path(tmp))
            doc=ET.fromstring((app/'MainWindow.xaml').read_text(encoding='utf-8'))
            lists=doc.findall('.//'+NS+'ListView')
            self.assertEqual(len(lists),2)
            processes=[lv for lv in lists if lv.attrib.get('ItemsSource')=='{Binding Processes}'][0]
            entries=[lv for lv in lists if lv.attrib.get('ItemsSource')=='{Binding Entries}'][0]
            self.assertIsNotNone(processes.find(NS+'ListView.ItemContainerStyle'))
            self.assertIsNone(entries.find(NS+'ListView.ItemContainerStyle'))
            self.assertEqual(len(processes.findall('.//'+NS+'GridViewRowPresenter')),1)
            self.assertEqual(len(processes.findall('.//'+NS+'GridViewColumn')),2)
            self.assertEqual(len(processes.findall('.//'+NS+'ContextMenu.Template')),1)
            self.assertIn('SelectedItem',processes.attrib)
            self.assertIn('VirtualizingPanel.IsVirtualizing',processes.attrib)
            self.assertIn('PreviewMouseRightButtonDown',processes.attrib)
            self.assertEqual(len(processes.findall('.//'+NS+'MenuItem[@Command="{Binding SetPriorityCommand}"]')),1)

    def test_unknown_source_process_list_fails_closed(self):
        with TemporaryDirectory() as tmp:
            app=make_fixture(Path(tmp),XAML.replace('ItemsSource="{Binding Processes}"','ItemsSource="{Binding OtherProcesses}"'))
            with self.assertRaises(AssertionError):
                patch.patch_process_context_menu(Path(tmp))
            self.assertNotIn('ProcessRowSurface',(app/'MainWindow.xaml').read_text())

    def test_preexisting_row_style_fails_closed(self):
        with TemporaryDirectory() as tmp:
            xaml=XAML.replace('<ListView.View><GridView>','<ListView.ItemContainerStyle><Style TargetType="{x:Type ListViewItem}"/></ListView.ItemContainerStyle><ListView.View><GridView>',1)
            app=make_fixture(Path(tmp),xaml)
            with self.assertRaisesRegex(RuntimeError, 'already has customized'):
                patch.patch_process_context_menu(Path(tmp))
            # This error may have been detected after menu injection, but the
            # existing row style is not overwritten and source patch aborts.
            self.assertEqual((app/'MainWindow.xaml').read_text().count('<ListView.ItemContainerStyle>'),1)

if __name__=='__main__': unittest.main()
