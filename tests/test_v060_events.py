from pathlib import Path
import json
import tempfile
import unittest
from board import project,storage,events


class EventTests(unittest.TestCase):
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
