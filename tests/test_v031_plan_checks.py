"""Dated schedule completion with real loopback API and isolated project data."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from board import project,storage,plan_checks
from board.app import create_server

ROOT=Path(__file__).resolve().parents[1]


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);project.initialize(self.root,'Task checks')
        self.days=[dict(date='2026-11-01',items=[dict(time='10:00',what='Read a paper',kind='研究'),dict(time='12:00',what='Lunch',kind='休息')])]
        storage.write(self.root/'overview.json',dict(schedule=self.days,preserved=42))
        self.server=create_server(self.root,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)

    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()

    def req(self,path,payload=None,**headers):
        port=self.server.server_port
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        values={'Host':f'127.0.0.1:{port}','Origin':f'http://127.0.0.1:{port}','Content-Type':'application/json',**headers}
        connection.request('POST' if payload is not None else 'GET',path,body=json.dumps(payload) if payload is not None else None,headers=values)
        response=connection.getresponse();body=response.read();connection.close()
        return response.status,json.loads(body)

    def rows(self):
        code,value=self.req('/api/board');self.assertEqual(code,200,value)
        return value['overview']['schedule'][0]['items']

    def test_toggle_persists_and_preserves_original_schedule(self):
        before=(self.root/'overview.json').read_bytes();rows=self.rows();key=rows[0]['check_id']
        self.assertNotIn('check_id',rows[1])
        for value in (True,True,False):
            self.assertEqual(self.req('/api/plan/check',dict(id=key,completed=value))[0],200)
            self.assertEqual(self.rows()[0]['completed'],value)
        self.assertEqual((self.root/'overview.json').read_bytes(),before)

    def test_current_row_identity_and_existing_security_boundaries(self):
        key=self.rows()[0]['check_id']
        for payload in (dict(id='x',completed=True),dict(id=key,completed=1),dict(id=key,completed=True,what='changed')):
            self.assertEqual(self.req('/api/plan/check',payload)[0],400)
        self.assertEqual(self.req('/api/plan/check',dict(id=key,completed=True),Origin='https://example.com')[0],403)
        self.assertEqual(self.req('/api/plan/check',dict(id=key,completed=True),**{'X-Board-Identity':'GPT'})[0],403)

    def test_reschedule_is_stable_and_next_date_is_separate(self):
        key=self.rows()[0]['check_id'];self.req('/api/plan/check',dict(id=key,completed=True))
        self.days[0]['items'][0]['time']='15:00';self.days[0]['items'].reverse()
        storage.write(self.root/'overview.json',dict(schedule=self.days))
        self.assertEqual(self.rows()[-1]['check_id'],key);self.assertTrue(self.rows()[-1]['completed'])
        self.days[0]['date']='2026-11-02';storage.write(self.root/'overview.json',dict(schedule=self.days))
        self.assertNotEqual(self.rows()[-1]['check_id'],key);self.assertFalse(self.rows()[-1]['completed'])


class Identity(unittest.TestCase):
    def test_duplicate_entries_explicit_ids_and_relative_days(self):
        from datetime import date
        task=dict(time='10:00',what='Read',kind='研究')
        days=[dict(relative_day=0,items=[task,copy.deepcopy(task),dict(id='rest-task',what='Stretch',kind='健康',checkable=True)])]
        first=plan_checks.project(days,today=date(2026,11,1))[0]['items']
        second=plan_checks.project(days,today=date(2026,11,2))[0]['items']
        self.assertEqual(len(set(r['check_id'] for r in first)),3)
        self.assertNotEqual(first[0]['check_id'],second[0]['check_id'])
        self.assertNotIn('check_id',days[0]['items'][0])
        stable=[dict(date='2026-11-01',items=[dict(id='a',what='Old title',kind='研究')])]
        before=plan_checks.project(stable)[0]['items'][0]['check_id']
        stable[0]['items'][0]['what']='New title'
        self.assertEqual(plan_checks.project(stable)[0]['items'][0]['check_id'],before)

    def test_same_title_at_two_times_keeps_identity_when_reordered(self):
        tasks=[dict(time=t,what='Read',kind='研究') for t in ('10:00','14:00')]
        days=[dict(date='2026-11-01',items=tasks)]
        first={r['time']:r['check_id'] for r in plan_checks.project(days)[0]['items']}
        tasks.reverse()
        self.assertEqual(first,{r['time']:r['check_id'] for r in plan_checks.project(days)[0]['items']})


if __name__=='__main__':unittest.main()
