"""Early rejection returns a readable response with delayed request bodies."""
import http.client
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from board import project
from board.app import create_server


class RejectedRequests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        project.initialize(self.root,'Rejected request test')
        self.server=create_server(self.root,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def request(self,length,body=b'',extra=''):
        sock=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=3)
        self.addCleanup(sock.close)
        headers=(f'POST /api/plan/check HTTP/1.0\r\nHost: 127.0.0.1:{self.server.server_port}\r\n'
                 f'Origin: https://elsewhere.invalid\r\nContent-Length: {length}\r\n'
                 f'Content-Type: application/json\r\n{extra}\r\n')
        sock.sendall(headers.encode())
        if body:
            time.sleep(0.02)
            sock.sendall(body)
        response=http.client.HTTPResponse(sock);response.begin()
        self.assertEqual(response.status,403)
        self.assertIn('error',json.loads(response.read()))

    def test_delayed_body_keeps_forbidden_response_readable(self):
        for _ in range(12):self.request(2,b'{}')
        self.assertFalse((self.root/'attachments/plan-checks.json').exists())

    def test_absent_body_has_bounded_wait(self):
        started=time.monotonic();self.request(2)
        self.assertLess(time.monotonic()-started,2)

    def test_trickled_body_has_total_wait_limit(self):
        sock=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=3)
        self.addCleanup(sock.close)
        stopped=threading.Event()
        headers=(f'POST /api/plan/check HTTP/1.0\r\nHost: 127.0.0.1:{self.server.server_port}\r\n'
                 'Origin: https://elsewhere.invalid\r\nContent-Length: 100\r\n\r\n')
        def trickle():
            for _ in range(20):
                try:sock.sendall(b'x')
                except OSError:return
                if stopped.wait(0.08):return
        started=time.monotonic()
        sock.sendall(headers.encode())
        sender=threading.Thread(target=trickle,daemon=True);sender.start()
        try:
            response=http.client.HTTPResponse(sock);response.begin()
            self.assertEqual(response.status,403)
            self.assertIn('error',json.loads(response.read()))
            self.assertLess(time.monotonic()-started,1)
        finally:
            stopped.set();sender.join(timeout=1)

    def test_large_and_ambiguous_lengths_are_rejected_promptly(self):
        for size,extra in [('100001',''),('2','Content-Length: 2\r\n'),('2','Transfer-Encoding: chunked\r\n')]:
            started=time.monotonic();self.request(size,extra=extra)
            self.assertLess(time.monotonic()-started,2)


if __name__=='__main__':unittest.main()
