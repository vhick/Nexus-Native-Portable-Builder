"""b1r8: verify shared WPF hover fix without touching app commands."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import xml.etree.ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nexus_patch_all_list_rows_b1r8', ROOT/'scripts/apply_portable.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

NS='{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
DARK_ORIGINAL = '''<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
<Style TargetType="Button"><Setter Property="Foreground" Value="{StaticResource TextBrush}"/></Style>
    <Style TargetType="ListViewItem">
        <Setter Property="Foreground" Value="{StaticResource TextBrush}"/>
        <Setter Property="Background" Value="Transparent"/>
        <Style.Triggers>
            <Trigger Property="IsSelected" Value="True">
                <Setter Property="Background" Value="#FF2A3550"/>
            </Trigger>
        </Style.Triggers>
    </Style>
<Style TargetType="GridViewColumnHeader"><Setter Property="Foreground" Value="{StaticResource TextDimBrush}"/></Style>
</ResourceDictionary>'''

# Minimal source-accurate control shape: preserves the interactive game, startup
# and IRQ GridView cells and the existing b1r7 Processes local style.
WINDOW = '''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"><Grid>
<ListView Grid.Row="1" ItemsSource="{Binding Processes}">
  <ListView.ItemContainerStyle><Style TargetType="{x:Type ListViewItem}"><Setter Property="Template"><Setter.Value><ControlTemplate TargetType="{x:Type ListViewItem}"><Border x:Name="ProcessRowSurface"/></ControlTemplate></Setter.Value></Setter></Style></ListView.ItemContainerStyle>
  <ListView.View><GridView><GridViewColumn Header="Process"/></GridView></ListView.View>
</ListView>
<ListView Grid.Row="2" ItemsSource="{Binding Games}"><ListView.View><GridView><GridViewColumn Header="Game"/><GridViewColumn Header="Enabled"><GridViewColumn.CellTemplate><DataTemplate><CheckBox IsChecked="{Binding Enabled}"/></DataTemplate></GridViewColumn.CellTemplate></GridViewColumn><GridViewColumn Header="Remove"><GridViewColumn.CellTemplate><DataTemplate><Button Command="{Binding RemoveGameCommand}"/></DataTemplate></GridViewColumn.CellTemplate></GridViewColumn></GridView></ListView.View></ListView>
<ListView ItemsSource="{Binding StartupEntries}"><ListView.View><GridView><GridViewColumn Header="Enabled"><GridViewColumn.CellTemplate><DataTemplate><CheckBox IsChecked="{Binding Enabled}"/></DataTemplate></GridViewColumn.CellTemplate></GridViewColumn></GridView></ListView.View></ListView>
<ListView ItemsSource="{Binding Devices}"><ListView.View><GridView><GridViewColumn Header="Pin"><GridViewColumn.CellTemplate><DataTemplate><StackPanel><TextBox Text="{Binding PinCore}"/><Button Command="{Binding PinCommand}"/></StackPanel></DataTemplate></GridViewColumn.CellTemplate></GridViewColumn></GridView></ListView.View></ListView>
<ListView Grid.Row="1" ItemsSource="{Binding Entries}"><ListView.View><GridView><GridViewColumn Header="Message"/></GridView></ListView.View></ListView>
<ListBox ItemsSource="{Binding Restrained}"><ListBox.ItemTemplate><DataTemplate><TextBlock Text="{Binding ExeName}"/></DataTemplate></ListBox.ItemTemplate></ListBox>
</Grid></Window>'''


def fixture(root, xaml=WINDOW, dark=DARK_ORIGINAL):
    theme=root/'src/Nexus.App/Themes/Dark.xaml'
    theme.parent.mkdir(parents=True,exist_ok=True)
    theme.write_text(dark,encoding='utf-8')
    window=root/'src/Nexus.App/MainWindow.xaml'
    window.parent.mkdir(parents=True,exist_ok=True)
    window.write_text(xaml,encoding='utf-8')
    return window,theme

class DarkSharedRowStyleTests(unittest.TestCase):
    def test_new_styles_well_formed_and_keep_respective_presenters(self):
        text=(ROOT/'patches/DarkListRows.xaml').read_text(encoding='utf-8')
        doc=ET.fromstring('<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'+text+'</ResourceDictionary>')
        self.assertEqual(len(doc.findall(NS+'Style')),2)
        self.assertEqual(len(doc.findall('.//'+NS+'GridViewRowPresenter')),1)
        self.assertEqual(len(doc.findall('.//'+NS+'ContentPresenter')),1)
        self.assertIn('Columns="{TemplateBinding GridView.ColumnCollection}"',text)
        self.assertIn('ContentTemplate="{TemplateBinding ContentTemplate}"',text)
        self.assertIn('Property="IsKeyboardFocusWithin" Value="True"',text)
        self.assertIn('Property="IsEnabled" Value="False"',text)
        self.assertNotIn('Property="Visibility"',text)

    def test_global_hover_and_selected_are_dark_and_distinct(self):
        text=(ROOT/'patches/DarkListRows.xaml').read_text(encoding='utf-8')
        for color in ['#FF2C374B','#FF354664','#FF405878']:
            self.assertEqual(text.count(color),2)
        self.assertEqual(text.count('<MultiTrigger>'),2)
        self.assertEqual(text.count('Property="IsMouseOver" Value="True"'),4)
        self.assertEqual(text.count('Property="IsSelected" Value="True"'),4)

    def test_source_replace_preserves_all_interactive_cell_bindings_and_process_style(self):
        with TemporaryDirectory() as tmp:
            window,theme=fixture(Path(tmp))
            before=window.read_bytes()
            patch.patch_shared_dark_list_rows(Path(tmp))
            self.assertEqual(window.read_bytes(),before)
            built=theme.read_text(encoding='utf-8')
            self.assertNotIn('#FF2A3550',built)
            self.assertIn('NexusSharedRowSurface',built)
            self.assertIn('NexusSharedListBoxSurface',built)
            doc=ET.fromstring(built)
            self.assertEqual(len(doc.findall(NS+'Style')),4)
            self.assertIn('ProcessRowSurface',window.read_text())
            for marker in ['{Binding RemoveGameCommand}','{Binding PinCommand}','{Binding Enabled}',
                           '{Binding PinCore}','<ListBox.ItemTemplate>']:
                self.assertIn(marker,window.read_text())

    def test_unknown_listview_fails_without_modifying_theme(self):
        with TemporaryDirectory() as tmp:
            window,theme=fixture(Path(tmp),WINDOW.replace('{Binding Devices}','{Binding UnexpectedDevices}'))
            before=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'Audited ListView set changed'):
                patch.patch_shared_dark_list_rows(Path(tmp))
            self.assertEqual(before,theme.read_bytes())

    def test_non_grid_list_fails_closed(self):
        with TemporaryDirectory() as tmp:
            xaml=WINDOW.replace('<ListView Grid.Row="1" ItemsSource="{Binding Entries}"><ListView.View><GridView><GridViewColumn Header="Message"/></GridView></ListView.View></ListView>',
                '<ListView Grid.Row="1" ItemsSource="{Binding Entries}"><ListView.ItemTemplate><DataTemplate><TextBlock/></DataTemplate></ListView.ItemTemplate></ListView>')
            _,theme=fixture(Path(tmp),xaml)
            original=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'Not all Nexus lists are GridView-backed'):
                patch.patch_shared_dark_list_rows(Path(tmp))
            self.assertEqual(theme.read_bytes(),original)

    def test_existing_other_styles_fail_closed(self):
        with TemporaryDirectory() as tmp:
            _,theme=fixture(Path(tmp),dark=DARK_ORIGINAL.replace('</ResourceDictionary>','<Style TargetType="ListBoxItem"/></ResourceDictionary>'))
            with self.assertRaisesRegex(RuntimeError,'already has shared row overrides'):
                patch.patch_shared_dark_list_rows(Path(tmp))

    def test_reapply_fails_without_rewriting_patched_theme(self):
        with TemporaryDirectory() as tmp:
            _,theme=fixture(Path(tmp))
            patch.patch_shared_dark_list_rows(Path(tmp))
            first=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'already has shared row overrides'):
                patch.patch_shared_dark_list_rows(Path(tmp))
            self.assertEqual(theme.read_bytes(),first)

    def test_bad_original_style_fails_closed(self):
        with TemporaryDirectory() as tmp:
            _,theme=fixture(Path(tmp),dark=DARK_ORIGINAL.replace('#FF2A3550','#FF112233'))
            first=theme.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'Dark.xaml ListViewItem theme changed'):
                patch.patch_shared_dark_list_rows(Path(tmp))
            self.assertEqual(theme.read_bytes(),first)

if __name__=='__main__': unittest.main()
