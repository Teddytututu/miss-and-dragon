"""Exercise reports from changed inputs, including invalid and escaped data."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import demo_research
import demo_manual_packet


class ReportDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        shutil.copytree(ROOT / 'demo', self.source / 'demo')
        for module in (demo_research, demo_manual_packet):
            patcher = patch.object(module, 'ROOT', self.source)
            patcher.start()
            self.addCleanup(patcher.stop)

    def generate(self, rows, name='result'):
        raw = ('batch,baseline_seconds,cache_seconds\r\n' + rows).encode('utf-8-sig')
        (self.source / 'demo/manual-packet/result-v2.csv').write_bytes(raw)
        output = self.base / name
        return demo_research.run(output), output, raw

    def test_changed_csv_updates_report_overview_and_download(self):
        result, output, raw = self.generate('A,4,1\r\nB,5,3\r\n')
        report = (output / 'reports/cache-pilot.html').read_text('utf-8')
        overview = json.loads((output / 'overview.json').read_text('utf-8'))
        self.assertEqual((result['baseline_seconds'], result['cached_seconds']), (9, 4))
        self.assertIn('from 9 to 4 seconds', report)
        self.assertIn('Baseline 9 seconds, cached 4 seconds', report)
        self.assertIn('<td>A</td><td>4</td><td>1</td>', report)
        self.assertIn('9 seconds baseline and 4 seconds cached', overview['tree'][0]['summary'])
        self.assertEqual((output / 'reports/paired.csv').read_bytes(), raw)
        self.assertEqual((result['model_calls'], result['answer_versions']), (0, 2))

    def test_slower_equal_and_zero_results_use_accurate_language(self):
        for i, (rows, description) in enumerate([
            ('A,1,4\nB,1,3\n', 'increased the paired time from 2 to 7 seconds'),
            ('A,1,1\nB,1,1\n', 'kept the paired time at 2 seconds'),
            ('A,0,0\nB,0,0\n', 'kept the paired time at 0 seconds'),
        ]):
            with self.subTest(description=description):
                _, output, _ = self.generate(rows, str(i))
                report = (output / 'reports/cache-pilot.html').read_text('utf-8')
                self.assertIn(description, report)
                self.assertNotIn('nan', report.lower())
                self.assertNotIn('inf', report.lower())

    def test_invalid_measurements_leave_destination_empty(self):
        for i, rows in enumerate([
            'A,nan,1\nB,3,2\n', 'A,inf,1\nB,3,2\n',
            'A,-1,1\nB,3,2\n', 'A,2,1\nA,3,2\n',
            'A,2,1\n', 'A,2,1\nC,3,2\n',
            'A,1e308,1\nB,1e308,2\n', 'A,2,1,extra\nB,3,2\n',
        ]):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    self.generate(rows, str(i))
                output = self.base / str(i)
                self.assertFalse(output.exists() and any(output.iterdir()))

    def test_batch_names_are_html_escaped(self):
        (self.source / 'demo/manual-packet/inputs.csv').write_text('batch,items\n<img>,10\nB,20\n', encoding='utf-8')
        _, output, _ = self.generate('<img>,2,1\nB,3,2\n')
        report = (output / 'reports/cache-pilot.html').read_text('utf-8')
        self.assertIn('<td>&lt;img&gt;</td>', report)
        self.assertNotIn('<td><img>', report)


if __name__ == '__main__':
    unittest.main()
