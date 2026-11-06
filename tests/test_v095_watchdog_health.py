from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from board import checks, project, storage
from scripts import night_watch


class WatchdogHealth(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project.initialize(self.root, 'Example')
        self.at = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def record(self, age=10, **fields):
        row = dict(last_checked_at=(self.at-timedelta(minutes=age)).isoformat(),
                   run_seconds=2, sleep_ms=1000)
        row.update(fields)
        storage.write(self.root/'attachments/state.json', dict(watchdog=row))

    def observe(self, sleep_ms):
        with patch('board.watch_clock.sleep_milliseconds', return_value=sleep_ms):
            return checks.watchdog_alive(self.root, now=self.at)

    def test_sleep_is_subtracted_but_awake_stalls_still_fail(self):
        self.record(age=130)
        self.assertTrue(self.observe(120*60000+1000)['ok'])
        self.assertFalse(self.observe(100*60000+1000)['ok'])

    def test_wall_clock_fallback_after_reboot_or_without_counter(self):
        self.record(age=16)
        self.assertFalse(self.observe(None)['ok'])
        self.assertFalse(self.observe(0)['ok'])
        self.record(age=15, sleep_ms=None)
        self.assertTrue(self.observe(200000)['ok'])

    def test_run_duration_and_invalid_or_missing_observations(self):
        self.assertIsNone(self.observe(None)['ok'])
        self.record(run_seconds=301)
        self.assertFalse(self.observe(1000)['ok'])
        self.record(run_seconds=300)
        self.assertTrue(self.observe(1000)['ok'])
        self.record(last_checked_at='invalid')
        self.assertIsNone(self.observe(1000)['ok'])
        with patch('board.checks.storage.read', return_value=dict(watchdog=dict(
                last_checked_at=self.at.isoformat(), run_seconds=float('nan')))):
            self.assertIsNone(self.observe(1000)['ok'])
        self.record(age=-1)
        self.assertIsNone(self.observe(1000)['ok'])

    def test_successful_patrol_records_completion_and_elapsed_time(self):
        with patch('scripts.night_watch.time', SimpleNamespace(monotonic=Mock(side_effect=[10, 12.5]))), \
             patch('board.watch_clock.sleep_milliseconds', return_value=1234):
            night_watch.patrol(self.root, data_dir='.', now=self.at.timestamp())
        row = storage.read(self.root/'attachments/state.json')['watchdog']
        self.assertEqual(datetime.fromisoformat(row['last_checked_at']), self.at+timedelta(seconds=2.5))
        self.assertEqual(row['run_seconds'], 2.5)
        self.assertEqual(row['sleep_ms'], 1234)
        self.assertIn('watchdog_alive', checks.run(self.root, now=self.at+timedelta(minutes=1)))

    def test_late_state_updates_survive_and_failed_patrol_keeps_health_record(self):
        def concurrent_update(*args, **kwargs):
            storage.write(self.root/'attachments/state.json', dict(other_writer='saved'))
        with patch('scripts.night_watch.task_eta.refresh', side_effect=concurrent_update):
            night_watch.patrol(self.root, data_dir='.', now=self.at.timestamp())
        state = storage.read(self.root/'attachments/state.json')
        self.assertEqual(state['other_writer'], 'saved')
        with patch('scripts.night_watch.task_eta.refresh', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError):
                night_watch.patrol(self.root, data_dir='.', now=self.at.timestamp()+60)
        self.assertEqual(storage.read(self.root/'attachments/state.json')['watchdog'], state['watchdog'])

    def test_non_windows_counter_is_optional(self):
        from board import watch_clock
        with patch.object(watch_clock.os, 'name', 'posix'):
            self.assertIsNone(watch_clock.sleep_milliseconds())


if __name__ == '__main__':unittest.main()
