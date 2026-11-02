import http.client
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import quote

from board import project, storage
from board.app import create_server


class ReportReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'data'
        project.initialize(self.root, 'Example')
        self.report = self.root / 'reports' / 'Result.html'
        self.report.parent.mkdir()
        self.report.write_text('<h1>Result</h1><a href="table.csv">Data</a>', encoding='utf-8')
        (self.report.parent / 'table.csv').write_bytes(b'a,b\n1,2\n')
        storage.write(self.root / 'overview.json', {'links': [{'title': 'Result', 'path': 'reports/Result.html'}]})
        self.server = create_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, path, method='GET', headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        c.request(method, path, headers=headers or {})
        response = c.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        c.close()
        return result

    def url(self, path=None):
        from board import report_reader
        return report_reader.report_url(path or 'reports/Result.html')

    def test_html_and_exact_attachment_with_duplicate_basename(self):
        other = self.root / 'other'
        other.mkdir()
        (other / 'table.csv').write_bytes(b'wrong')
        status, headers, body = self.request(self.url())
        self.assertEqual(status, 200)
        self.assertTrue(headers['Content-Type'].startswith('text/html'))
        link = re.search(rb'href="([^"]+)"', body)[1].decode()
        self.assertEqual(self.request(link)[2], b'a,b\n1,2\n')
        self.assertEqual(self.request(link, 'HEAD')[2], b'')
        self.assertEqual(headers['Cache-Control'], 'no-store, private')
        _, _, snapshot = self.request('/api/board')
        self.assertEqual(json.loads(snapshot)['overview']['links'][0]['reader_url'], self.url())
        self.assertIn("script-src 'none'", headers['Content-Security-Policy'])

    def test_markdown_escapes_markup_and_preserves_download(self):
        md = self.root / 'reports' / 'Notes.md'
        md.write_text('# Notes\n\n<script>alert(1)</script>\n\n[Data](table.csv)\n\n[Bad](javascript:alert)\n', encoding='utf-8')
        storage.write(self.root / 'overview.json', {'links': [{'path': 'reports/Notes.md'}]})
        status, _, body = self.request(self.url('reports/Notes.md'))
        self.assertEqual(status, 200)
        self.assertIn(b'<h1>Notes</h1>', body)
        self.assertIn(b'&lt;script&gt;', body)
        self.assertNotIn(b'href="javascript:', body)
        self.assertIn(b'_asset/', body)
        self.assertEqual(self.request('/files/reports/Notes.md')[2], md.read_bytes())

    def test_unlinked_private_external_and_traversal_stay_outside_scope(self):
        (self.root / 'secret.txt').write_text('secret', encoding='utf-8')
        private = self.root / 'attachments' / 'private'
        private.mkdir(parents=True, exist_ok=True)
        (private / 'note.txt').write_text('private', encoding='utf-8')
        outside = self.root.parent / 'outside.txt'
        outside.write_text('outside', encoding='utf-8')
        self.report.write_text('<a href="../attachments/private/note.txt">private</a><a href="../../outside.txt">outside</a>', encoding='utf-8')
        body = self.request(self.url())[2]
        self.assertNotIn(b'_asset/', body)
        for suffix in ['../secret.txt', '%2e%2e/secret.txt', 'secret.txt', '_asset/' + '0'*24 + '/note.txt']:
            self.assertEqual(self.request(self.url().rsplit('/', 1)[0] + '/' + suffix)[0], 404)
        storage.write(self.root / 'overview.json', {'links': [{'path': 'attachments/private/note.txt'}, {'path': str(outside)}]})
        self.assertEqual(self.request(self.url('attachments/private/note.txt'))[0], 404)
        self.assertEqual(self.request(self.url(str(outside)))[0], 404)

    def test_referenced_css_and_cross_report_navigation(self):
        style = self.report.parent / 'style.css'
        style.write_text('body{background:url("chart.svg")}', encoding='utf-8')
        (self.report.parent / 'chart.svg').write_text('<svg/>', encoding='utf-8')
        second = self.report.parent / 'Second.html'
        second.write_text('<a href="unshared.txt">other</a>', encoding='utf-8')
        (self.report.parent / 'unshared.txt').write_text('second-only', encoding='utf-8')
        self.report.write_text('<link href="style.css"><a href="Second.html#part">Next</a>', encoding='utf-8')
        storage.write(self.root / 'overview.json', {'links': [{'path': 'reports/Result.html'}, {'path': 'reports/Second.html'}]})
        body = self.request(self.url())[2].decode()
        self.assertIn(self.url('reports/Second.html') + '#part', body)
        css_url = re.search(r'href="([^"]+)"', body)[1]
        css = self.request(css_url)[2].decode()
        image_url = re.search(r'url\("([^"]+)"\)', css)[1]
        self.assertEqual(self.request(image_url)[2], b'<svg/>')
        from board import report_reader
        allowed = report_reader.allowed_assets(self.root, self.report)
        self.assertNotIn(self.report.parent / 'unshared.txt', allowed)

    def test_live_references_and_methods_and_loopback_guard(self):
        self.request(self.url())
        self.report.write_text('<a href="new.csv">New</a>', encoding='utf-8')
        (self.report.parent / 'new.csv').write_bytes(b'new')
        body = self.request(self.url())[2]
        link = re.search(rb'href="([^"]+)"', body)[1].decode()
        self.assertEqual(self.request(link)[2], b'new')
        status, headers, _ = self.request(self.url(), 'POST', {'Origin': f'http://127.0.0.1:{self.server.server_port}'})
        self.assertEqual(status, 405)
        self.assertEqual(headers['Allow'], 'GET, HEAD')
        self.assertEqual(self.request(self.url(), headers={'Host': 'example.com'})[0], 403)

    def test_unicode_names_fragments_and_private_aliases(self):
        name = '图 表.csv'
        (self.report.parent / name).write_bytes(b'unicode')
        private = self.root / 'attachments' / 'private'
        private.mkdir(parents=True, exist_ok=True)
        (private / 'note.txt').write_text('private', encoding='utf-8')
        self.report.write_text('<a href="' + quote(name) + '?download=1#row">Table</a><a href="../attachments/private/note.txt">private</a>', encoding='utf-8')
        body = self.request(self.url())[2].decode()
        link = re.search(r'href="([^"]+)"', body)[1]
        self.assertTrue(link.endswith('?download=1#row'))
        self.assertEqual(self.request(link.split('#')[0])[2], b'unicode')
        from board import report_reader
        self.assertFalse(report_reader.eligible(self.root, self.report.parent / '../attachments/private/note.txt'))
        self.assertFalse(report_reader.eligible(self.root, self.root / 'Attachments' / 'Private' / 'note.txt'))
        self.assertNotIn((private / 'note.txt').resolve(), report_reader.allowed_assets(self.root, self.report))

    def test_symbolic_link_reference_is_excluded(self):
        target = self.report.parent / 'table.csv'
        alias = self.report.parent / 'alias.csv'
        try:
            alias.symlink_to(target)
        except OSError:
            self.skipTest('Symbolic link creation requires the host capability')
        self.report.write_text('<a href="alias.csv">Alias</a>', encoding='utf-8')
        self.assertNotIn(b'_asset/', self.request(self.url())[2])

    def test_markdown_attribute_and_scheme_escaping(self):
        from board.md_render import render
        from board.report_reader import eligible
        text = render('![a" onerror="alert](x.png)\n\n<iframe src=x>', 'Notes')
        self.assertIn('&quot;', text)
        self.assertNotIn('<iframe', text)
        self.assertFalse(eligible(self.root, self.root / '../outside.txt'))


if __name__ == '__main__':
    unittest.main()
