"""Voice setup stays optional and only appears on qualifying local hardware."""
from pathlib import Path
import tempfile, unittest
from board import onboarding, project


class VoicePreferences(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        project.initialize(self.root,'Voice fixture')
        self.gpu=lambda:[8192]
        self.disk=lambda root:20*(1024**3)

    def tearDown(self):
        self.tmp.cleanup()

    def test_qualifying_machine_shows_choice_and_links_official_project(self):
        result=onboarding.configure_voice(self.root,gpu_probe=self.gpu,disk_probe=self.disk)
        self.assertTrue(result['show_prompt'])
        self.assertTrue(result['decision_required'])
        self.assertEqual(result['mode'],'disabled')
        enabled=onboarding.configure_voice(self.root,'enable',gpu_probe=self.gpu,disk_probe=self.disk)
        self.assertEqual(enabled['mode'],'enabled')
        self.assertEqual(enabled['license'],'Apache-2.0')
        self.assertTrue(enabled['project_url'].startswith('https://github.com/'))
        self.assertIn('#installation',enabled['install_url'])

    def test_missing_gpu_defaults_off_and_hides_choice(self):
        result=onboarding.configure_voice(self.root,gpu_probe=lambda:[],disk_probe=self.disk)
        self.assertFalse(result['show_prompt'])
        self.assertFalse(result['decision_required'])
        self.assertEqual(result['mode'],'disabled')

    def test_insufficient_gpu_memory_defaults_off_and_hides_choice(self):
        result=onboarding.configure_voice(self.root,gpu_probe=lambda:[5120],disk_probe=self.disk)
        self.assertFalse(result['show_prompt'])
        self.assertFalse(result['hardware']['eligible'])

    def test_insufficient_disk_defaults_off_and_hides_choice(self):
        result=onboarding.configure_voice(self.root,gpu_probe=self.gpu,disk_probe=lambda root:9*(1024**3))
        self.assertFalse(result['show_prompt'])
        self.assertFalse(result['hardware']['eligible'])


if __name__=='__main__':
    unittest.main()
