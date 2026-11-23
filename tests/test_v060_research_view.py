"""Optional features exercise the real HTTP and snapshot boundary."""
from pathlib import Path
import hashlib, http.client, json, tempfile, threading, unittest
from board import project, manual_packets, storage
from board.app import create_server

ROOT=Path(__file__).resolve().parents[1]


class ResearchView(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work/tests');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);project.initialize(self.root,'Fictional cache study')
        self.packet=self.root/'attachments/manual-packets/example'
        manual_packets.create(self.packet,'Cache study','Compare the same two batches')
        a=manual_packets.paste(self.packet,'First answer')
        manual_packets.review(self.packet,a['answer_versions'][0]['id'],'rejected','Repeat with paired inputs')
        b=manual_packets.paste(self.packet,'Second answer')
        manual_packets.review(self.packet,b['answer_versions'][1]['id'],'partial','Adopt the timing table',task='T002')
        storage.write(self.root/'attachments/resource-plan.json',dict(cards=1,jobs=[
            dict(id='one',title='First',unit='batch',measurement=dict(unit='batch',seconds=7200,units=1)),
            dict(id='two',title='Second',unit='batch',measurement=dict(unit='batch',seconds=10800,units=1))]))
        self.server=create_server(self.root,0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def get(self,url):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10);c.request('GET',url);r=c.getresponse();value=r.status,r.read();c.close();return value

    def files(self):
        return {p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}

    def test_board_reads_same_plan_and_two_version_history_without_writes(self):
        before=self.files();code,raw=self.get('/api/board');self.assertEqual(code,200)
        overview=json.loads(raw)['overview'];plan=overview['resource_plan']
        self.assertEqual(plan['remaining_card_hours'],5)
        self.assertEqual(len(plan['jobs']),2)
        packets=overview['manual_packets'];self.assertEqual(len(packets[0]['answer_versions']),2)
        self.assertEqual(packets[0]['answer_versions'][0]['review']['decision'],'rejected')
        self.assertEqual(packets[0]['answer_versions'][1]['review']['decision'],'partial')
        self.assertEqual(self.files(),before)

    def test_packet_files_are_explicitly_registered_and_path_scoped(self):
        code,raw=self.get('/manual-packets/example/ask.md');self.assertEqual(code,200);self.assertIn(b'Compare',raw)
        secret=self.root/'attachments/private/secret.md';storage.write_bytes(secret,b'private fixture')
        for url in ['/manual-packets/example/meta.json','/manual-packets/example/../../private/secret.md','/files/attachments/private/secret.md','/manual-packets/example/%2e%2e%2fmeta.json']:
            self.assertIn(self.get(url)[0],(400,403,404))

    def test_malformed_optional_files_leave_the_main_board_readable(self):
        storage.write(self.root/'attachments/resource-plan.json',dict(cards=4))
        storage.write(self.packet/'meta.json',dict(answer_versions=[{}]))
        code,raw=self.get('/api/board');self.assertEqual(code,200)
        data=json.loads(raw);self.assertIn('tasks',data)
        self.assertEqual(len(data['overview']['research_issues']),2)


if __name__=='__main__':unittest.main()
