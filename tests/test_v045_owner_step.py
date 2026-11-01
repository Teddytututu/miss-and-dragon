from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from board import storage, project
from board.lifecycle import transition, check


class OwnerStep(unittest.TestCase):
    """Acceptance says whether the owner still has a step; owner-facing waits stay visible."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project.initialize(self.root, 'Example', 'Compare methods', 'Report')
        (self.root / 'tasks').mkdir()
        (self.root / 'tasks/T001-example.md').write_text('# Example\n\nGoal.\n', encoding='utf-8')
        storage.write(self.root / 'overview.json', {'tree': [{'title': 'Study', 'status': 'todo', 'tasks': []}]})
        self.now = datetime(2030, 1, 2, 12, tzinfo=timezone.utc)
        capacity = patch('board.stability.disk_summary', return_value=[])
        capacity.start()
        self.addCleanup(capacity.stop)

    def move(self, action, by='GPT', **kw):
        return transition(self.root, action, 'T001', by=by, now=self.now, **kw)

    def delivered(self):
        self.move('new', 'Claude', title='Example', when='Inputs ready', node='Study')
        self.move('start', status='0/1 · 估不了：fixture')
        (self.root / 'attachments').mkdir(exist_ok=True)
        (self.root / 'attachments/e.md').write_text('done\n', encoding='utf-8')
        self.move('deliver', evidence='attachments/e.md')

    def todos(self):
        return storage.read(self.root / 'overview.json', {}).get('todo', [])

    def test_accept_requires_owner_step(self):
        self.delivered()
        with self.assertRaisesRegex(ValueError, 'owner-step'):
            self.move('accept', 'Claude', summary='Ready')

    def test_owner_step_becomes_todo_and_none_adds_nothing(self):
        self.delivered()
        before = len(self.todos())
        self.move('accept', 'Claude', summary='Ready', owner_step='Approve the preview')
        added = [t for t in self.todos() if t.get('what') == 'Approve the preview']
        self.assertEqual(len(added), 1)
        self.assertIn('T001', added[0]['note'])
        self.assertEqual(len(self.todos()), before + 1)

    def test_none_adds_no_todo(self):
        self.delivered()
        before = len(self.todos())
        self.move('accept', 'Claude', summary='Ready', owner_step='none')
        self.assertEqual(len(self.todos()), before)

    def test_waiting_on_owner_without_todo_is_reported(self):
        self.move('new', 'Claude', title='Example', when='Inputs ready', node='Study')
        self.move('block', wait='等你 提供下载链接')
        codes = [i['code'] for i in check(self.root, now=self.now)]
        self.assertIn('owner_step_hidden', codes)
        overview = storage.read(self.root / 'overview.json', {})
        overview['todo'] = [dict(what='Send the link', note='T001 needs it')]
        storage.write(self.root / 'overview.json', overview)
        codes = [i['code'] for i in check(self.root, now=self.now)]
        self.assertNotIn('owner_step_hidden', codes)


if __name__ == '__main__':
    unittest.main()
