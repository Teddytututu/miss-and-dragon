"""The demo launcher owns only its marked synthetic workspace."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('portfolio_demo', ROOT/'scripts/portfolio_demo.py')
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class PortfolioDemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name)/'work'
        self.target = self.workspace/'demo'

    def prepare(self, **kwargs):
        return demo.prepare(self.target, workspace=self.workspace, **kwargs)

    def test_first_run_builds_complete_synthetic_data_and_reuses_it(self):
        result = self.prepare()
        self.assertEqual(result['action'], 'created')
        self.assertEqual(result['model_calls'], 0)
        self.assertTrue((self.target/'reports/cache-pilot.html').is_file())
        marker = (self.target/demo.MARKER).read_bytes()
        self.assertEqual(self.prepare()['action'], 'reused')
        self.assertEqual((self.target/demo.MARKER).read_bytes(), marker)

    def test_reset_archives_user_changes_instead_of_deleting_them(self):
        self.prepare()
        (self.target/'my-note.txt').write_text('Keep this note', encoding='utf-8')
        result = self.prepare(reset=True)
        archive = Path(result['archive'])
        self.assertEqual((archive/'my-note.txt').read_text('utf-8'), 'Keep this note')
        self.assertTrue((self.target/'reports/cache-pilot.html').is_file())
        self.assertFalse((self.target/'my-note.txt').exists())

    def test_unmarked_existing_directory_is_preserved(self):
        self.target.mkdir(parents=True)
        (self.target/'private.txt').write_text('private', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.prepare(reset=True)
        self.assertEqual((self.target/'private.txt').read_text('utf-8'), 'private')

    def test_workspace_root_and_outside_paths_are_rejected(self):
        for target in (self.workspace, self.workspace.parent/'other'):
            with self.assertRaises(ValueError):
                demo.prepare(target, workspace=self.workspace, reset=True)

    def test_modified_marker_or_project_identity_is_preserved(self):
        self.prepare()
        (self.target/'project.json').write_text(json.dumps({'name':'Real project'}), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.prepare(reset=True)
        self.assertEqual(json.loads((self.target/'project.json').read_text())['name'], 'Real project')
