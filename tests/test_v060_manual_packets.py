import sys, tempfile, unittest, hashlib, json
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

if __name__=='__main__':unittest.main()
