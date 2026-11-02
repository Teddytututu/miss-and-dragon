from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from board import agent_tools, checks, project, storage


class CollaborationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        self.at = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def patrols(self, records):
        value = storage.read(self.root/'overview.json')
        value['patrols'] = records
        storage.write(self.root/'overview.json', value)

    def record(self, minutes=120):
        return dict(at=self.at.isoformat(), every_min=minutes,
                    next_at=(self.at+timedelta(minutes=minutes)).isoformat())

    def owner(self, mid='question', age=3, channel='main', **fields):
        row = dict(id=mid, author='owner', body='Please explain', channel=channel,
                   created_at=(self.at-timedelta(hours=age)).isoformat())
        row.update(fields)
        storage.append(project.ledger(self.root, channel), row)
        return row

    def test_patrol_grace_boundary_and_missing_records(self):
        self.assertIsNone(checks.patrols_on_time(self.root, now=self.at)['ok'])
        self.patrols(dict(Claude=self.record(), GPT=self.record(60)))
        self.assertTrue(checks.patrols_on_time(self.root, now=self.at+timedelta(minutes=105))['ok'])
        failed = checks.patrols_on_time(self.root, now=self.at+timedelta(minutes=105, seconds=1))
        self.assertFalse(failed['ok'])
        self.assertIn('GPT', failed['detail'])
        self.patrols(dict(GPT=self.record(60)))
        self.assertFalse(checks.patrols_on_time(self.root, now=self.at+timedelta(hours=4))['ok'])

    def test_patrol_bad_times_are_unknown_and_reading_keeps_bytes(self):
        self.patrols(dict(Claude=self.record(), GPT=dict(self.record(), at='invalid')))
        before = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertIsNone(checks.patrols_on_time(self.root, now=self.at)['ok'])
        after = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.patrols(dict(Claude=self.record(), GPT=self.record(-5)))
        self.assertIsNone(checks.patrols_on_time(self.root, now=self.at)['ok'])

    def test_owner_requires_text_or_explicit_active_reaction(self):
        self.owner()
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        agent_tools.react_message(self.root, 'GPT', 'question', '💡')
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        agent_tools.react_message(self.root, 'GPT', 'question', '💡', enough=True)
        self.assertTrue(checks.owner_answered(self.root, now=self.at)['ok'])
        agent_tools.react_message(self.root, 'GPT', 'question', '💡', remove=True)
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        project.post(self.root, 'Claude', 'Here is the answer', 'question')
        self.assertTrue(checks.owner_answered(self.root, now=self.at)['ok'])
        self.assertFalse((self.root/'attachments/inbox/GPT.json').exists())

    def test_edited_message_invalidates_ack_and_withdrawn_answer_reopens(self):
        row = self.owner()
        agent_tools.react_message(self.root, 'GPT', 'question', '💡', enough=True)
        import json
        storage.write_bytes(project.ledger(self.root), (json.dumps(dict(row, body='A changed question'))+'\n').encode())
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        reply = project.post(self.root, 'GPT', 'An answer', 'question')
        project.delete_message(self.root, reply['id'], 'GPT', assistant=True)
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])

    def test_owner_window_channels_and_non_session_answers(self):
        self.owner('old', age=25)
        self.owner('recent', age=1)
        self.owner('saved', channel='library')
        self.owner('removed')
        project.delete_message(self.root, 'removed', 'owner')
        self.assertTrue(checks.owner_answered(self.root, now=self.at)['ok'])
        self.owner('study', channel='study', age=2)
        storage.append(project.ledger(self.root, 'study'), dict(id='demo', author='GPT', body='Example', parent_id='study', client_id='demo-example'))
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        project.post(self.root, 'GPT', '', 'study', channel='study', images=['example.png'])
        self.assertFalse(checks.owner_answered(self.root, now=self.at)['ok'])
        project.post(self.root, 'GPT', 'An answer', 'study', channel='study')
        self.assertTrue(checks.owner_answered(self.root, now=self.at)['ok'])

    def test_registry_uses_observation_clock_for_due_checks(self):
        self.owner()
        self.patrols(dict(Claude=self.record(), GPT=self.record()))
        (self.root/'board.md').write_text('| T001 | Work | queued: ready now | GPT |\n', encoding='utf-8')
        result = checks.run(self.root, now=self.at)
        self.assertTrue(result['patrols_on_time']['ok'])
        self.assertFalse(result['owner_answered']['ok'])
        again = checks.run(self.root, now=self.at+timedelta(minutes=1))
        self.assertEqual(again['patrols_on_time']['streak'], 1)
        due = checks.run(self.root, now=self.at+timedelta(hours=3))
        self.assertFalse(due['patrols_on_time']['ok'])
        self.assertEqual(due['patrols_on_time']['streak'], 0)


if __name__ == '__main__':unittest.main()
