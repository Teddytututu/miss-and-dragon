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

if __name__=='__main__':unittest.main()
