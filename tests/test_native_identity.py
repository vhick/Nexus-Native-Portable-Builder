"""Regression checks for Nexus.App WPF helper source imports (b1r3 CS0103 failure)."""
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'patches' / 'NativePortableIdentity.cs'

class NativePortableIdentityTests(unittest.TestCase):
    def test_explicit_system_io_import_for_wpf_temporary_project(self):
        source = TEMPLATE.read_text(encoding='utf-8')
        self.assertRegex(source, r'(?m)^using\s+System\.IO\s*;')
        self.assertIn('Path.GetFullPath(AppContext.BaseDirectory)', source)
        self.assertIn('Path.DirectorySeparatorChar', source)
        self.assertIn('Path.AltDirectorySeparatorChar', source)

    def test_required_crypto_imports_and_namespace(self):
        source = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('using System.Security.Cryptography;', source)
        self.assertIn('using System.Text;', source)
        self.assertIn('namespace Nexus.App.Services;', source)
        self.assertIn('SHA256.HashData', source)

    def test_source_validation_rejects_missing_system_io(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('validator', ROOT / 'scripts' / 'validate_source.py')
        validator=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        valid=TEMPLATE.read_text(encoding='utf-8')
        validator.validate_native_identity_source(valid)
        no_import=valid.replace('using System.IO;\n', '')
        self.assertNotEqual(no_import, valid)
        with self.assertRaisesRegex(AssertionError, 'missing explicit using System.IO;'):
            validator.validate_native_identity_source(no_import)

    def test_source_validation_rejects_non_executable_root(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('validator', ROOT / 'scripts' / 'validate_source.py')
        validator=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        valid=TEMPLATE.read_text(encoding='utf-8')
        bad=valid.replace('Path.GetFullPath(AppContext.BaseDirectory)', 'Path.GetFullPath(Environment.CurrentDirectory)')
        self.assertNotEqual(bad, valid)
        with self.assertRaisesRegex(AssertionError, 'running executable location'):
            validator.validate_native_identity_source(bad)

if __name__=='__main__':
    unittest.main()
