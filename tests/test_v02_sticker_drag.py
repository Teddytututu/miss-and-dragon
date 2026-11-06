"""Exercise sticker pointer behavior in the packaged JavaScript."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StickerDragTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for JavaScript regressions')
    def test_sticker_interactions(self):
        result = subprocess.run(['node', 'tests/sticker-drag.test.cjs'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
