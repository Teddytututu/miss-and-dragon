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
    def test_task_linked_todos_prompt_review_after_task_starts_and_keep_other_notes(self):
        from board import workflow_checks as w
        notes=[dict(what='Choose schedule',task='T001'),dict(what='Keep the application note')]
        row=dict(task='T001',owner='GPT',status='queued: waiting for owner')
        self.assertEqual(w.task_todo_issues(notes,[row]),[])
        row['status']='1/3 · Work · 约 21:00'
        self.assertEqual(w.task_todo_issues(notes,[row])[0]['task'],'T001')
        self.assertEqual(len(notes),2)
        self.assertTrue(w.task_todo_issues(notes,[]))
    def test_todo_cli_accepts_task_and_retains_unrelated_overview_fields(self):
        import importlib.util
        from types import SimpleNamespace
        spec=importlib.util.spec_from_file_location('workflow_agent',Path(__file__).resolve().parents[1]/'scripts/agent.py')
        agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
        storage.write(self.root/'overview.json',dict(sentinel=7))
        agent.cmd_todo(SimpleNamespace(op='add',until=None,what='Choose schedule',when='today',how='Open the course page',note='Group choice',task='T001',data_dir=self.root,who='GPT'))
        value=storage.read(self.root/'overview.json');self.assertEqual(value['todo'][0]['task'],'T001');self.assertEqual(value['sentinel'],7)
    def test_daily_open_source_reviews_have_distinct_responsible_assistants(self):
        from board import workflow_checks as w
        late=datetime(2026,1,12,14,tzinfo=timezone.utc)
        self.assertEqual(w.oss_sync_issues(self.root,late),[])
        p=self.root/'project.json';value=storage.read(p);value['open_source_sync']={'enabled':True};storage.write(p,value)
        self.assertTrue(any(r['code']=='oss_sync_missing' and r['owner']=='GPT' for r in w.oss_sync_issues(self.root,late)))
        folder=self.root/'attachments/open-source-sync';folder.mkdir(parents=True)
        report=folder/'2026-01-12.md';report.write_text('Review: pending Claude\nPrepared changes.\n')
        values=w.oss_sync_issues(self.root,late);self.assertEqual([r['owner'] for r in values],['Claude'])
        report.write_text('Review: returned: revise the example\n')
        self.assertEqual(w.oss_sync_issues(self.root,late)[0]['owner'],'GPT')

if __name__=='__main__':unittest.main()
