import tempfile, unittest
from pathlib import Path
from datetime import datetime
from board import cadence, storage, scheduler, project
from scripts import night_watch, install_night_watch

class CadenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name);self.root=self.repo/'data'
        project.initialize(self.root,'Example')
    def tearDown(self):self.tmp.cleanup()
    def test_defaults_and_validation(self):
        self.assertEqual(len(cadence.view(self.root)['items']),13)
        cadence.configure(self.root,{'overrides':{'night_watch':{'minutes':7},'lead':{'minutes':90}}})
        self.assertEqual(cadence.minutes(self.root,'night_watch'),7)
        with self.assertRaises(ValueError):cadence.configure(self.root,{'overrides':{'night_watch':{'minutes':61}}})
        with self.assertRaises(ValueError):cadence.configure(self.root,{'order':['lead']})
        with self.assertRaises(ValueError):cadence.configure(self.root,{'overrides':{'weekly_tidy':{'weekday':7,'time':'20:00'}}})
        cadence.configure(self.root,{'overrides':{'night_watch':None}})
        self.assertEqual(cadence.minutes(self.root,'night_watch'),10)
    def test_schedule_fixed_and_guards(self):
        config={'overrides':{'lead':{'minutes':90},'front':{'minutes':100}}}
        normal={n:{'remaining':.7} for n in scheduler.AGENTS}
        s=scheduler.compute_schedule(normal,{},now=100,cadence=config)
        self.assertEqual(s['agents']['Claude']['interval_minutes'],90)
        self.assertEqual(s['sessions']['front']['interval_minutes'],100)
        urgent=scheduler.compute_schedule(normal,{'Claude':{'mentioned':True}},now=100,cadence=config)
        self.assertEqual(urgent['agents']['Claude']['interval_minutes'],20)
        low=scheduler.compute_schedule({'Claude':{'remaining':.03}}, {},now=100,cadence=config)
        self.assertTrue(low['agents']['Claude']['paused'])
        restored=scheduler.compute_schedule(normal,{},s,now=110,cadence={})
        automatic=scheduler.compute_schedule(normal,{},now=100)
        self.assertEqual(restored['agents']['Claude']['interval_minutes'],automatic['agents']['Claude']['interval_minutes'])
    def test_plans_and_install(self):
        cadence.configure_plans(self.root,{'GPT':{'subscriptions':2,'tier':'highest'},'Claude':{'subscriptions':0,'tier':'free'}})
        rows={r['id']:r for r in cadence.view(self.root)['items']}
        self.assertEqual(rows['execution']['suggested_minutes'],20)
        self.assertEqual(rows['lead']['suggested_minutes'],240)
        (self.repo/'scripts').mkdir();(self.repo/'scripts/night_watch.py').touch()
        cadence.configure(self.root,{'overrides':{'night_watch':{'minutes':7}}})
        for system in ['Windows','Linux']:
            plan=install_night_watch.build_plan(self.repo,system=system)
            self.assertEqual(plan['interval_minutes'],7)
        plan=install_night_watch.build_plan(self.repo,system='Windows')
        self.assertIn('-WindowStyle Hidden -Command',plan['action'])
        self.assertIn('-WindowStyle Hidden -Command',plan['task_xml'])
        self.assertNotIn('-EncodedCommand',plan['task_xml'])
        self.assertNotIn('<Hidden>true</Hidden>',plan['task_xml'])
    def test_weekly_dedup_ack_and_rules_follow_tidy(self):
        at=datetime(2026,11,1,19,59).timestamp()
        night_watch.patrol(self.repo,now=at)
        first=night_watch.patrol(self.repo,now=at+120)
        tidy=next(e for e in first if e['type']=='weekly_tidy')
        self.assertFalse(any(e['type']=='weekly_rules' for e in first))
        self.assertEqual(night_watch.patrol(self.repo,now=at+180),[])
        night_watch.acknowledge(self.repo,[tidy['id']])
        follow=night_watch.patrol(self.repo,now=at+240)
        self.assertEqual([e['type'] for e in follow],['weekly_rules'])
        night_watch.acknowledge(self.repo,[follow[0]['id']])
        self.assertEqual(night_watch.patrol(self.repo,now=at+300),[])

    def test_api_persistence_validation_and_origin(self):
        import http.client,json,threading
        from board.app import create_server,snapshot
        server=create_server(self.root,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def req(route,payload=None,origin=None):
            port=server.server_port;c=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
            c.request('POST' if payload is not None else 'GET',route,json.dumps(payload) if payload is not None else None,{'Origin':origin or f'http://127.0.0.1:{port}','Content-Type':'application/json'})
            r=c.getresponse();raw=r.read();c.close();return r.status,json.loads(raw)
        try:
            self.assertEqual(req('/api/cadence',{'overrides':{'lead':{'minutes':75}}})[0],200)
            self.assertEqual(next(r for r in req('/api/cadence')[1]['items'] if r['id']=='lead')['override'],{'minutes':75})
            self.assertEqual(req('/api/cadence',{'overrides':{'lead':{'minutes':19}}})[0],400)
            self.assertEqual(req('/api/cadence',{'order':cadence.IDS[::-1]},'https://example.com')[0],403)
            self.assertEqual(req('/api/display-name',{'user_name':'Example'})[1]['user_name'],'Example')
            self.assertIn('告诉 Claude',snapshot(self.root)['overview']['todo'][0]['what'])
            self.assertEqual(req('/api/project',{'question':'Which approach?','deliverable':'A comparison'})[0],200)
            self.assertEqual(snapshot(self.root)['overview']['todo'],[])
        finally:server.shutdown();server.server_close();thread.join()

    def test_messages_require_completed_results_in_both_languages(self):
        from board.writing import validate_message
        for text in ['我会查一下','稍后给你结果','收到，继续','抱歉，理解错了',"I will check the report", "I'll get back to you",'Got it, thanks','It is worth noting that this works']:
            self.assertTrue(validate_message(text),text)
        for text in ['四档对照完成，保留四分之一缓存时准确率下降 1.8 个点。','Four comparisons finished; quarter cache loses 1.8 points.']:
            self.assertEqual(validate_message(text),[],text)

    def test_schedule_completion_is_readable_to_assistants(self):
        from board import plan_checks
        days=[dict(date='2026-11-01',items=[dict(what='Read',kind='study',time='09:00'),dict(what='Lunch',kind='休息',time='12:00')])]
        storage.write(self.root/'overview.json',dict(schedule=days))
        key=plan_checks.project(days)[0]['items'][0]['check_id']
        storage.write(self.root/'attachments/plan-checks.json',{'items':{key:{'completed':True}}})
        summary=plan_checks.summary(self.root)
        self.assertEqual((summary['completed'],summary['pending']),(1,0))
        self.assertEqual(summary['items'][0]['what'],'Read')
        storage.write(self.root/'attachments/plan-checks.json',{'items':{key:{'completed':False}}})
        self.assertEqual(plan_checks.summary(self.root)['pending'],1)

if __name__=='__main__':unittest.main()
