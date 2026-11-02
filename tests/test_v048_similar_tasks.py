from pathlib import Path
import tempfile
import unittest
from board import lifecycle, project, storage


class SimilarTasks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        (self.root/'tasks').mkdir(exist_ok=True)
        (self.root/'tasks/T003-next.md').write_text('# Next\nKeep this scope.\n')
        (self.root/'board.md').write_text(
            '| T001 | [视频评分曲线](tasks/T001-old.md) | queued: ready now | GPT |\n')
        (self.root/'tasks/archive.md').write_text(
            '| T002 | [视频评分结果](tasks/T002-old.md) | accepted: done | GPT |\n')

    def test_creation_advises_live_and_archived_matches_without_blocking(self):
        before = (self.root/'tasks/archive.md').read_bytes()
        result = lifecycle.transition(self.root, 'new', 'T003', by='Claude',
            title='视频评分复查', when='ready now')
        self.assertEqual({m['task'] for m in result['similar_tasks']}, {'T001', 'T002'})
        self.assertTrue(result['warnings'])
        self.assertIn('T003', (self.root/'board.md').read_text())
        self.assertEqual((self.root/'tasks/archive.md').read_bytes(), before)
        self.assertEqual(storage.lines(self.root/'attachments/task-flow.jsonl')[-1]['similar_tasks'], result['similar_tasks'])

    def test_title_only_deduplicates_ids_and_ignores_links_and_status(self):
        rows = lifecycle.parse_board((self.root/'board.md').read_text())
        self.assertEqual(lifecycle.similar_tasks('T003', 'unrelated', rows), [])
        hits = lifecycle.similar_tasks('T003', '视频评分曲线', rows+rows)
        self.assertEqual([r['task'] for r in hits], ['T001'])
        self.assertEqual(lifecycle.similar_tasks('T001', '视频评分曲线', rows), [])

    def test_short_exact_titles_and_case_normalization(self):
        rows = [dict(task='T001', title='[QA](tasks/a.md)')]
        self.assertEqual(lifecycle.similar_tasks('T002', 'qa', rows)[0]['task'], 'T001')


if __name__ == '__main__':
    unittest.main()
