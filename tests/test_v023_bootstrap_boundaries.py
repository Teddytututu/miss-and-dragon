"""First-run output and emote filesystem boundaries use local fixtures only."""
from pathlib import Path
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from board import onboarding

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/t162-independent-review/test-fixtures'
WORK.mkdir(parents=True, exist_ok=True)


def module(name):
    spec = importlib.util.spec_from_file_location('boundary_' + name, ROOT / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class BootstrapBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bootstrap = module('bootstrap')
    def link_directory(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            env = dict(os.environ, RESEARCH_TEST_LINK=str(link), RESEARCH_TEST_TARGET=str(target))
            subprocess.run([shutil.which('powershell.exe') or 'pwsh', '-NoProfile', '-NonInteractive',
                            '-Command', '$null = New-Item -ItemType Junction -Path $env:RESEARCH_TEST_LINK -Target $env:RESEARCH_TEST_TARGET'],
                           env=env, check=True, capture_output=True,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        else:
            link.symlink_to(target, target_is_directory=True)

    def test_first_run_cp1252_keeps_prompt_choices_and_continues_registration(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding='cp1252', errors='strict')
        with patch.object(self.bootstrap, 'register_night_watch', return_value={'status': 'registered'}), contextlib.redirect_stdout(stream):
            result = self.bootstrap.first_run_options(sys.executable, self.root / 'data', None, None, 'install')
        stream.flush()
        text = raw.getvalue().decode(stream.encoding)
        self.assertEqual(result['night_watch']['status'], 'registered')
        self.assertFalse(result['emotes']['decision_required'])
        self.assertIn('--download-emotes', text)
        self.assertIn('--unicode-emotes', text)
        self.assertIn('Unicode', text)

    def test_first_run_utf8_preserves_chinese_prompt(self):
        stream = io.StringIO()
        with patch.object(self.bootstrap, 'register_night_watch', return_value={'status': 'registered'}), contextlib.redirect_stdout(stream):
            self.bootstrap.first_run_options(sys.executable, self.root / 'data', None, None, 'install')
        self.assertIn(onboarding.EMOTE_PROMPT, stream.getvalue())

    def test_cp1252_opt_in_prints_guide_and_keeps_registration_actionable(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding='cp1252', errors='strict')
        watch = {'status': 'manual', 'manual_command': 'python scripts/install_night_watch.py --install',
                 'error': '调度错误', 'report': {'detail': '需手动接续'}}
        with patch.object(self.bootstrap, 'register_night_watch', return_value=watch), contextlib.redirect_stdout(stream):
            result = self.bootstrap.first_run_options(sys.executable, self.root / 'data', 'download', None, 'install')
        stream.flush()
        text = raw.getvalue().decode(stream.encoding)
        self.assertEqual(result['night_watch']['status'], 'manual')
        self.assertEqual(result['emotes']['mode'], 'unicode')
        self.assertIn('docs/local-emotes.md', text)
        self.assertIn('install_night_watch.py', text)

    def test_cp1252_unicode_manual_command_has_an_exact_local_record(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding='cp1252', errors='strict')
        command = 'python scripts/install_night_watch.py --project-root "研究目录" --install'
        watch = {'status': 'manual', 'manual_command': command}
        data = self.root / 'data'
        with patch.object(self.bootstrap, 'register_night_watch', return_value=watch), contextlib.redirect_stdout(stream):
            self.bootstrap.first_run_options(sys.executable, data, None, None, 'install')
        stream.flush()
        text = raw.getvalue().decode(stream.encoding)
        self.assertIn('attachments/onboarding.json', text)
        self.assertIn('install_night_watch.py', text)
        import json
        saved = json.loads((data / 'attachments/onboarding.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['night_watch']['manual_command'], command)

    def test_local_emote_directory_junction_stays_private(self):
        from board import assets
        data = self.root / 'data'
        target = self.root / 'other-project'
        self.link_directory(data / 'emotes', target)
        try:
            (target / 'manifest.json').write_text('[{"id":123,"label":"Other project"}]', encoding='utf-8')
            Image.new('RGB',(8,8)).save(target / '123.png')
            self.assertEqual(assets.reaction_catalog(data), [])
        finally:
            os.rmdir(data / 'emotes') if os.name == 'nt' else (data / 'emotes').unlink()


if __name__ == '__main__':
    unittest.main()
