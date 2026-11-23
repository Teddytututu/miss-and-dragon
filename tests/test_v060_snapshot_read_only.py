from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from board import app, note_schedule, plan_checks, project, storage


class SnapshotReadOnly(unittest.TestCase):
    def test_completed_yesterday_stays_complete_and_browsing_preserves_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project.initialize(root, 'Fictional reading example')
            yesterday = note_schedule.today_date() - timedelta(days=1)
            day = dict(date=yesterday.isoformat(), items=[dict(
                id='note:example', what='Read the sample report', checkable=True,
                scheduled_from_note=dict(id='example', date=yesterday.isoformat(), index=0,
                                         placed_at=yesterday.isoformat(), note=dict(what='Read the sample report')))])
            storage.write(root/'overview.json', dict(schedule=[day], todo=[]))
            key = plan_checks.project([day], today=yesterday)[0]['items'][0]['check_id']
            storage.write(root/'attachments/plan-checks.json', dict(items={key: dict(completed=True)}))
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            value = app.snapshot(root)
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)
            self.assertTrue(value['overview']['schedule'][0]['items'][0]['completed'])
            self.assertEqual(app.snapshot(root)['overview']['schedule'], value['overview']['schedule'])


if __name__ == '__main__':
    unittest.main()
