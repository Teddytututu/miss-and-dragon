from datetime import datetime, timezone
from pathlib import Path
import tempfile, unittest
from board import project, storage, lifecycle

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);project.initialize(self.root,'Example project','Compare methods','Report')
        (self.root/'tasks').mkdir(exist_ok=True)
        self.now=datetime(2026,1,12,12,tzinfo=timezone.utc)
    def test_idle_executor_alert_goes_to_lead_and_ready_work_suppresses_it(self):
        from board import workflow_checks as w
        self.assertEqual(w.idle_roles(self.root,[]),['GPT'])
        for status in ['1/4 · Read sources · 约 21:00','queued: ready now','rejected: revise table']:
            self.assertEqual(w.idle_roles(self.root,[dict(task='T001',owner='GPT',status=status)]),[])
        issues=lifecycle.check(self.root,now=self.now)
        self.assertTrue(any(r['code']=='idle_executor' and r['owner']=='Claude' for r in issues))
    def test_configured_executor_roles_are_checked_separately_and_pause_is_respected(self):
        from board import workflow_checks as w
        p=self.root/'project.json';value=storage.read(p);value['executor_roles']=['research','chores'];storage.write(p,value)
        (self.root/'tasks/T001-first.md').write_text('# First\nExecution role: research\n')
        row=dict(task='T001',owner='GPT',status='1/3 · Read · 约 21:00')
        self.assertEqual(w.idle_roles(self.root,[row]),['chores'])
        value['paused_executor_roles']=['chores'];storage.write(p,value)
        self.assertEqual(w.idle_roles(self.root,[row]),[])
    def test_prompt_checks_lengths_jargon_and_archived_references(self):
        from board import workflow_checks as w
        (self.root/'instructions.md').write_text('T007\n'+'a'*4501)
        (self.root/'tasks/archive.md').write_text('| T007 | Example | accepted | GPT | 2026-01-01 |\n')
        storage.write(self.root/'attachments/wake-prompts.json',{'GPT':'x'*1201,'Claude':'identity boundary and admission gate'})
        values=w.prompt_readability_issues(self.root)
        self.assertTrue(any('instructions.md' in v and 'T007' in v for v in values))
        self.assertTrue(any('GPT' in v for v in values));self.assertTrue(any('Claude' in v for v in values))
        self.assertTrue(any(r['code']=='prompt_readability' and r['owner']=='Claude' for r in lifecycle.check(self.root,now=self.now)))
    def test_plain_notes_and_questions_reject_before_writing_any_record(self):
        from board import exchange, agent_tools
        for body in ['x'*601,'Digest '+'a'*64,'identity boundary, admission gate, byte contract']:
            with self.assertRaises(ValueError):exchange.write(self.root,'GPT','Update',body)
            with self.assertRaises(ValueError):agent_tools.ask(self.root,'GPT','Choice',body,'design',['A','B'])
        self.assertEqual(agent_tools.records(self.root),[])
        self.assertEqual(exchange.entries(self.root),[])
        exchange.write(self.root,'GPT','Update','The table is ready. Please review it.')
        self.assertEqual(len(exchange.entries(self.root)),1)
    def test_nightly_review_is_due_after_2230_and_date_requires_heading(self):
        from board import workflow_checks as w
        early=datetime(2026,1,12,14,29,tzinfo=timezone.utc)
        late=early.replace(minute=30)
        self.assertEqual(w.lead_review_issues(self.root,early),[])
        self.assertTrue(w.lead_review_issues(self.root,late))
        p=self.root/'lead-review.md';p.write_text('Mentioned 2026-01-12 in the error log.\n')
        self.assertTrue(w.lead_review_issues(self.root,late))
        p.write_text('## 2026-01-12\n- Judgment: Checked the wrong total.\n- Cause: Used an old row.\n- Change: Read the current row.\n- Tomorrow: Check counts.\n')
        self.assertEqual(w.lead_review_issues(self.root,late),[])

if __name__=='__main__':unittest.main()
