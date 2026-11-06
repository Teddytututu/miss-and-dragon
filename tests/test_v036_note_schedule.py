from pathlib import Path
from datetime import datetime,timedelta
import tempfile,unittest
from board import project,storage,todo_notes,note_schedule,plan_checks

class NoteSchedule(unittest.TestCase):
    def test_same_day_and_rollover(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project.initialize(root,'Plan',question='Q',deliverable='Page')
            storage.write(root/'overview.json',dict(todo=[dict(what='Same'),dict(what='Same'),dict(what='Other')],schedule=[]))
            rows=todo_notes.view(storage.read(root/'overview.json'))['todo']
            for i,row in enumerate(rows[:2]):
                payload=dict(op='schedule',id=row['note_id'],client_id='schedule-client-00'+str(i))
                todo_notes.choose(root,'owner',payload);todo_notes.choose(root,'owner',payload)
            value=storage.read(root/'overview.json');today=note_schedule.today_date()
            projected=plan_checks.project(value['schedule'],today=today)
            key=projected[0]['items'][0]['check_id']
            storage.write(root/'attachments/plan-checks.json',dict(items={key:dict(completed=True,updated_at=datetime.now().astimezone().isoformat())}))
            self.assertEqual(note_schedule.rollover(root,today),0)
            self.assertEqual(len(storage.read(root/'overview.json')['schedule'][0]['items']),2)
            self.assertEqual(note_schedule.rollover(root,today+timedelta(days=1)),2)
            value=storage.read(root/'overview.json')
            self.assertEqual([row['what'] for row in value['todo']],['Same','Other'])
            self.assertEqual(value['todo'][0]['note_id'],rows[1]['note_id'])
            self.assertEqual(len(value['todo_done']),1)
            self.assertEqual(note_schedule.rollover(root,today+timedelta(days=1)),0)
