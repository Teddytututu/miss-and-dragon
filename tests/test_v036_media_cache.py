"""Private avatar caching through the HTTP entry point."""
from pathlib import Path
import http.client
import tempfile
import threading
import unittest
from board.project import initialize
from board.app import create_server

class MediaCache(unittest.TestCase):
    def test_private_cache_revalidation_and_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            initialize(root,'Media example')
            path=root/'attachments/generated/Claude/avatar.svg'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
            server=create_server(root,port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            def request(url,headers=None):
                connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                connection.request('GET',url,headers=headers or {})
                response=connection.getresponse()
                result=response.status,response.read(),dict(response.getheaders())
                connection.close()
                return result
            try:
                status,body,headers=request('/generated/Claude/avatar.svg')
                self.assertEqual(status,200)
                self.assertEqual(headers['Cache-Control'],'private, max-age=60')
                self.assertIn('sandbox',headers['Content-Security-Policy'])
                etag=headers['ETag']
                status,body,headers=request('/generated/Claude/avatar.svg',{'If-None-Match':etag})
                self.assertEqual((status,body),(304,b''))
                path.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"><title>Updated</title></svg>')
                status,body,headers=request('/generated/Claude/avatar.svg',{'If-None-Match':etag})
                self.assertEqual(status,200)
                self.assertNotEqual(headers['ETag'],etag)
                self.assertIn(b'Updated',body)
                for url in ['/api/board','/api/discussion']:
                    self.assertEqual(request(url)[2]['Cache-Control'],'no-store, private')
                self.assertEqual(request('/art/avatar-user.png')[2]['Cache-Control'],'private, max-age=60')
            finally:
                server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
