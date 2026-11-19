"""Regression for Nexus upstream ShellIntegrationService unregister formatting drift.

These controlled fixtures test text transformation only, NOT Windows compilation or
registry behavior. The real selected upstream commit must pass in GitHub Actions.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

script = Path(__file__).resolve().parents[1] / 'scripts' / 'apply_portable.py'
spec = importlib.util.spec_from_file_location('nexus_patch', script)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class ShellPatchTests(unittest.TestCase):
    def verify(self, source, newline='\n'):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'ShellIntegrationService.cs'
            file.write_bytes(source.replace('\n', newline).encode('utf-8'))
            patch.patch_shell_unregister(file)
            result = file.read_text(encoding='utf-8')
            self.assertIn('using var owned = shell?.OpenSubKey(KeyName);', result)
            self.assertIn('using var command = owned.OpenSubKey("command");', result)
            self.assertIn('StringComparison.OrdinalIgnoreCase', result)
            self.assertIn('shell!.DeleteSubKeyTree(KeyName);', result)
            self.assertNotIn('if (shell?.OpenSubKey(KeyName) is null)', result)
            # A second application must reject the already patched file.
            with self.assertRaisesRegex(RuntimeError, 'expected 1 matching audited'):
                patch.patch_shell_unregister(file)

    def test_exact_statement_sequence(self):
        self.verify('''                if (shell?.OpenSubKey(KeyName) is null)
                    continue;
                shell.DeleteSubKeyTree(KeyName);''')

    def test_crlf_and_blank_lines(self):
        self.verify('''                if (shell?.OpenSubKey(KeyName) is null)

                    continue;

                shell.DeleteSubKeyTree(KeyName);''', '\r\n')

    def test_whitespace_indentation_variation(self):
        self.verify('''\t\t\tif  ( shell?.OpenSubKey(KeyName) is null )
\t\t\t\tcontinue;
\t\t\tshell.DeleteSubKeyTree(KeyName);''')

    def test_fail_closed_on_changed_behavior(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'ShellIntegrationService.cs'
            original='''if (shell?.OpenSubKey(KeyName) is null)
    continue;
shell.DeleteSubKeyTree(unrelatedKey);'''
            file.write_text(original, encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'expected 1 matching audited'):
                patch.patch_shell_unregister(file)
            self.assertEqual(original, file.read_text(encoding='utf-8'))

    def test_fail_closed_on_ambiguous_multiple_sequences(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'ShellIntegrationService.cs'
            block='''    if (shell?.OpenSubKey(KeyName) is null)
        continue;
    shell.DeleteSubKeyTree(KeyName);'''
            file.write_text(block+'\n'+block, encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'got 2'):
                patch.patch_shell_unregister(file)
            self.assertEqual(block+'\n'+block, file.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
