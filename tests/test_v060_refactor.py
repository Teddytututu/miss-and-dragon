import json
from pathlib import Path
import tempfile
import unittest
from board import delivery, imports, project, storage
from board.plugins import accounts, budget, queue_protocol


class RefactorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'data'
        project.initialize(self.root,'Fixture','Question','Result',demo=False)

    def artifact(self,name='result.md',text='# Result\nActual finding'):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,'utf-8');return name

    def test_stage_review_binds_actual_bytes_and_invalidates_descendants(self):
        delivery.configure(self.root,'T001','build',executor='GPT')
        delivery.configure(self.root,'T001','report',dependencies=['build'])
        artifact=self.artifact()
        first=delivery.submit(self.root,'T001','build',[artifact],actor='GPT')
        with self.assertRaises(PermissionError):delivery.review(self.root,'T001','build',first['version'],actor='GPT',accept=True)
        delivery.review(self.root,'T001','build',first['version'],actor='Claude',accept=True)
        downstream=delivery.submit(self.root,'T001','report',[self.artifact('report.md')],actor='GPT')
        delivery.review(self.root,'T001','report',downstream['version'],actor='Claude',accept=True)
        self.artifact(text='# Changed result')
        revised=delivery.submit(self.root,'T001','build',[artifact],actor='GPT')
        self.assertNotEqual(first['version'],revised['version'])
        self.assertEqual(delivery.read(self.root)['stages']['T001:report']['state'],'invalidated')
        with self.assertRaises(ValueError):delivery.review(self.root,'T001','build',first['version'],actor='Claude',accept=True)

    def test_publication_freezes_reviewed_closure_and_retries_independent_steps(self):
        from board import publication
        delivery.configure(self.root,'T002','report')
        self.artifact('style.css','body{color:navy}')
        self.artifact('report.html','<link rel="stylesheet" href="style.css"><h1>Result</h1>')
        row=delivery.submit(self.root,'T002','report',['report.html','style.css'],actor='GPT')
        delivery.review(self.root,'T002','report',row['version'],actor='Claude',accept=True)
        calls=[]
        def opening(url):calls.append(url);raise OSError('browser fixture')
        first=publication.publish(self.root,'T002','report','report.html','Result',open_report=opening)
        self.assertEqual(first['opening'],'failed')
        second=publication.publish(self.root,'T002','report','report.html','Result',open_report=lambda url: calls.append(url))
        self.assertEqual(first['path'],second['path'])
        self.assertEqual(sum('publication_id' in link for link in storage.read(self.root/'overview.json')['links']),1)
        self.artifact('report.html','changed')
        self.assertIn('Result',(self.root/first['path']).read_text('utf-8'))
        with self.assertRaises(ValueError):publication.publish(self.root,'T002','report','report.html','Result')

    def test_explicit_packet_import_is_version_scoped_and_retry_safe(self):
        from board import manual_packets
        folder=self.root/'attachments/manual-packets/P001-example'
        manual_packets.create(folder,'Title','Question')
        manual_packets.paste(folder,'# First answer')
        version=manual_packets.snapshot(folder)['answer_versions'][0]['id']
        file=Path(self.temp.name)/'result.txt';file.write_text('one','utf-8')
        first=imports.attach(self.root,'P001-example',[file],version_id=version)
        imports.attach(self.root,'P001-example',[file],version_id=version)
        self.assertEqual(len(manual_packets.snapshot(folder)['answer_versions'][0]['files']),1)
        file.write_text('two','utf-8');imports.attach(self.root,'P001-example',[file],version_id=version)
        self.assertEqual(len(manual_packets.snapshot(folder)['answer_versions'][0]['files']),2)
        self.assertTrue(file.exists())

    def test_current_task_restore_and_consumer_ack_are_separate(self):
        from board import continuity
        continuity.set_current(self.root,'GPT','T001','Implement','results/example.md',authorization='explicit-current-instruction')
        pointer=continuity.current(self.root,'GPT')
        self.assertEqual(pointer['task'],'T001')
        first=continuity.record(self.root,'GPT','T001','stage-a','turn-a','running')
        second=continuity.record(self.root,'GPT','T002','stage-a','turn-a','running')
        self.assertNotEqual(first['id'],second['id'])
        self.assertTrue(continuity.consume(self.root,'web','message-a'))
        self.assertTrue(continuity.consume(self.root,'assistant','message-a'))
        self.assertFalse(continuity.consume(self.root,'web','message-a'))

    def test_decision_revision_requires_current_claim_and_actual_artifact(self):
        from board import decisions
        with storage.locked(self.root):
            value=storage.read(self.root/'overview.json');row=decisions.add(value,'Choose a route','Resource choice',['A','B'])
            storage.write(self.root/'overview.json',value)
        decisions.choose(self.root,'owner',dict(id=row['id'],option=0))
        first=decisions.claim(self.root,row['id'],'GPT','Implement selected route')
        decisions.choose(self.root,'owner',dict(id=row['id'],option=1))
        with self.assertRaises(ValueError):decisions.finish(self.root,row['id'],'GPT',self.artifact())
        second=decisions.claim(self.root,row['id'],'GPT','Implement revised route')
        self.assertNotEqual(first['selection_key'],second['selection_key'])
        result=decisions.finish(self.root,row['id'],'GPT',self.artifact())
        self.assertTrue(result['acked_at'])


if __name__=='__main__':unittest.main()
