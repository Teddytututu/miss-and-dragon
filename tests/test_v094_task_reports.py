from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from board import project, storage, workflow_checks


class TaskReports(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        self.at = datetime.now(timezone.utc)
        self.accepted = self.at - timedelta(hours=3)
        storage.append(self.root/'attachments/task-flow.jsonl', dict(
            task='T1', action='accept', by='Claude', at=self.accepted.isoformat()))

    def issues(self):
        return workflow_checks.result_report_issues(self.root, self.at)

    def test_cli_keeps_task_out_of_body(self):
        repo = Path(__file__).resolve().parents[1]
        proc = subprocess.run([sys.executable, str(repo/'scripts/agent.py'),
            '--data-dir', str(self.root), '--as', 'GPT', 'say',
            'The result page is ready.', '--task', 'T1'],
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        json.loads(proc.stdout)
        row = project.all_posts(self.root)[-1]
        self.assertEqual(row['task'], 'T1')
        self.assertEqual(row['body'], 'The result page is ready.')

    def test_retry_preserves_task_identity(self):
        project.post(self.root, 'GPT', 'Ready', client_id='retry-task-000001', task='T1')
        with self.assertRaises(ValueError):
            project.post(self.root, 'GPT', 'Ready', client_id='retry-task-000001', task='T10')
        with self.assertRaises(ValueError):
            project.post(self.root, 'GPT', 'Ready', task='bad')

    def test_exact_metadata_and_withdrawal(self):
        project.post(self.root, 'Claude', 'T1 is ready', task='T10')
        self.assertEqual([r['task'] for r in self.issues()], ['T1'])
        reply = project.post(self.root, 'Claude', 'The result page is ready', task='T1')
        self.assertEqual(self.issues(), [])
        project.delete_message(self.root, reply['id'], 'Claude', assistant=True)
        self.assertEqual([r['task'] for r in self.issues()], ['T1'])

    def test_legacy_text_boundary_and_grace(self):
        project.post(self.root, 'Claude', 'T10 is ready')
        self.assertEqual(len(self.issues()), 1)
        project.post(self.root, 'Claude', 'T1 is ready')
        self.assertEqual(self.issues(), [])
        storage.append(self.root/'attachments/task-flow.jsonl', dict(
            task='T2', action='accept', by='Claude', at=(self.at-timedelta(hours=2)).isoformat()))
        self.assertEqual(self.issues(), [])

    def test_old_report_does_not_cover_new_acceptance(self):
        storage.append(project.ledger(self.root), dict(id='old', author='Claude',
            body='T1 is ready', task='T1', created_at=(self.accepted-timedelta(hours=3)).isoformat()))
        self.assertEqual(len(self.issues()), 1)


if __name__ == '__main__':
    unittest.main()
