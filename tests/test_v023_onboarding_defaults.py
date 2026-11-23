"""First-run choices remain local, explicit and recoverable."""
from pathlib import Path
import importlib.util, io, json, os, subprocess, tempfile, unittest
from unittest.mock import Mock, patch
from board import onboarding, project, storage, assets
from board.app import conversation

ROOT = Path(__file__).resolve().parents[1]
(ROOT/'work/tests').mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(ROOT/'work/tests')


class FirstRunDefaults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Fictional first run')

    def tearDown(self):
        self.tmp.cleanup()

    def test_bundled_characters_satisfy_setup_without_generation(self):
        for agent in ['GPT', 'Claude']:
            result = onboarding.status(self.root, agent)
            self.assertTrue(result['checks']['artwork'])
            self.assertEqual(result['artwork']['mode'], 'bundled')
            self.assertTrue(all(row['file'].endswith('.svg') for row in result['artwork']['files']))
        self.assertFalse((self.root/'attachments/generated').exists())

    def test_unanswered_prompt_uses_unicode_without_downloader_or_stdin(self):

        with patch('builtins.input', side_effect=AssertionError('Interactive input')):
            first = onboarding.configure_emotes(self.root)
            again = onboarding.configure_emotes(self.root)
        self.assertTrue(first['show_prompt'])
        self.assertFalse(again['show_prompt'])
        self.assertFalse(again['decision_required'])
        self.assertEqual(again['mode'], 'unicode')

    def test_decline_is_reused_and_existing_chat_artwork_bytes_survive(self):
        post = project.post(self.root, 'GPT', 'Existing opening')
        art = self.root/'attachments/generated/GPT/avatar.png'
        art.parent.mkdir(parents=True)
        art.write_bytes(b'prior artwork')
        ledger = project.ledger(self.root).read_bytes()
        onboarding.configure_emotes(self.root, 'unicode')
        result = onboarding.configure_emotes(self.root)
        self.assertEqual((result['mode'], result['decision_required']), ('unicode', False))
        self.assertEqual(project.ledger(self.root).read_bytes(), ledger)
        self.assertEqual(art.read_bytes(), b'prior artwork')
        self.assertEqual(conversation(self.root)['items'][0]['id'], post['id'])

    def test_saved_opt_in_reuses_guide_and_falls_back_without_local_files(self):
        result = onboarding.configure_emotes(self.root, 'download')
        self.assertEqual((result['mode'], result['status']), ('unicode', 'awaiting-local-files'))
        again = onboarding.configure_emotes(self.root)
        self.assertEqual(again['guide'], 'docs/local-emotes.md')
        self.assertEqual(again['choice'], 'download')
        self.assertFalse((self.root/'emotes').exists())

    def test_invalid_manifest_entries_keep_unicode(self):
        onboarding.configure_emotes(self.root, 'download')
        manifest = self.root/'emotes/manifest.json'
        storage.write(manifest, [{'id': '../other', 'label': 'Escape'}, {'id': 42, 'label': 'Missing'}, {'id': 7, 'label': 'Remote', 'url': 'https://example.org/image.png'}])
        self.assertEqual(conversation(self.root)['reaction_catalog'], [])
        manifest.write_text('{', encoding='utf-8')
        self.assertEqual(conversation(self.root)['reaction_catalog'], [])
        self.assertEqual(onboarding.emote_preferences(self.root)['mode'], 'unicode')

    def test_night_watch_registration_is_injectable_and_failure_is_actionable(self):
        spec = importlib.util.spec_from_file_location('onboarding_bootstrap', ROOT/'scripts/bootstrap.py')
        bootstrap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bootstrap)
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, '{"registered":true}', ''))
        result = bootstrap.register_night_watch('local-python', self.root, runner=runner)
        self.assertEqual(result['status'], 'registered')
        command = runner.call_args.args[0]
        self.assertEqual(command[command.index('--data-dir')+1], self.root.relative_to(ROOT).as_posix())
        self.assertIn('--install', command)
        runner.side_effect = OSError('Fictional scheduler error')
        result = bootstrap.register_night_watch('local-python', self.root, runner=runner)
        self.assertEqual(result['status'], 'manual')
        self.assertIn('install_night_watch.py', result['manual_command'])
        self.assertIn('Fictional scheduler error', result['error'])


if __name__ == '__main__':
    unittest.main()
