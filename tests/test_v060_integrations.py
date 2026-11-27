"""Exercise optional entry points through real HTTP and CLI calls."""
from pathlib import Path
import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from board import project,storage,note_schedule

ROOT=Path(__file__).resolve().parents[1]


class OptionalEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'data'
        project.initialize(self.root,'Example','Question','Report','Owner',False)

    def test_guest_projection_permissions_logout(self):
        from board.plugins import accounts,account_server
        cfg=accounts.initial_config();cfg['accounts']['owner']['password_hash']=accounts.password_hash('owner-password')
        cfg['accounts']['visitor']['password_hash']=accounts.password_hash('guest-password')
        path=self.root/'attachments/accounts.json';accounts.atomic_json(path,cfg)
        storage.write(self.root/'overview.json',dict(schedule=[],todo=[],private_field='private-canary',runs=[dict(secret='private-canary')]))
        server=account_server.create_server(self.root,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(thread.join,2);self.addCleanup(server.shutdown)
        port=server.server_port;origin=f'http://127.0.0.1:{port}'
        def request(method,path,value=None,cookie=''):
            connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
            headers={'Origin':origin,'Content-Type':'application/json','Cookie':cookie}
            connection.request(method,path,json.dumps(value) if value is not None else None,headers)
            response=connection.getresponse();raw=response.read();status=response.status;headers=dict(response.getheaders());connection.close()
            return status,raw,headers
        self.assertEqual(request('GET','/api/board')[0],401)
        status,raw,headers=request('POST','/api/login',dict(password='guest-password'))
        self.assertEqual(status,200);cookie=headers['Set-Cookie'].split(';')[0]
        status,raw,_=request('GET','/api/board',cookie=cookie)
        self.assertEqual(status,200);self.assertNotIn(b'private-canary',raw)
        self.assertEqual(request('GET','/api/private-notes',cookie=cookie)[0],403)
        self.assertEqual(request('POST','/api/discussion',dict(body='inject'),cookie)[0],403)
        before=(self.root/'overview.json').read_bytes()
        status,guest_html,_=request('GET','/',cookie=cookie)
        self.assertEqual(status,200)
        self.assertNotIn(b'Leave a note',guest_html)
        self.assertNotIn(b'/api/notes',guest_html)
        self.assertIn(b'Discussion',guest_html)
        self.assertEqual(request('POST','/api/notes',dict(what='A useful suggestion'),cookie)[0],403)
        self.assertEqual((self.root/'overview.json').read_bytes(),before)
        self.assertEqual(request('POST','/api/logout',{},cookie)[0],200)
        self.assertEqual(request('GET','/api/board',cookie=cookie)[0],401)

    def test_schedule_assignment_and_pending(self):
        from datetime import datetime,timedelta
        now=datetime.now().astimezone().replace(hour=12,minute=0,second=0,microsecond=0)
        value=dict(todo=[dict(what='Read source',by='Claude')],schedule=[])
        note_schedule.place(value,'n1',value['todo'][0],0,'op1',(now-timedelta(hours=1)).timestamp())
        storage.write(self.root/'overview.json',value)
        events=note_schedule.pending_events(self.root,now.timestamp())
        self.assertEqual(len(events),1);self.assertEqual(events[0]['note_id'],'n1')
        assigned=note_schedule.assign(self.root,'n1','14:00',today=now)
        self.assertEqual(assigned['time'],'14:00');self.assertEqual(note_schedule.pending_events(self.root,now.timestamp()),[])

    def test_shared_read_markers_and_read_only_preview(self):
        from board import app,tree_reads
        storage.write(self.root/'overview.json',dict(tree=[dict(id='stable',title='Before',page='result.md')]))
        payload=dict(title='Before',key='id:stable',version='v1',read=True)
        tree_reads.choose(self.root,'owner',payload)
        value=storage.read(self.root/'overview.json');value['tree'][0]['title']='After';storage.write(self.root/'overview.json',value)
        self.assertEqual(app.snapshot(self.root)['overview']['tree_reads']['versions']['id:stable'],'v1')
        tree_reads.choose(self.root,'owner',dict(payload,title='After',read=False))
        self.assertIsNone(tree_reads.snapshot(self.root)['versions']['id:stable'])
        server=app.create_server(self.root,0,read_only=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(thread.join,2);self.addCleanup(server.shutdown)
        def hashes():return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file() and p.suffix in {'.json','.md','.jsonl'}}
        before=hashes();c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        for path in ['/api/board','/api/schedule']:
            c.request('GET',path);r=c.getresponse();r.read();self.assertEqual(r.status,200)
        c.request('POST','/api/tree/read',json.dumps(payload),{'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json'});r=c.getresponse();r.read();self.assertEqual(r.status,403);c.close()
        self.assertEqual(before,hashes())

    def test_cli_disabled_observation_and_continuity(self):
        script=ROOT/'scripts/integrations.py'
        response=subprocess.run([sys.executable,str(script),'--data-dir',str(self.root),'watch'],capture_output=True,text=True)
        self.assertEqual(response.returncode,0,response.stderr);self.assertEqual(json.loads(response.stdout)['status'],'disabled')
        response=subprocess.run([sys.executable,str(script),'--data-dir',str(self.root),'current','--actor','GPT','--task','T001','--stage','implement'],capture_output=True,text=True)
        self.assertEqual(response.returncode,0,response.stderr)
        self.assertEqual(json.loads(response.stdout)['task'],'T001')

    def test_reply_mute_and_selected_avatar_http_identity(self):
        from datetime import datetime,timedelta,timezone
        from board import reply,app
        from board.plugins import asset_choices
        from PIL import Image
        text=self.root/'reply.md';text.write_text('A **clear result** with [details](https://example.org).','utf-8')
        result=reply.finish(self.root,'GPT',text,config=dict(enabled=True,mute_until=dict(GPT=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()),backend_command=['missing-backend']))
        self.assertEqual(result['playback'],'muted_by_preference')
        catalog=self.root/'attachments/avatar-catalog';catalog.mkdir(parents=True)
        Image.new('RGB',(16,16),'navy').save(catalog/'owned.png');storage.write(catalog/'catalog.json',[dict(id='owned',file='owned.png')])
        asset_choices.select(catalog,self.root/'attachments/avatar-choices','owner','owned',[0,0,16])
        entry=app.accounts(self.root)[0]
        self.assertEqual(entry['avatar']['file'],'generated/owner/avatar.png')


if __name__=='__main__':unittest.main()
