"""Candidate boundaries apply to the bytes shipped to a fresh installation."""
from pathlib import Path
import runpy, unittest

ROOT = Path(__file__).resolve().parents[1]


class CandidateBoundary(unittest.TestCase):
    def test_source_archive_uses_original_svg_character_art(self):
        release = runpy.run_path(str(ROOT / 'scripts/release.py'))
        names = release['files']()
        self.assertFalse(any(n.startswith('board/art/') and n.endswith('.png') for n in names))
        self.assertIn('board/art/avatar-claude.svg', names)
        self.assertIn('board/art/avatar-gpt.svg', names)


if __name__ == '__main__':
    unittest.main()
