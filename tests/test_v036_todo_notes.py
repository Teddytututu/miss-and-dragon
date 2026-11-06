from pathlib import Path
import tempfile,unittest
from board import project,storage,todo_notes

class NoteReplies(unittest.TestCase):
    def test_reply_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project.initialize(root,'Notes',question='Question',deliverable='Page')
            storage.write(root/'overview.json',dict(todo=[dict(what='Read the result',by='GPT')]))
            key=todo_notes.view(storage.read(root/'overview.json'))['todo'][0]['note_id']
            payload=dict(op='reply',id=key,text='I have read it',client_id='note-reply-client-0001')
            result=todo_notes.choose(root,'owner',payload)
            self.assertEqual(result['todo'][0]['note_id'],key)
            todo_notes.choose(root,'owner',payload)
            self.assertEqual(len(project.raw_posts(root)),1)
            self.assertEqual(project.raw_posts(root)[0]['author'],'owner')
            self.assertEqual(result['todo'][0]['note_replies'][0]['to'],'GPT')
            for changed in [dict(payload,text='changed'),dict(payload,text='x'*41),dict(payload,id='stale')]:
                with self.assertRaises(ValueError):todo_notes.choose(root,'owner',changed)
            with self.assertRaises(ValueError):todo_notes.choose(root,'GPT',payload)
