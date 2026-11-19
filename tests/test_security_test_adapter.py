"""Fixture-only tests for the explicit portable ransomware consent default.

NOT a substitute for running patched upstream C# tests on Windows.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

script = Path(__file__).resolve().parents[1] / 'scripts' / 'apply_portable.py'
spec = importlib.util.spec_from_file_location('adapter_security', script)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

LEGACY = '''using Xunit;
class SettingsUpgradeTests {
    [Fact]
    public void A_settings_file_without_the_security_section_still_loads_its_defaults()
    {
        Assert.True(settings.Security.BehaviourMonitoring);
        Assert.True(settings.Security.RansomwareWatch);
    }
    [Fact]
    public void Sections_that_were_present_are_preserved()
    {
    }
}
'''

class SecurityMigrationTests(unittest.TestCase):
    def make_file(self, source):
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name) / 'SettingsUpgradeTests.cs'
        p.write_text(source, encoding='utf-8')
        self.addCleanup(tmp.cleanup)
        return p

    def test_update_exact_expectation_and_add_opt_in_check(self):
        p=self.make_file(LEGACY)
        patch.patch_portable_security_tests(p)
        result=p.read_text(encoding='utf-8')
        self.assertIn('Assert.False(settings.Security.RansomwareWatch);', result)
        self.assertEqual(result.count('Assert.True(settings.Security.RansomwareWatch);'),1)
        self.assertIn('Native_portable_explicit_ransomware_watch_opt_in_is_preserved', result)

    def test_second_patch_fails_closed(self):
        p=self.make_file(LEGACY)
        patch.patch_portable_security_tests(p)
        with self.assertRaisesRegex(RuntimeError,'expected one original migration-test'):
            patch.patch_portable_security_tests(p)

    def test_absent_test_anchor_fails_closed(self):
        p=self.make_file(LEGACY.replace('Assert.True(settings.Security.RansomwareWatch);', 'Assert.False(settings.Security.RansomwareWatch);'))
        with self.assertRaisesRegex(RuntimeError,'expected one upstream'):
            patch.patch_portable_security_tests(p)

    def test_ambiguous_expectations_fail_closed(self):
        p=self.make_file(LEGACY.replace('Assert.True(settings.Security.RansomwareWatch);','Assert.True(settings.Security.RansomwareWatch);\n        Assert.True(settings.Security.RansomwareWatch);'))
        with self.assertRaisesRegex(RuntimeError,'found 2'):
            patch.patch_portable_security_tests(p)

if __name__=='__main__': unittest.main()
