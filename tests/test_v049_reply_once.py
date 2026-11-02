from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from board import project, storage


class ReplyOnce(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        self.target = project.post(self.root, 'owner', 'Please explain')['id']

    def reply(self, author='GPT', body='Here is the result', **kwargs):
        return project.post(self.root, author, body, self.target, **kwargs)

    def test_second_text_reply_preserves_ledger_and_other_roles_and_targets_work(self):
        self.reply()
        path = project.ledger(self.root)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'once'):
            self.reply(body='Another result')
        self.assertEqual(path.read_bytes(), before)
        self.reply(author='Claude')
        other = project.post(self.root, 'owner', 'Another question')['id']
        project.post(self.root, 'GPT', 'Another answer', other)
        self.reply(author='owner')

    def test_client_retry_returns_original_before_duplicate_guard(self):
        first = self.reply(client_id='retry_same_answer_001')
        self.assertEqual(self.reply(client_id='retry_same_answer_001')['id'], first['id'])
        with self.assertRaisesRegex(ValueError, 'Retry content'):
            self.reply(body='Changed content', client_id='retry_same_answer_001')

    def test_deleted_and_attachment_only_replies_leave_text_available(self):
        attachment = self.reply(body='', images=['example.png'])
        answer = self.reply()
        project.delete_message(self.root, answer['id'], 'GPT', assistant=True)
        self.reply(body='Replacement answer')
        self.reply(body='', images=['another.png'])
        self.assertNotEqual(attachment['id'], answer['id'])

    def test_window_boundary_timezone_and_invalid_timestamps(self):
        at = datetime(2030, 1, 1, tzinfo=timezone.utc)
        def previous(created):
            storage.write_bytes(project.ledger(self.root), b'')
            storage.append(project.ledger(self.root), dict(id=self.target, author='owner', body='Question', channel='main', created_at=at.isoformat()))
            storage.append(project.ledger(self.root), dict(id='answer', author='GPT', body='Result', parent_id=self.target, channel='main', created_at=created))
        with patch('board.project.datetime', wraps=datetime) as clock:
            clock.now.return_value = at
            previous((at-timedelta(minutes=29)).astimezone(timezone(timedelta(hours=8))).isoformat())
            with self.assertRaises(ValueError):self.reply()
            for created in [(at-timedelta(minutes=30)).isoformat(), 'invalid', (at+timedelta(minutes=1)).isoformat()]:
                previous(created)
                self.reply()

    def test_simultaneous_replies_write_exactly_one_answer(self):
        def attempt(_):
            try:self.reply();return True
            except ValueError:return False
        with ThreadPoolExecutor(max_workers=2) as workers:
            self.assertEqual(sorted(workers.map(attempt, range(2))), [False, True])
        self.assertEqual(len([p for p in project.all_posts(self.root) if p.get('parent_id')==self.target]), 1)

    def test_post_command_rejects_duplicate_text(self):
        repo = Path(__file__).resolve().parents[1]
        cmd = [sys.executable, str(repo/'scripts/post_message.py'), 'GPT', 'Here is the result', '--root', str(self.root), '--reply', self.target]
        first = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(first.returncode, 0, first.stderr)
        second = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('once', second.stderr)


if __name__ == '__main__':unittest.main()
