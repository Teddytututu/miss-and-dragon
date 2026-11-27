from pathlib import Path
import json
import tempfile
import unittest
from board import project,storage,events


class EventTests(unittest.TestCase):
    def test_archived_task_holds_dispatch_even_with_stale_running_state(self):
        for status in (None, '1/2 · Running'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);project.initialize(root,'Events','Question','Report',demo=False)
                row=events.enqueue(root,'GPT','T001','implement','v1','Implement current assignment',authorization='Assignment')
                archive=root/'tasks/archive.md';archive.parent.mkdir(exist_ok=True)
                archive.write_text('| T001 | Finished task | accepted | GPT |\n',encoding='utf-8')
                if status:
                    storage.write(root/'attachments/state.json',dict(tasks=dict(T001=dict(status=status))))
                before=(root/events.PATH).read_bytes()
                self.assertIsNone(events.claim(root,row['id']))
                self.assertEqual((root/events.PATH).read_bytes(),before)
                active=events.enqueue(root,'GPT','T002','implement','v1','Current next task',authorization='Assignment')
                self.assertTrue(events.claim(root,active['id']))

    def test_single_flight_and_independent_consumers(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project.initialize(root,'Events','Question','Report',demo=False)
            one=events.enqueue(root,'GPT','T001','implement','v1','Implement the current task',authorization='Current task assignment')
            two=events.enqueue(root,'GPT','T001','implement','v1','Implement the current task',authorization='Current task assignment')
            self.assertEqual(one['id'],two['id'])
            claim=events.claim(root,one['id']);self.assertTrue(claim)
            self.assertIsNone(events.claim(root,one['id']))
            with self.assertRaises(ValueError):events.settle(root,one['id'],'wrong',sent=True)
            events.settle(root,one['id'],claim['claim'],sent=False)
            claim=events.claim(root,one['id']);events.settle(root,one['id'],claim['claim'],sent=True)
            self.assertIsNone(events.claim(root,one['id']))
            self.assertTrue(events.consume(root,'assistant',one['id']))
            self.assertTrue(events.consume(root,'web',one['id']))
            self.assertFalse(events.consume(root,'assistant',one['id']))

    def test_paused_or_closed_task_holds_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project.initialize(root,'Events','Question','Report',demo=False)
            storage.write(root/'attachments/state.json',dict(tasks=dict(T001=dict(status='accepted'))))
            row=events.enqueue(root,'GPT','T001','implement','v1','Implement current assignment',authorization='Assignment')
            self.assertIsNone(events.claim(root,row['id']))


if __name__=='__main__':unittest.main()
