"""Controlled temp fixtures for b1r9 audit-report packaging; no binaries distributed."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util
import json
import struct
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nexus_native_package_b1r9',ROOT/'scripts/package_native.py')
pkg=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)


def prepare(root):
    """Create synthetic test inputs in a throwaway temp directory ONLY."""
    published=root/'publish'; published.mkdir()
    for name in ('Nexus.exe','Nexus.Scanner.exe'):
        # Fake PE signature ONLY to unit-test the package validator, never a
        # claimed working Nexus executable or a file distributed with the kit.
        b=bytearray(2048); b[:2]=b'MZ'; struct.pack_into('<I',b,0x3c,0x80)
        b[0x80:0x84]=b'PE\0\0'; struct.pack_into('<H',b,0x84,0x8664)
        (published/name).write_bytes(b)
    assets=published/'assets';assets.mkdir()
    (assets/'patterns.txt').write_text('sample controlled fixture\n')
    upstream=root/'upstream';upstream.mkdir()
    (upstream/'LICENSE').write_text('test fixture')
    (upstream/'NOTICE.md').write_text('test fixture')
    reports=root/'ui-audit';reports.mkdir()
    for phase in ('upstream','patched'):
        (reports/(phase+'.json')).write_text(json.dumps({'phase':phase,'blockers':[],
            'xaml_files':['src/Nexus.App/MainWindow.xaml','src/Nexus.App/Themes/Dark.xaml']}))
        (reports/(phase+'.md')).write_text('# Static inventory\nNo blockers\n')
    return published,upstream,reports


class PackagingEvidenceTests(unittest.TestCase):
    def stage(self, root, reports):
        with patch.object(pkg.subprocess,'check_output',return_value='8.0.400\n'):
            return pkg.stage(root/'publish',root/'out',root/'upstream','dev2026',
                             'f5294a682565db62b01994ac12bf630a7f54b0d8',
                             'a'*40,'r9','development-commit',reports)

    def test_valid_reports_are_included_and_checksums_recorded(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,reports=prepare(root)
            (root/'out').mkdir()
            result=self.stage(root,reports)
            with zipfile.ZipFile(result) as z:
                names=z.namelist(); prefix=result.stem+'/'
                self.assertIn(prefix+'AUDITS/upstream.json',names)
                self.assertIn(prefix+'AUDITS/patched.md',names)
                identity=json.loads(z.read(prefix+'BUILD-IDENTITY.json'))
                self.assertEqual(len(identity['ui_source_inventory_sha256']),4)
                self.assertIn(prefix+'Data/',names)
                self.assertEqual(z.testzip(),None)

    def test_missing_audit_is_fatal(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,reports=prepare(root)
            (root/'out').mkdir()
            (reports/'patched.json').unlink()
            with self.assertRaisesRegex(ValueError,'Missing application-wide'):
                self.stage(root,reports)

    def test_blocked_audit_is_fatal_even_if_json_present(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,reports=prepare(root)
            (root/'out').mkdir()
            p=reports/'patched.json';info=json.loads(p.read_text());info['blockers']=['review new view']
            p.write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError,'Unverified/blocked'):
                self.stage(root,reports)


if __name__=='__main__': unittest.main()
