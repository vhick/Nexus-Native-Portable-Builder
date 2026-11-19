import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class WindowsIssueRegressionTests(unittest.TestCase):
    def test_first_run_task_is_normal_not_error(self):
        s=(ROOT/'patches/AutostartService.cs').read_text()
        self.assertIn('folder.GetTasks(1)',s)
        self.assertIn('return null; // no matching task',s)
        self.assertNotIn('folder.GetTask(TaskName)',s)
    def test_autostart_ownership_is_still_checked(self):
        s=(ROOT/'patches/AutostartService.cs').read_text()
        self.assertIn('Owned(existing)',s)
        self.assertIn('"__FOREIGN__"',s)
        self.assertIn('string.Equals(target, recorded',s)
        self.assertIn('if (!Owned(existing))',s)
    def test_dark_process_menu_xaml_is_valid_xml(self):
        opening='<ContextMenu xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'
        xml=opening+(ROOT/'patches/ProcessMenuStyle.xaml').read_text()+'<MenuItem Header="Test"><MenuItem Header="Leaf"/></MenuItem></ContextMenu>'
        ET.fromstring(xml)
        self.assertIn('PART_Popup',xml)
        self.assertIn('IsSubmenuOpen',xml)
        self.assertIn('PanelAltBrush',xml)
    def test_patch_source_has_explicit_row_selection(self):
        s=(ROOT/'scripts/apply_portable.py').read_text()
        self.assertIn('SelectProcessOnRightClick',s)
        self.assertIn('ItemsControl.ContainerFromElement(list, element)',s)
        self.assertIn('text.count(context)==1',s)
if __name__=='__main__': unittest.main()
