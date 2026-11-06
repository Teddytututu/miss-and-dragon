"""Behavior regressions for shared interface improvements."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class InterfaceUpdates(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node enables browser regressions')
    def test_interface_behaviors(self):
        result = subprocess.run(['node', '--test', 'tests/interface-updates.test.cjs','tests/note-wall.test.cjs','tests/result-tree.test.cjs'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
