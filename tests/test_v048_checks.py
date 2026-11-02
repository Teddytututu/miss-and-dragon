from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from board import project, storage


class ProcessChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        self.at = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def module(self):
        from board import checks
        return checks

    def registry(self, result=True):
        return {'example': dict(title='Example check', target=10, every_minutes=180,
            run=lambda root: dict(ok=result, detail='Observed'))}

    def test_ten_due_successes_solve_and_repeated_poll_keeps_count(self):
        checks = self.module()
        for i in range(10):
            now = self.at+timedelta(hours=i*3)
            row = checks.run(self.root, now=now, registry=self.registry())['example']
            self.assertEqual(row['streak'], i+1)
            self.assertEqual(row['solved'], i==9)
            again = checks.run(self.root, now=now, registry=self.registry())['example']
            self.assertEqual(again['streak'], i+1)
        self.assertEqual(len(row['history']), 10)

    def test_failure_resets_unknown_keeps_count_and_show_keeps_bytes(self):
        checks = self.module()
        checks.run(self.root, now=self.at, registry=self.registry())
        row = checks.run(self.root, now=self.at+timedelta(hours=3), registry=self.registry(None))['example']
        self.assertEqual(row['streak'], 1)
        row = checks.run(self.root, now=self.at+timedelta(hours=6), registry=self.registry(False))['example']
        self.assertEqual(row['streak'], 0)
        path = self.root/'attachments/checks.json'
        before = path.read_bytes()
        checks.run(self.root, show_only=True, registry=self.registry())
        self.assertEqual(path.read_bytes(), before)

    def test_default_check_requires_work_for_each_active_role(self):
        checks = self.module()
        (self.root/'board.md').write_text('| T001 | Build chart | queued: ready now | GPT |\n')
        self.assertTrue(checks.task_ready(self.root)['ok'])
        (self.root/'board.md').write_text('| T001 | Build chart | blocked: waiting for lead | GPT |\n')
        self.assertFalse(checks.task_ready(self.root)['ok'])
        value = storage.read(self.root/'project.json')
        value['paused_executor_roles'] = ['GPT']
        storage.write(self.root/'project.json', value)
        self.assertIsNone(checks.task_ready(self.root)['ok'])

    def test_cli_and_wake_share_due_record_and_show_preserves_it(self):
        import json, subprocess, sys
        repo = Path(__file__).resolve().parents[1]
        def call(*args):
            p = subprocess.run([sys.executable, str(repo/'scripts/agent.py'), '--as', 'GPT',
                '--data-dir', str(self.root), *args], cwd=repo, capture_output=True,
                text=True, encoding='utf-8')
            self.assertEqual(p.returncode, 0, p.stderr+p.stdout)
            return json.loads(p.stdout)['result']
        (self.root/'board.md').write_text('| T001 | Build chart | queued: ready now | GPT |\n')
        first = call('checks', 'run')['task_ready']
        self.assertEqual(first['streak'], 1)
        path = self.root/'attachments/checks.json'
        before = path.read_bytes()
        self.assertEqual(call('checks', 'show')['task_ready']['streak'], 1)
        self.assertEqual(path.read_bytes(), before)
        wake = call('wake')
        observed = wake.get('status', wake)['process_checks']['task_ready']
        self.assertEqual(observed['streak'], 1)
        self.assertEqual(len(observed['history']), 1)

    def test_changed_target_starts_fresh_and_checker_failure_is_unknown(self):
        checks = self.module()
        checks.run(self.root, now=self.at, registry=self.registry())
        registry = self.registry()
        registry['example']['target'] = 2
        row = checks.run(self.root, now=self.at+timedelta(hours=3), registry=registry)['example']
        self.assertEqual(row['streak'], 1)
        def failing(root):
            raise OSError('Observation unavailable')
        registry['example']['run'] = failing
        row = checks.run(self.root, now=self.at+timedelta(hours=6), registry=registry)['example']
        self.assertEqual(row['streak'], 1)
        self.assertIsNone(row['ok'])


if __name__ == '__main__':
    unittest.main()
