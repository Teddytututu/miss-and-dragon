"""Default artwork, optional emotes and release boundaries work together."""
from pathlib import Path
import http.client, io, json, runpy, tempfile, threading, unittest
from PIL import Image
from board import onboarding, storage
from board.app import create_server
from board.project import initialize, post

ROOT=Path(__file__).resolve().parents[1]


class PublicAssets(unittest.TestCase):
    def test_default_avatar_mood_emote_and_reaction_are_served(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work/tests') as folder:
            root=Path(folder)
            initialize(root,'Character board')
            message=post(root,'GPT','Ready')
            row={'key':'bili:123','file':'123.png'}
            path=root/'emotes'/row['file']
            path.parent.mkdir()
            image=io.BytesIO()
            Image.new('RGBA',(4,4),(30,80,120,255)).save(image,format='PNG')
            path.write_bytes(image.getvalue())
            storage.write(root/'emotes/manifest.json',[{'id':123,'label':'Local example'}])
            onboarding.configure_emotes(root,'download')
            server=create_server(root,port=0)
            worker=threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()

            def request(url,value=None):
                connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                headers={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{server.server_port}'}
                connection.request('GET' if value is None else 'POST',url,None if value is None else json.dumps(value),headers)
                response=connection.getresponse()
                result=response.status,response.read(),dict(response.getheaders())
                connection.close()
                return result

            try:
                _,raw,_=request('/api/accounts')
                self.assertEqual(next(x for x in json.loads(raw)['accounts'] if x['id']=='Claude')['avatar']['file'],'avatar-claude.svg')
                for url in ['/generated/Claude/calm','/art/avatar-claude.svg','/room-reactions/'+row['file']]:
                    code,raw,headers=request(url)
                    expected = 'image/png' if url.startswith('/room-reactions/') else 'image/svg+xml'
                    self.assertEqual((code,headers['Content-Type']),(200,expected))
                    self.assertTrue(raw.startswith(b'\x89PNG') if expected=='image/png' else b'<svg' in raw)
                code,raw,_=request('/api/reaction',dict(message_id=message['id'],emoji=row['key'],active=True))
                self.assertEqual(code,200)
                self.assertEqual(json.loads(raw)['reactions'][0]['emoji'],row['key'])
                _,raw,_=request('/api/discussion')
                self.assertEqual(json.loads(raw)['reaction_catalog'][0]['key'],row['key'])
                onboarding.configure_emotes(root,'unicode')
                self.assertTrue(path.exists())
                self.assertEqual(request('/room-reactions/123.png')[0],404)
                self.assertNotEqual(request('/api/reaction',dict(message_id=message['id'],emoji=row['key'],active=True))[0],200)
                _,raw,_=request('/api/discussion')
                self.assertEqual(json.loads(raw)['items'][0]['reactions'][0]['emoji'],row['key'])
                self.assertEqual(request('/api/reaction',dict(message_id=message['id'],emoji=row['key'],active=False))[0],200)
                _,raw,_=request('/api/discussion')
                self.assertEqual(json.loads(raw)['reaction_catalog'],[])
                self.assertIn('👍',json.loads(raw)['reaction_emoji'])
            finally:
                server.shutdown()
                server.server_close()
                worker.join()

    def test_public_manifest_and_archive_keep_media_scopes(self):
        release=runpy.run_path(str(ROOT/'scripts/release.py'))
        names=release['files']()
        self.assertEqual(sum(x.startswith('board/art/') and x.endswith('.png') for x in names),0)
        self.assertTrue(all(not x.startswith('data/') for x in names))
        self.assertNotIn('assets/public-emotes.json',names)
        self.assertNotIn('scripts/install_emotes.py',names)
        self.assertIn('docs/local-emotes.md',names)
        self.assertIn('private_media_reference',release['scan'](b'/chat-img/'+b'a'*32+b'.png','assets/public-emotes.json'))


if __name__=='__main__':
    unittest.main()
