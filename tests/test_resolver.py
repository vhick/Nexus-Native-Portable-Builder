import importlib.util
import pathlib
import unittest
from unittest.mock import patch

path=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'resolve_source.py'
spec=importlib.util.spec_from_file_location('nexus_resolver',path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ResolverTests(unittest.TestCase):
    def test_numeric_semver(self):
        self.assertGreater(mod.stable('v2.10.0'),mod.stable('v2.9.10'))
        self.assertIsNone(mod.stable('v2.3.0-rc.1'))
        self.assertIsNone(mod.stable('nightly'))
        self.assertIsNone(mod.stable('main'))
    def test_never_use_main_if_no_stable_tag(self):
        with patch.object(mod,'get',return_value=[]):
            with self.assertRaisesRegex(RuntimeError,'No suitable official stable'):
                mod.resolve('',False)
    def test_reject_untagged_without_consent(self):
        with self.assertRaisesRegex(RuntimeError,'allow_untagged=true'):
            mod.resolve('a'*40,False)
    def test_exact_commit_identity_must_match(self):
        with patch.object(mod,'get',return_value={'sha':'b'*40}):
            with self.assertRaisesRegex(RuntimeError,'SHA mismatch'):
                mod.resolve('a'*40,True)
    def test_prereleases_excluded(self):
        def api(path):
            if '/releases?' in path:return [{'tag_name':'v1.2.3-beta.1','draft':False,'prerelease':True}]
            if '/tags?' in path:return [{'name':'v1.2.3-rc.1'}]
            raise AssertionError('Unexpected call')
        with patch.object(mod,'get',side_effect=api):
            with self.assertRaisesRegex(RuntimeError,'No suitable official stable'):
                mod.resolve('',False)
    def test_highest_numeric_tag(self):
        def api(path):
            if '/releases?' in path:return []
            if '/tags?' in path:return [{'name':'v1.9.0'},{'name':'v1.10.0'}]
            if '/git/ref/tags/v1.10.0' in path:return {'object':{'type':'commit','sha':'a'*40}}
            raise AssertionError(path)
        with patch.object(mod,'get',side_effect=api):
            self.assertEqual(mod.resolve('',False),('v1.10.0','a'*40,'STABLE_TAG'))
if __name__=='__main__':unittest.main()
