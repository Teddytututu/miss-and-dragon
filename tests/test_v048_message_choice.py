"""Only an assistant's explicit decision closes an owner message."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import tempfile
import unittest
from board import agent_tools, project, storage, stability


class MessageChoice(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project.initialize(self.root, 'Example', 'Compare approaches', 'Table')
        self.room = self.root / 'attachments/discussion'
        self.at = datetime.now(timezone.utc)
        storage.append(self.room / 'web-main.jsonl', dict(
            id='one', author='owner', body='Thanks', images=[], channel='main',
            created_at=(self.at-timedelta(hours=4)).isoformat()))

    def pending(self, who='GPT'):
        return {p['id'] for p in agent_tools.inbox(self.root, who)['pending_replies']}

    def test_ordinary_and_automatic_reactions_keep_message_pending(self):
        agent_tools.react_owed(self.root, 'GPT')
        storage.append(self.room / 'reactions.jsonl', dict(
            actor='GPT', message_id='one', emoji='💡', active=True))
        self.assertIn('one', self.pending())
        issues = stability.issues(self.root, self.at, {}, owner='GPT')
        self.assertTrue(any(i['code']=='owner_reply_overdue' for i in issues))

    def test_explicit_enough_is_role_specific_and_removal_reopens(self):
        agent_tools.react_message(self.root, 'GPT', 'one', '💡', enough=True)
        self.assertNotIn('one', self.pending())
        self.assertIn('one', self.pending('Claude'))
        self.assertFalse(any(i['code']=='owner_reply_overdue' for i in
            stability.issues(self.root, self.at, {}, owner='GPT')))
        agent_tools.react_message(self.root, 'GPT', 'one', '💡', remove=True)
        self.assertIn('one', self.pending())
        self.assertEqual(len(storage.lines(self.root/'attachments/inbox/ack-only.jsonl')), 2)

    def test_edit_invalidates_old_decision_and_text_reply_closes_message(self):
        agent_tools.react_message(self.root, 'GPT', 'one', '💡', enough=True)
        original = storage.lines(self.room/'web-main.jsonl')[0]
        storage.write_bytes(self.room/'web-main.jsonl', ( __import__('json').dumps(dict(original, body='Please explain'))+'\n').encode())
        self.assertIn('one', self.pending())
        storage.append(self.room/'web-main.jsonl', dict(id='answer', author='GPT',
            parent_id='one', body='Here is the explanation', channel='main',
            created_at=self.at.isoformat()))
        self.assertNotIn('one', self.pending())

    def test_agent_cli_enough_reaches_persistent_inbox(self):
        import json, subprocess, sys
        repo = Path(__file__).resolve().parents[1]
        p = subprocess.run([sys.executable, str(repo/'scripts/agent.py'), '--as', 'GPT',
            '--data-dir', str(self.root), 'react', 'one', '💡', '--enough'],
            cwd=repo, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(p.returncode, 0, p.stderr+p.stdout)
        self.assertTrue(json.loads(p.stdout)['ok'])
        self.assertNotIn('one', self.pending())

    def test_patrol_keeps_reaction_choice_with_assistant(self):
        import subprocess, sys
        import json
        row = storage.lines(self.room/'web-main.jsonl')[0]
        row['created_at'] = datetime.now(timezone.utc).isoformat()
        storage.write_bytes(self.room/'web-main.jsonl', (json.dumps(row)+'\n').encode())
        repo = Path(__file__).resolve().parents[1]
        p = subprocess.run([sys.executable, str(repo/'scripts/agent.py'), '--as', 'GPT',
            '--data-dir', str(self.root), 'patrol', 'Checking the work', '--mood', 'calm'],
            cwd=repo, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(p.returncode, 0, p.stderr+p.stdout)
        self.assertEqual(storage.lines(self.room/'reactions.jsonl'), [])
        self.assertIn('one', self.pending())

    def test_enough_requires_live_owner_message_and_valid_reaction(self):
        for mid, emoji in [('missing', '💡'), ('one', 'bad')]:
            with self.assertRaises(ValueError):
                agent_tools.react_message(self.root, 'GPT', mid, emoji, enough=True)
        with self.assertRaises(ValueError):
            agent_tools.react_message(self.root, 'GPT', 'one', '💡', enough=True, remove=True)
        self.assertEqual(storage.lines(self.root/'attachments/inbox/ack-only.jsonl'), [])


if __name__ == '__main__':
    unittest.main()
