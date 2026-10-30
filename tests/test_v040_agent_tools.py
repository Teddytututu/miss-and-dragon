from pathlib import Path
from datetime import datetime,timedelta,timezone
import tempfile,unittest
from board import project,storage

class AgentTools(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        project.initialize(self.root,'Example study','Compare methods','Report')
    def tools(self):
        from board import agent_tools
        return agent_tools
    def test_question_kind_and_options_are_required(self):
        t=self.tools()
        for kind,options in [(None,['A','B']),('design',['A'])]:
            with self.assertRaises(ValueError):t.ask(self.root,'GPT','Choice','Which?',kind,options)
    def test_invalid_question_leaves_ledger_unchanged(self):
        t=self.tools()
        for title,options in [('', ['A','B']),('Two\nlines',['A','B']),('Choice',[3,'B'])]:
            with self.assertRaises(ValueError):t.ask(self.root,'GPT',title,'Which?','design',options)
        self.assertEqual(t.records(self.root),[])
    def test_concurrent_answers_close_question_once(self):
        from concurrent.futures import ThreadPoolExecutor
        t=self.tools();q=t.info(self.root,'GPT','Which report?')
        def attempt(_):
            try:t.answer(self.root,'Claude',q['id'],'report.html');return True
            except ValueError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sum(pool.map(attempt,range(2))),1)
        self.assertEqual(len([r for r in t.records(self.root) if r['kind']=='answer']),1)
    def test_missing_gpu_observations_are_explicit(self):
        value=self.tools().efficiency(self.root,'GPT')
        self.assertEqual(value['gpu_observation_count'],0)
        self.assertIsNone(value['own_gpu_idle_seconds'])
    def test_numbered_questions_preserve_history_and_answer_by_peer(self):
        t=self.tools();a=t.ask(self.root,'GPT','Choice','Which?','design',['A','B']);b=t.ask(self.root,'GPT','Other','Which?','budget',['A','B'])
        self.assertNotEqual(a['id'],b['id']);self.assertEqual(len(t.pending(self.root,'Claude')),2)
        with self.assertRaises(ValueError):t.answer(self.root,'GPT',a['id'],'A')
        t.answer(self.root,'Claude',a['id'],'A');self.assertEqual([r['id'] for r in t.pending(self.root,'Claude')],[b['id']])
    def test_info_records_query_and_answer(self):
        t=self.tools();row=t.info(self.root,'Claude','Where is the report?')
        self.assertEqual(t.pending(self.root,'GPT')[0]['id'],row['id'])
        t.answer(self.root,'GPT',row['id'],'reports/result.html');self.assertEqual(t.pending(self.root,'GPT'),[])
    def test_decisions_keep_original_and_lead_veto(self):
        t=self.tools();r=t.decide(self.root,'GPT','T001','Use a stable tie break','Keep the original ordering')
        with self.assertRaises(ValueError):t.veto(self.root,'GPT',r['id'],'Change it')
        t.veto(self.root,'Claude',r['id'],'Use the reviewed ordering')
        rows=t.records(self.root);self.assertEqual(rows[0]['body'],'Use a stable tie break');self.assertEqual(rows[-1]['kind'],'veto')
    def test_expiry_keeps_files_and_unrelated_fields(self):
        t=self.tools();now=datetime(2026,1,12,tzinfo=timezone.utc);p=self.root/'report.txt';p.write_text('result')
        storage.write(self.root/'overview.json',dict(sentinel={'keep':True},links=[dict(title='Old',path='report.txt',until='2026-01-11T00:00:00+00:00'),dict(title='Next',until='2026-01-13T00:00:00+00:00')],todo=[dict(what='Old task',until='2026-01-11T00:00:00+00:00')]))
        t.expire_due(self.root,now=now);d=storage.read(self.root/'overview.json')
        self.assertTrue(d['sentinel']['keep']);self.assertTrue(d['links'][0]['archived']);self.assertFalse(d['links'][1].get('archived',False));self.assertEqual(d['todo'],[]);self.assertTrue(p.is_file())
    def test_invalid_expiry_is_rejected(self):
        with self.assertRaises(ValueError):self.tools().expiry('tomorrow maybe')
    def test_plan_and_progress_upserts_preserve_other_fields(self):
        t=self.tools();storage.write(self.root/'overview.json',dict(sentinel=7,schedule=[],progress_lines=[]))
        t.plan(self.root,'2026-01-12','09:00','Read','研究');t.progress(self.root,'Evaluation','First');t.progress(self.root,'Evaluation','Second')
        d=storage.read(self.root/'overview.json');self.assertEqual(d['sentinel'],7);self.assertEqual(d['schedule'][0]['items'][0]['what'],'Read');self.assertEqual(len(d['progress_lines']),1);self.assertEqual(d['progress_lines'][0]['text'],'Second')
    def test_tree_update_requires_one_node_and_retains_children(self):
        t=self.tools();storage.write(self.root/'overview.json',dict(tree=[dict(title='Route',children=[dict(title='Child')])]))
        t.tree(self.root,'Route',status='done',summary='Complete',task='T001',result='Report')
        d=storage.read(self.root/'overview.json')['tree'][0];self.assertEqual(d['children'][0]['title'],'Child');self.assertEqual(d['tasks'],['T001']);self.assertEqual(d['results'],['Report'])
        with self.assertRaises(ValueError):t.tree(self.root,'Missing',status='done')
    def test_finding_is_lead_owned_and_append_only(self):
        t=self.tools()
        with self.assertRaises(ValueError):t.finding(self.root,'GPT','A result','T001')
        t.finding(self.root,'Claude','First result','T001');before=(self.root/'findings.md').read_bytes()
        t.finding(self.root,'Claude','Second result','T001');self.assertTrue((self.root/'findings.md').read_bytes().startswith(before))
    def test_task_name_limit_and_retitle_preserve_status(self):
        t=self.tools();p=self.root/'tasks/T001-example.md';p.parent.mkdir(exist_ok=True);p.write_text('# Example\n\nKeep this body.\n')
        (self.root/'board.md').write_text('| T001 | [Example](tasks/T001-example.md) | 排队 | GPT | 2026-01-11T00:00:00+00:00 |\n')
        with self.assertRaises(ValueError):t.retitle(self.root,'T001','A title much longer than sixteen')
        t.retitle(self.root,'T001','Short title');self.assertIn('| 排队 | GPT |',(self.root/'board.md').read_text());self.assertIn('Keep this body.',p.read_text())
    def test_inbox_keeps_images_and_does_not_require_assistant_report_replies(self):
        t=self.tools();now=datetime.now(timezone.utc).isoformat();folder=self.root/'attachments/discussion';folder.mkdir(parents=True,exist_ok=True);image='a'*32+'.png';(folder/'images').mkdir(exist_ok=True);(folder/'images'/image).write_bytes(b'image')
        storage.append(folder/'web-main.jsonl',dict(id='report',author='Claude',body='The batch is complete.',created_at=now,images=[image],channel='main'))
        a=t.inbox(self.root,'GPT');self.assertEqual(a['pending_replies'],[]);self.assertTrue(Path(a['new_messages'][0]['image_paths'][0]).is_absolute());self.assertEqual(t.inbox(self.root,'GPT')['new_messages'],[])
    def test_efficiency_uses_only_owned_gpu_observations(self):
        t=self.tools();storage.write(self.root/'attachments/gpu-observations.json',{'items':[dict(owner='GPT',idle_seconds=120),dict(owner='other',idle_seconds=999)]})
        self.assertEqual(t.efficiency(self.root,'GPT')['own_gpu_idle_seconds'],120)
    def test_acknowledgment_requires_existing_ids_and_records_result(self):
        t=self.tools();path=self.root/'attachments/night-watch/events.json';storage.write(path,dict(events=[dict(id='done:one',type='job_done')]))
        with self.assertRaises(ValueError):t.acknowledge(self.root,'GPT',['other'],'Checked')
        t.acknowledge(self.root,'GPT',['done:one'],'Result collected')
        self.assertEqual(storage.read(path)['events'],[]);self.assertEqual(storage.lines(self.root/'attachments/event-results.jsonl')[0]['result'],'Result collected')
    def test_active_research_staleness_is_reported_after_a_day(self):
        from board import stability
        now=datetime(2026,1,12,tzinfo=timezone.utc)
        d=dict(progress_lines=[dict(line='Route',updated=(now-timedelta(hours=25)).isoformat())],tree=[dict(title='Active',status='doing',updated=(now-timedelta(hours=25)).isoformat()),dict(title='Done',status='done',updated=(now-timedelta(hours=25)).isoformat())])
        issues=stability.issues(self.root,now,d)
        self.assertEqual(sum(r['code']=='progress_stale' for r in issues),1);self.assertEqual(sum(r['code']=='tree_stale' for r in issues),1)

