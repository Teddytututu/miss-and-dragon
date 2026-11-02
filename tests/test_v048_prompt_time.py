from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import unittest


class PromptTime(unittest.TestCase):
    def test_clock_context_uses_given_offset_and_weekday_in_both_languages(self):
        path = Path(__file__).resolve().parents[1]/'scripts/prompt_time.py'
        spec = importlib.util.spec_from_file_location('prompt_time', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        now = datetime(2030, 1, 1, 0, 5, tzinfo=timezone(timedelta(hours=8)))
        self.assertEqual(module.context(now, 'en'), 'Current local time: 2030-01-01 00:05 Tuesday (UTC+0800).')
        self.assertEqual(module.context(now, 'zh-CN'), '现在是 2030-01-01 00:05 周二（UTC+0800）。')

    def test_example_hook_runs_without_touching_settings_and_wake_reads_clock_first(self):
        root = Path(__file__).resolve().parents[1]
        example = json.loads((root/'templates/claude-settings.example.json').read_text())
        hook = example['hooks']['UserPromptSubmit'][0]['hooks'][0]
        self.assertEqual(hook['type'], 'command')
        self.assertEqual(hook['command'], 'python scripts/prompt_time.py --language en')
        p = subprocess.run([sys.executable, 'scripts/prompt_time.py', '--language', 'en'],
            cwd=root, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('Current local time:', p.stdout)
        from board.wake_prompt import build
        prompt = build('GPT')
        self.assertLess(prompt.index('current local time'), prompt.index('scripts/agent.py'))


if __name__ == '__main__':
    unittest.main()
