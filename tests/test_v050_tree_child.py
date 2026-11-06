from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from board import agent_tools, storage
from scripts import agent


class TreeChild(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'overview.json'
        storage.write(self.path, {
            'sentinel': 7,
            'tree': [{'title': 'Route', 'status': 'doing', 'children': [
                {'title': 'Existing', 'page': 'report.html', 'children': [{'title': 'Nested'}]},
            ]}],
        })

    def test_new_child_reuses_exact_title_and_preserves_parent(self):
        for _ in range(2):
            value = agent_tools.tree(self.root, 'Route', add_child=' New ', status='done',
                                     summary='Result', task='T001', result='Report')
            self.assertEqual(value, {'node': 'New', 'status': 'done'})
        data = storage.read(self.path)
        parent = data['tree'][0]
        self.assertEqual(data['sentinel'], 7)
        self.assertEqual(parent['status'], 'doing')
        self.assertEqual([row['title'] for row in parent['children']], ['Existing', 'New'])
        child = parent['children'][1]
        self.assertEqual(child['tasks'], ['T001'])
        self.assertEqual(child['results'], ['Report'])
        self.assertEqual(child['summary'], 'Result')

    def test_existing_child_keeps_page_and_descendants(self):
        agent_tools.tree(self.root, 'Route', add_child='Existing', summary='Updated')
        child = storage.read(self.path)['tree'][0]['children'][0]
        self.assertEqual(child['page'], 'report.html')
        self.assertEqual(child['children'], [{'title': 'Nested'}])
        self.assertEqual(child['summary'], 'Updated')

    def test_blank_and_ambiguous_children_preserve_file(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            agent_tools.tree(self.root, 'Route', add_child='  ')
        self.assertEqual(self.path.read_bytes(), before)
        data = storage.read(self.path)
        data['tree'][0]['children'].append({'title': 'Existing'})
        storage.write(self.path, data)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            agent_tools.tree(self.root, 'Route', add_child='Existing')
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_retries_create_one_child(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: agent_tools.tree(self.root, 'Route', add_child='New'), range(2)))
        children = storage.read(self.path)['tree'][0]['children']
        self.assertEqual([row['title'] for row in children], ['Existing', 'New'])
        self.assertEqual(children[1]['status'], 'todo')

    def test_cli_updates_child(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = agent.main(['--as', 'GPT', '--data-dir', str(self.root),
                                    'tree', 'Route', '--add-child', 'New', '--status', 'done'])
        response = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(response['ok'])
        self.assertEqual(response['result']['node'], 'New')
        self.assertEqual(storage.read(self.path)['tree'][0]['children'][1]['status'], 'done')


if __name__ == '__main__':
    unittest.main()