class AgentToolsCLI(unittest.TestCase):
    setUp=AgentTools.setUp
    def agent(self,who,*args):
        import subprocess,sys
        root=Path(__file__).resolve().parents[1]
        r=subprocess.run([sys.executable,str(root/'scripts/agent.py'),'--data-dir',str(self.root),'--as',who,*args],capture_output=True,text=True,encoding='utf-8')
        value=__import__('json').loads(r.stdout);return r.returncode,value
    def test_cli_numbered_question_answer_and_kind_validation(self):
        code,value=self.agent('GPT','ask','Choice','Pick a route','--option','A','--option','B');self.assertEqual(code,1);self.assertIn('--kind',value['error'])
        code,value=self.agent('GPT','ask','Choice','Pick a route','--kind','design','--option','A','--option','B');self.assertEqual(code,0,value)
        code,answer=self.agent('Claude','answer',value['result']['id'],'A');self.assertEqual(code,0,answer)
    def test_cli_info_and_execution_choice(self):
        code,q=self.agent('Claude','info','Where is the report?');self.assertEqual(code,0,q)
        code,a=self.agent('GPT','info','report.html','--answer',q['result']['id']);self.assertEqual(code,0,a)
        code,q=self.agent('GPT','decide','T001','Stable ordering','--why','Repeatability');self.assertEqual(code,0,q)
        code,a=self.agent('Claude','veto',q['result']['id'],'Use reviewed ordering');self.assertEqual(code,0,a)
    def test_cli_expiring_card_and_patrol_mood(self):
        code,a=self.agent('GPT','file','add','--title','Report','--path','report.html','--until','2026-01-11T12:00:00+00:00');self.assertEqual(code,0,a)
        code,a=self.agent('GPT','patrol','Checked');self.assertEqual(code,1);self.assertIn('--mood',a['error'])
        code,a=self.agent('GPT','patrol','Checked','--mood','calm');self.assertEqual(code,0,a)
        self.assertTrue(storage.read(self.root/'overview.json')['links'][0]['archived'])

if __name__=='__main__':unittest.main()
