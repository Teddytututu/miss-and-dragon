"""A browser's parallel assets fit in the local listener's pending queue."""
import socket
import unittest
from http.server import BaseHTTPRequestHandler
from board.app import BoardHTTPServer

class BrowserConnectionBurst(unittest.TestCase):
    def test_parallel_initial_connections_are_accepted(self):
        server=BoardHTTPServer(('127.0.0.1',0),BaseHTTPRequestHandler)
        clients=[]
        try:
            for _ in range(24):
                clients.append(socket.create_connection(server.server_address,timeout=.5))
            self.assertEqual(len(clients),24)
        finally:
            for client in clients:client.close()
            server.server_close()

if __name__=='__main__':unittest.main()
