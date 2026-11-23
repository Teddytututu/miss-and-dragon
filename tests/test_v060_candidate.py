"""Candidate boundaries apply to the bytes shipped to a fresh installation."""
from pathlib import Path
import re, runpy, unittest

ROOT = Path(__file__).resolve().parents[1]


class CandidateBoundary(unittest.TestCase):
    def test_source_archive_ships_only_original_character_art(self):
        release = runpy.run_path(str(ROOT / 'scripts/release.py'))
        names = release['files']()
        art = [n for n in names if n.startswith('board/art/') and n.endswith('.png')]
        self.assertEqual(len(art), 51)
        self.assertTrue(all(re.fullmatch(r'(?:avatar-(?:user|claude|gpt)|(?:user|claude|gpt)-[a-z]+)\.png', n.rsplit('/', 1)[1]) for n in art))
        self.assertIn('board/art/avatar-claude.svg', names)
        self.assertIn('board/art/avatar-gpt.svg', names)


if __name__ == '__main__':
    unittest.main()
