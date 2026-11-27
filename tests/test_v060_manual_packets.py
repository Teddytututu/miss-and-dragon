import sys, tempfile, unittest, hashlib, json, subprocess, os, zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'public') if (BASE/'public').exists() else str(BASE))
from board import manual_packets as packets

class ManualPackets(unittest.TestCase):
    def test_complete_two_version_flow_is_local_and_preserves_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';source=root/'numbers.csv';source.write_text('value\n2\n3\n',encoding='utf-8')
            packets.create(folder,'Cache pilot','Compare the same two inputs',[source],task='T001')
            first=packets.paste(folder,'First answer uses inconsistent units',[source]);vid1=first['answer_versions'][0]['id']
            packets.review(folder,vid1,'rejected','Use seconds throughout')
            source.write_text('value\n2\n3\n5\n',encoding='utf-8')
            second=packets.paste(folder,'Second answer corrects the paired measurement',[source]);vid2=second['answer_versions'][1]['id']
            result=packets.review(folder,vid2,'partial','Use measured timing, keep the memory claim open',task='T002')
            self.assertEqual(result['adopted_answer'],vid2)
            self.assertEqual(result['answer_versions'][0]['review']['decision'],'rejected')
            self.assertEqual((folder/result['answer_versions'][0]['files'][0]).read_text('utf-8'),'value\n2\n3\n')
            self.assertEqual(len(packets.paste(folder,'Second answer corrects the paired measurement',[source])['answer_versions']),2)
            before={p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            packets.snapshot(folder)
            after={p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
    def test_invalid_review_keeps_existing_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Toy','Question')
            value=packets.paste(folder,'Answer');vid=value['answer_versions'][0]['id']
            packets.review(folder,vid,'accepted','Use it')
            with self.assertRaises(ValueError):packets.review(folder,'missing','partial','Unknown')
            self.assertEqual(packets.snapshot(folder)['adopted_answer'],vid)

    def test_result_hash_collision_preserves_every_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Toy','Question')
            raw=b'new result';stem='result-'+hashlib.sha256(raw).hexdigest()[:16]
            originals={'result.csv':b'old',stem+'.csv':b'unrelated',stem+'-2.csv':b'other'}
            for name,data in originals.items():(folder/name).write_bytes(data)
            actual=packets._put(folder,'result.csv',raw)
            self.assertEqual(actual,stem+'-3.csv')
            self.assertEqual((folder/actual).read_bytes(),raw)
            self.assertEqual(packets._put(folder,'result.csv',raw),actual)
            for name,data in originals.items():self.assertEqual((folder/name).read_bytes(),data)

    def test_answer_named_attachment_stays_an_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Toy','Question')
            attachment=root/'answer-notes.md';attachment.write_text('Attachment notes',encoding='utf-8')
            row=packets.paste(folder,'The actual answer',[attachment])
            self.assertEqual(len(row['answer_versions']),1)
            self.assertEqual(row['answer_versions'][0]['files'],['answer-notes.md'])
            second=packets.paste(folder,'The next answer')
            self.assertEqual(len(second['answer_versions']),2)
            self.assertEqual(len(packets.snapshot(folder)['answer_versions']),2)

    def test_explicit_input_answer_filename_is_not_a_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Toy','Question')
            (folder/'answer-input.md').write_text('Input document',encoding='utf-8')
            meta=json.loads((folder/'meta.json').read_text('utf-8'))
            meta['attachments'].append({'file':'answer-input.md'})
            (folder/'meta.json').write_text(json.dumps(meta),encoding='utf-8')
            self.assertEqual(packets.snapshot(folder)['answer_versions'],[])

    def test_malformed_version_metadata_raises_a_clear_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Toy','Question')
            meta=json.loads((folder/'meta.json').read_text('utf-8'));meta['answer_versions']=[{}]
            (folder/'meta.json').write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'version'):
                packets.snapshot(folder)

    def test_interrupted_creation_preserves_existing_question_and_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';folder.mkdir()
            originals={'ask.md':b'Original question','materials.zip':b'Original inputs'}
            for name,raw in originals.items():(folder/name).write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'empty packet directory'):
                packets.create(folder,'Replacement','Replacement question')
            for name,raw in originals.items():self.assertEqual((folder/name).read_bytes(),raw)
            self.assertFalse((folder/'meta.json').exists())

    def test_reserved_attachment_failure_does_not_create_a_phantom_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            valid=root/'numbers.csv';valid.write_text('value\n1\n','utf-8')
            reserved=root/'meta.json';reserved.write_text('{"answer":"output"}','utf-8')
            before={p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}
            with self.assertRaisesRegex(ValueError,'result filename'):
                packets.paste(folder,'This paste fails',[valid,reserved])
            self.assertEqual(packets.snapshot(folder)['answer_versions'],[])
            self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()})

    def test_corrupt_cumulative_file_list_is_rejected_before_writing_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Title','Question')
            path=folder/'meta.json';meta=json.loads(path.read_text('utf-8'));meta['answer_files']=42
            path.write_text(json.dumps(meta),'utf-8')
            before={p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}
            with self.assertRaisesRegex(ValueError,'answer_files'):
                packets.paste(folder,'Valid answer text')
            self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()})

    def test_adopted_projection_tracks_rollback_and_never_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'packet';packets.create(folder,'Title','Question')
            first=packets.paste(folder,'Original answer')['answer_versions'][0]['id']
            packets.review(folder,first,'accepted','Use the original')
            second=packets.paste(folder,'Revised answer')['answer_versions'][1]['id']
            packets.review(folder,second,'partial','Use the revision')
            self.assertEqual(packets.adopted(folder)['id'],second)
            packets.review(folder,first,'accepted','Roll back after rechecking')
            before={p.relative_to(folder):p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            chosen=packets.adopted(folder)
            self.assertEqual(chosen['id'],first)
            chosen['files'].append('unrelated.csv')
            self.assertEqual(packets.adopted(folder)['files'],[])
            self.assertEqual(before,{p.relative_to(folder):p.read_bytes() for p in folder.rglob('*') if p.is_file()})
            packets.review(folder,first,'rejected','Withdraw this choice')
            with self.assertRaisesRegex(ValueError,'No adopted answer'):
                packets.adopted(folder)

    def test_adopted_projection_requires_the_reviewed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            result=root/'result.csv';result.write_text('value\n3\n','utf-8')
            row=packets.paste(folder,'Answer',[result])['answer_versions'][0]
            packets.review(folder,row['id'],'accepted','Use the table')
            (folder/'result.csv').unlink()
            with self.assertRaisesRegex(ValueError,'result.csv'):
                packets.adopted(folder)
            meta=json.loads((folder/'meta.json').read_text('utf-8'));meta['adopted_answer']='unknown'
            (folder/'meta.json').write_text(json.dumps(meta),'utf-8')
            with self.assertRaisesRegex(ValueError,'one registered version'):
                packets.adopted(folder)

    def test_reviewed_file_drift_requires_a_new_version_and_legacy_still_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            source=root/'result.csv';source.write_text('value\n3\n','utf-8')
            first=packets.paste(folder,'Answer',[source])['answer_versions'][0]['id']
            packets.review(folder,first,'accepted','Use this table')
            (folder/'result.csv').write_text('value\n9\n','utf-8')
            with self.assertRaisesRegex(ValueError,'paste and review a new'):
                packets.adopted(folder)
            with self.assertRaisesRegex(ValueError,'paste and review a new'):
                packets.review(folder,first,'accepted','Try the same version')
            source.write_text('value\n9\n','utf-8')
            second=packets.paste(folder,'Revised answer',[source])['answer_versions'][1]['id']
            packets.review(folder,second,'accepted','Use the corrected table')
            self.assertEqual(packets.adopted(folder)['id'],second)
            meta=json.loads((folder/'meta.json').read_text('utf-8'))
            for row in meta['answer_versions']:
                row.get('review',{}).pop('artifacts',None)
                row.get('review',{}).pop('inputs',None)
            (folder/'meta.json').write_text(json.dumps(meta),'utf-8')
            before=(folder/'meta.json').read_bytes()
            self.assertEqual(packets.adopted(folder)['id'],second)
            self.assertEqual((folder/'meta.json').read_bytes(),before)

    def test_partial_review_records_selected_files_and_rejects_unknown_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            table=root/'result.csv';table.write_text('value\n3\n','utf-8')
            note=root/'notes.md';note.write_text('Timing still needs review','utf-8')
            identifier=packets.paste(folder,'Answer',[table,note])['answer_versions'][0]['id']
            packets.review(folder,identifier,'partial','Adopt prose only',adopted_files=['notes.md'])
            self.assertEqual(packets.adopted(folder)['review']['adopted_files'],['notes.md'])
            before=(folder/'meta.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'registered file list'):
                packets.review(folder,identifier,'partial','Unknown scope',adopted_files=['missing.csv'])
            with self.assertRaisesRegex(ValueError,'accepted or partial'):
                packets.review(folder,identifier,'rejected','No adoption',adopted_files=['result.csv'])
            self.assertEqual((folder/'meta.json').read_bytes(),before)
            packets.review(folder,identifier,'partial','Legacy note-only review')
            self.assertNotIn('adopted_files',packets.adopted(folder)['review'])

    def test_rejection_keeps_binding_so_reacceptance_cannot_relabel_changed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            source=root/'result.csv';source.write_text('value\n3\n','utf-8')
            first=packets.paste(folder,'Answer',[source])['answer_versions'][0]['id']
            accepted=packets.review(folder,first,'accepted','Adopt')
            binding=accepted['answer_versions'][0]['review']['artifacts']
            inputs=accepted['answer_versions'][0]['review']['inputs']
            rejected=packets.review(folder,first,'rejected','Reconsider')
            self.assertEqual(rejected['answer_versions'][0]['review']['artifacts'],binding)
            self.assertEqual(rejected['answer_versions'][0]['review']['inputs'],inputs)
            (folder/'result.csv').write_text('value\n9\n','utf-8')
            with self.assertRaisesRegex(ValueError,'paste and review a new'):
                packets.review(folder,first,'accepted','Reaccept the changed file')
            source.write_text('value\n9\n','utf-8')
            second=packets.paste(folder,'Revised answer',[source])['answer_versions'][1]['id']
            packets.review(folder,second,'accepted','Use the new version')
            self.assertEqual(packets.adopted(folder)['id'],second)

    def test_changed_original_inputs_require_new_reviewed_answer_before_report(self):
        from board import paired_report
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'attachments/manual-packets/cache-pilot'
            inputs=root/'inputs.csv';inputs.write_text('batch,items\nA,10\nB,20\n','utf-8')
            packets.create(folder,'Title','Question',[inputs])
            table=root/'result.csv';table.write_text('batch,baseline_seconds,cache_seconds\nA,2,1\nB,3,2\n','utf-8')
            first=packets.paste(folder,'Answer',[table])['answer_versions'][0]['id']
            packets.review(folder,first,'accepted','Adopt these timings')
            paired_report.build(root)
            before=(root/'reports/cache-pilot.html').read_bytes()
            with zipfile.ZipFile(folder/'materials.zip','w',zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr('inputs.csv','batch,items\nA,999\nB,999\n')
            for action in [lambda:packets.adopted(folder),
                           lambda:packets.review(folder,first,'accepted','Reaccept old answer'),
                           lambda:paired_report.build(root)]:
                with self.assertRaisesRegex(ValueError,'Original packet inputs changed'):action()
            self.assertEqual((root/'reports/cache-pilot.html').read_bytes(),before)
            second=packets.paste(folder,'A newly checked answer for the changed inputs',[table])['answer_versions'][1]['id']
            packets.review(folder,second,'accepted','Reviewed the new inputs and answer')
            self.assertTrue(paired_report.build(root)['ok'])

    def test_cli_records_explicit_adopted_file_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'packet';packets.create(folder,'Title','Question')
            table=root/'result.csv';table.write_text('value\n3\n','utf-8')
            identifier=packets.paste(folder,'Answer',[table])['answer_versions'][0]['id']
            done=subprocess.run([sys.executable,str(BASE/'scripts/manual_packet.py'),'--packet-dir',str(folder),'review','--version',identifier,'--decision','partial','--note','Adopt timing only','--adopt-file','result.csv'],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertEqual(json.loads(done.stdout)['answer_versions'][0]['review']['adopted_files'],['result.csv'])

    def test_cli_reports_corrupt_metadata_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'中文 包';folder.mkdir();(folder/'meta.json').write_text('{broken','utf-8')
            done=subprocess.run([sys.executable,str(BASE/'scripts/manual_packet.py'),'--packet-dir',str(folder),'show'],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(done.returncode,2)
            error=json.loads(done.stderr);self.assertFalse(error['ok'])
            self.assertIn(str(folder/'meta.json'),error['error'])
            self.assertIn('restore a history copy',error['error'])
            self.assertNotIn('Traceback',done.stderr)

    def test_cli_accepts_bom_question_and_paths_outside_the_source_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);question=root/'问题.md';question.write_text('问题：比较同一批次','utf-8-sig')
            folder=root/'中文 packet'
            done=subprocess.run([sys.executable,str(BASE/'scripts/manual_packet.py'),'--packet-dir',str(folder),'create','--title','中文标题','--question',str(question)],cwd=root,env=dict(os.environ,PYTHONIOENCODING='ascii'),capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertEqual(json.loads(done.stdout)['title'],'中文标题')
            self.assertEqual((folder/'ask.md').read_text('utf-8'),'问题：比较同一批次')

if __name__=='__main__':unittest.main()
