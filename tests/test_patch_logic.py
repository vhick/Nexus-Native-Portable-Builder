"""String-anchor fixture test; not a substitute for real checked-out upstream CI compilation."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

script=Path(__file__).resolve().parents[1]/'scripts/apply_portable.py'
spec=importlib.util.spec_from_file_location('nexus_adapter',script)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PatchAnchorFixtureTests(unittest.TestCase):
    def test_core_and_pipe_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'NexusPaths.cs'
            p.write_text('/// (%APPDATA%\\Nexus in production, a temp dir in tests).\n'
                'Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Nexus")',encoding='utf-8')
            mod.change(p,mod.AUDITED_ANCHOR,mod.PORTABLE_ANCHOR)
            self.assertIn('Path.Combine(AppContext.BaseDirectory, "Data")',p.read_text(encoding='utf-8'))
            # Reapplying must fail rather than silently going to main or overwriting source.
            with self.assertRaisesRegex(RuntimeError,'Already patched'):
                mod.change(p,mod.AUDITED_ANCHOR,mod.PORTABLE_ANCHOR)
if __name__=='__main__':unittest.main()
