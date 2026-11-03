from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from board import exchange, project, storage, watch_rules, lifecycle

AT = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)

class QuestionExecution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project.initialize(self.root, 'Example', 'Compare methods', 'Report')
        exchange.write(self.root, 'GPT', '[abcd1234] [design] [T101] Layout',
                       'Choose a layout', ask=True, options=['A','B'], now=AT-timedelta(hours=3))

    def decision(self, **extra):
        row = dict(id='decision1', by='GPT', kind='decision', task='T101',
                   body='Apply choice for [abcd1234]', why='Reversible layout',
                   at=(AT-timedelta(hours=1)).isoformat())
        row.update(extra)
        storage.append(self.root/'attachments/coordination.jsonl', row)

    def reminders(self):
        return [r for r in watch_rules.conditions(self.root, {}, AT.timestamp())
                if r['type']=='question_unanswered_30min']

    def test_recorded_execution_suppresses_executor_reminder_and_retains_review(self):
        self.assertEqual(len(self.reminders()), 1)
        self.decision()
        self.assertEqual(self.reminders(), [])
        self.assertEqual(len(exchange.open_questions(self.root, now=AT)), 1)
        self.assertTrue(any(r['owner']=='Claude' and r['code']=='exchange_reply_overdue'
                            for r in lifecycle.check(self.root, now=AT)))

    def test_exact_id_author_task_and_chronology(self):
        variants = [dict(body='Apply abcd12345'), dict(by='Claude'), dict(task='T102'),
                    dict(at=(AT-timedelta(hours=4)).isoformat()),
                    dict(at=(AT+timedelta(hours=1)).isoformat()), dict(at='invalid'),
                    dict(kind='note')]
        for variant in variants:
            with self.subTest(variant=variant):
                (self.root/'attachments/coordination.jsonl').unlink(missing_ok=True)
                self.decision(**variant)
                self.assertEqual(len(self.reminders()), 1)

    def test_lead_veto_restores_execution_reminder(self):
        self.decision()
        storage.append(self.root/'attachments/coordination.jsonl',
                       dict(id='veto1', by='Claude', kind='veto', ref='decision1',
                            at=(AT-timedelta(minutes=30)).isoformat()))
        self.assertEqual(len(self.reminders()), 1)

    def test_sensitive_categories_remain_for_lead_review(self):
        for kind in ['external','deletion','conclusion']:
            with self.subTest(kind=kind):
                path = self.root/'exchange/2026-01-01.md'
                path.write_text(path.read_text().replace('[design]', '['+kind+']').replace('[external]', '['+kind+']').replace('[deletion]', '['+kind+']'))
                self.assertEqual(self.reminders(), [])
                self.assertEqual(len(exchange.open_questions(self.root, now=AT)), 1)

    def test_future_or_other_author_veto_keeps_execution_registered(self):
        self.decision()
        for author, at in [('GPT',AT-timedelta(minutes=30)),('Claude',AT+timedelta(minutes=30))]:
            storage.append(self.root/'attachments/coordination.jsonl',
                           dict(id='veto2',by=author,kind='veto',ref='decision1',at=at.isoformat()))
        self.assertEqual(self.reminders(), [])

if __name__=='__main__': unittest.main()
