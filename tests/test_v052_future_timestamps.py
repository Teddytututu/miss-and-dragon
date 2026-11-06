from datetime import datetime, timedelta
from pathlib import Path
import os
import tempfile
import unittest

from board import lifecycle, project, workflow_checks


class FutureTimestamps(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        project.initialize(self.root, 'Example', 'Compare methods', 'Report')
        self.now = datetime(2030, 1, 2, 12, tzinfo=lifecycle.TAIPEI)

    def write(self, relative, text, age=0):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        stamp = (self.now - timedelta(hours=age)).timestamp()
        os.utime(path, (stamp, stamp))
        return path

    def issues(self, links=()):
        return workflow_checks.timestamp_issues(self.root, self.now, {'links': list(links)})

    def test_explicit_date_and_three_minute_boundary(self):
        self.write('tasks/T001-example.md', 'Claude 2030-01-02 12:03')
        self.assertEqual(self.issues(), [])
        self.write('tasks/T001-example.md', 'Claude 2030-01-02 12:04')
        self.assertEqual(self.issues()[0]['task'], 'T001')

    def test_time_only_hour_boundary(self):
        self.write('experiment-design/E001-example.md', 'Claude 12:59')
        self.assertEqual(len(self.issues()), 1)
        self.write('experiment-design/E001-example.md', 'Claude 13:00')
        self.assertEqual(self.issues(), [])

    def test_due_dates_transitions_invalid_dates_and_old_files(self):
        for text in ('Claude 预计 2030-01-02 12:30',
                     'Claude expected 2030-01-02 12:30',
                     '- 2030-01-02 12:30 HKT · Claude 12:30',
                     'Claude 2030-02-30 12:30'):
            self.write('tasks/T001-example.md', text)
            self.assertEqual(self.issues(), [], text)
        self.write('tasks/T001-example.md', 'Claude 2030-01-02 12:30', age=49)
        self.assertEqual(self.issues(), [])

    def test_only_registered_local_html_and_five_minute_boundary(self):
        self.write('attachments/listed.html', 'Claude 2030-01-02 12:05')
        self.write('attachments/other.html', 'Claude 2030-01-02 12:30')
        link = {'path': 'attachments/listed.html'}
        self.assertEqual(self.issues([link]), [])
        self.write('attachments/listed.html', 'Claude 2030-01-02 12:06')
        self.assertEqual(len(self.issues([link])), 1)
        self.assertEqual(self.issues([dict(link, archived=True),
                                      {'path': 'https://example.com/a.html'},
                                      {'path': '../outside.html'}]), [])

    def test_check_includes_timestamp_issue(self):
        self.write('tasks/T001-example.md', 'Claude 2030-01-02 12:04')
        result = lifecycle.check(self.root, now=self.now)
        self.assertIn('future_timestamp', [item['code'] for item in result])
