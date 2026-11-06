from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from board import lifecycle, project


class ExperimentRecord(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        project.initialize(self.root, 'Example', 'Compare methods', 'Report')
        (self.root / 'tasks').mkdir()
        self.spec = self.root / 'tasks/T001-example.md'
        self.spec.write_text('# Example\n', encoding='utf-8')
        self.now = datetime(2030, 1, 2, 12, tzinfo=timezone.utc)
        self.move('new', by='Claude', title='Example', when='Ready')
        self.move('start', status='0/2 · 约 18:00')
        (self.root / 'attachments/evidence.md').write_text('Results\n', encoding='utf-8')

    def move(self, action, by='GPT', **fields):
        return lifecycle.transition(self.root, action, 'T001', by=by, now=self.now, **fields)

    def record(self, sections):
        folder = self.root / 'attachments/T001'
        folder.mkdir(exist_ok=True)
        (folder / 'experiment-record.md').write_text(
            '\n'.join(f'## {i}. Section\nResults\n' for i in sections), encoding='utf-8')

    def test_execution_spec_requires_record_and_each_numbered_section(self):
        for marker in ('Execution spec: experiment-design/E001-example.md',
                       '执行规格：实验设计/E001-example.md'):
            with self.subTest(marker=marker):
                self.spec.write_text('# Example\n' + marker + '\n', encoding='utf-8')
                record = self.root / 'attachments/T001/experiment-record.md'
                record.unlink(missing_ok=True)
                before = (self.root / 'board.md').read_bytes()
                with self.assertRaisesRegex(ValueError, 'experiment-record'):
                    self.move('deliver', evidence='attachments/evidence.md')
                for missing in range(1, 10):
                    self.record(i for i in range(1, 10) if i != missing)
                    with self.assertRaisesRegex(ValueError, 'section'):
                        self.move('deliver', evidence='attachments/evidence.md')
                self.assertEqual((self.root / 'board.md').read_bytes(), before)

    def test_complete_record_allows_delivery(self):
        self.spec.write_text('# Example\nExecution spec: experiment-design/E001-example.md\n', encoding='utf-8')
        self.record(range(1, 10))
        self.move('deliver', evidence='attachments/evidence.md')
        self.assertEqual(lifecycle.state_of(lifecycle.parse_board(
            (self.root / 'board.md').read_text('utf-8'))[0]['status']), 'delivered')

    def test_ordinary_task_uses_existing_evidence(self):
        self.move('deliver', evidence='attachments/evidence.md')
        self.assertEqual(lifecycle.state_of(lifecycle.parse_board(
            (self.root / 'board.md').read_text('utf-8'))[0]['status']), 'delivered')
