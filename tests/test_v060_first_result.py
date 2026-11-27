"""A fresh reader reaches an adopted result, and later revisions cannot masquerade as it."""
from pathlib import Path
import hashlib
import http.client
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

from board import lifecycle, manual_packets, paired_report, report_reader, storage

ROOT = Path(__file__).resolve().parents[1]


class FirstResult(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / 'study with spaces 中文'
        result = self.command('demo_research.py', '--data-dir', str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.result = json.loads(result.stdout)
        self.packet = self.root / 'attachments/manual-packets/cache-pilot'

    def command(self, script, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / script), *args],
                              cwd=self.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)

    def hashes(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}

    def revised(self, data='batch,baseline_seconds,cache_seconds\nA,4,1\nB,5,3\n'):
        path = self.parent / 'revised.csv'
        path.write_text(data, encoding='utf-8')
        result = manual_packets.paste(self.packet, 'Revised paired measurements', [path])
        row = result['answer_versions'][-1]
        manual_packets.review(self.packet, row['id'], 'partial', 'Adopt measured timing; memory remains open', task='T002', adopted_files=row['files'])
        return row

    def test_first_result_contains_real_task_review_history_and_csv_totals(self):
        self.assertEqual((self.result['baseline_seconds'], self.result['cached_seconds']), (5, 3))
        self.assertEqual((self.result['answer_versions'], self.result['report_check']), (2, 'current'))
        self.assertEqual(self.result['model_calls'], 0)
        events = storage.lines(self.root / 'attachments/task-flow.jsonl')
        self.assertEqual([r['action'] for r in events if r['task'] == 'T001'],
                         ['new', 'start', 'deliver', 'reject', 'start', 'deliver', 'accept'])
        self.assertEqual([r['task'] for r in lifecycle.parse_board((self.root / 'board.md').read_text('utf-8'))], ['T002'])
        self.assertTrue((self.root / 'tasks/T002-memory.md').is_file())
        self.assertEqual([r['task'] for r in lifecycle.parse_board((self.root / 'tasks/archive.md').read_text('utf-8'))], ['T001'])
        before = self.hashes()
        self.assertTrue(paired_report.check(self.root)['ok'])
        self.assertEqual(before, self.hashes())

    def test_repeat_and_file_path_fail_without_overwriting_the_first_result(self):
        before = self.hashes()
        result = self.command('demo_research.py', '--data-dir', str(self.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn('empty directory', json.loads(result.stderr)['error'])
        self.assertEqual(before, self.hashes())
        target = self.parent / 'keep.txt'
        target.write_text('keep', encoding='utf-8')
        result = self.command('demo_research.py', '--data-dir', str(target))
        self.assertEqual(result.returncode, 2)
        self.assertIn('path is a file', json.loads(result.stderr)['error'])
        self.assertEqual(target.read_text('utf-8'), 'keep')

    def test_changed_measurements_and_rollback_use_the_selected_version(self):
        original = manual_packets.snapshot(self.packet)['adopted_answer']
        revised = self.revised()
        self.assertFalse(paired_report.check(self.root)['ok'])
        changed = paired_report.build(self.root)
        self.assertEqual((changed['baseline_seconds'], changed['cached_seconds']), (9, 4))
        self.assertIn('9 to 4 seconds', (self.root / changed['report']).read_text('utf-8'))
        node = storage.read(self.root / 'overview.json')['tree'][0]
        self.assertEqual(node['report_answer'], revised['id'])
        self.assertIn('9 seconds baseline and 4 seconds cached', node['summary'])
        manual_packets.review(self.packet, original, 'partial', 'Restore the original paired timing table', task='T002', adopted_files=['result-v2.csv'])
        self.assertFalse(paired_report.check(self.root)['ok'])
        restored = paired_report.build(self.root)
        self.assertEqual(restored['report_answer'], original)
        self.assertEqual((restored['baseline_seconds'], restored['cached_seconds']), (5, 3))
        self.assertTrue((self.packet / revised['files'][0]).is_file())

    def test_review_scope_changes_and_rejection_invalidate_the_current_label(self):
        selected = manual_packets.snapshot(self.packet)['adopted_answer']
        manual_packets.review(self.packet, selected, 'accepted', 'Only use batch A in the follow-up')
        status = paired_report.check(self.root)
        self.assertFalse(status['ok'])
        self.assertIn('scope', ' '.join(status['problems']))
        manual_packets.review(self.packet, selected, 'rejected', 'Withdraw this timing answer')
        self.assertFalse(paired_report.check(self.root)['ok'])
        with self.assertRaisesRegex(ValueError, 'adopt'):
            paired_report.build(self.root)

    def test_bad_units_wrong_batches_and_nonfinite_values_preserve_the_previous_report(self):
        for data, expected in [
            ('batch,baseline_ms,cache_seconds\nA,2000,1\nB,3000,2\n', 'columns'),
            ('batch,baseline_seconds,cache_seconds\nA,2,1\nC,3,2\n', 'original input batches'),
            ('batch,baseline_seconds,cache_seconds\nA,NaN,1\nB,3,2\n', 'finite'),
            ('batch,baseline_seconds,cache_seconds\nA,2,1\nA,3,2\n', 'distinct batch'),
        ]:
            with self.subTest(expected=expected):
                self.revised(data)
                before = (self.root / 'reports/cache-pilot.html').read_bytes()
                with self.assertRaisesRegex(ValueError, expected):
                    paired_report.build(self.root)
                self.assertEqual((self.root / 'reports/cache-pilot.html').read_bytes(), before)

    def test_moving_project_keeps_relative_report_and_packet_bindings(self):
        moved = self.parent / 'moved project 中文'
        shutil.move(self.root, moved)
        self.root = moved
        self.packet = moved / 'attachments/manual-packets/cache-pilot'
        result = self.command('research_report.py', '--data-dir', str(moved), 'check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['report'], 'reports/cache-pilot.html')

    def test_legacy_review_remains_readable_but_needs_explicit_binding_before_reporting(self):
        meta = storage.read(self.packet / 'meta.json')
        selected = next(row for row in meta['answer_versions'] if row['id'] == meta['adopted_answer'])
        selected['review'].pop('artifacts')
        selected['review'].pop('inputs')
        storage.write(self.packet / 'meta.json', meta)
        self.assertEqual(manual_packets.adopted(self.packet)['id'], selected['id'])
        before = self.hashes()
        with self.assertRaisesRegex(ValueError, 'legacy answer'):
            paired_report.build(self.root)
        with self.assertRaisesRegex(ValueError, 'legacy answer'):
            paired_report.check(self.root)
        self.assertEqual(before, self.hashes())
        manual_packets.review(self.packet, selected['id'], 'partial', 'Reviewed original paired timing',
                              adopted_files=selected['files'])
        self.assertTrue(paired_report.build(self.root)['ok'])

    def test_different_report_file_with_the_same_stem_cannot_inherit_current_status(self):
        alternate = self.root / 'reports/cache-pilot.htm'
        alternate.write_bytes((self.root / 'reports/cache-pilot.html').read_bytes())
        self.revised()
        paired_report.build(self.root)
        before = self.hashes()
        notice = paired_report.reader_notice(self.root, alternate)
        self.assertIn('Historical snapshot', notice)
        self.assertNotIn('matches the currently adopted answer', notice)
        self.assertIn('5 to 3 seconds', alternate.read_text('utf-8'))
        self.assertEqual(before, self.hashes())

    def test_reader_exposes_stale_adoption_without_writing_to_disk(self):
        from board.app import create_server
        self.revised()
        (self.root / '.write.lock').unlink()
        before = self.hashes()
        server = create_server(self.root, 0, read_only=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            connection.request('GET', '/api/board')
            projected = connection.getresponse()
            projected.read()
            self.assertEqual(projected.status, 200)
            connection.request('GET', report_reader.report_url('reports/cache-pilot.html'))
            response = connection.getresponse()
            content = response.read().decode('utf-8')
            connection.close()
            self.assertEqual(response.status, 200)
            self.assertIn('Historical snapshot', content)
            self.assertIn('5 to 3 seconds', content)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(before, self.hashes())


if __name__ == '__main__':
    unittest.main()
