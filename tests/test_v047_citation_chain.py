import csv,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

class CitationChain(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('public_citation_chain',Path(__file__).resolve().parents[1]/'scripts/citation_chain.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_cached_response_is_reused_without_network(self):
        import hashlib
        url='https://example.org/paper';cache=self.root/'cache';cache.mkdir()
        (cache/(hashlib.sha1(url.encode()).hexdigest()+'.json')).write_text('{"paperId":"P1"}')
        with patch.object(self.m,'urlopen',side_effect=AssertionError('network')):
            self.assertEqual(self.m.get(url,cache,lambda text:None)['paperId'],'P1')
    def test_daily_mode_excludes_known_papers_and_clears_stale_output(self):
        seeds=self.root/'seeds.txt';seeds.write_text('0000.00001 # example\n')
        exclude=self.root/'seen.csv';exclude.write_text('paperId\nP1\n')
        out=self.root/'out';out.mkdir();(out/'candidates.csv').write_text('stale result')
        seed=dict(paperId='S1',title='Example seed',externalIds={'ArXiv':'0000.00001'})
        candidate=dict(paperId='P1',title='Example candidate',publicationDate='2026-01-13',year=2026)
        with patch.object(self.m,'get',return_value=seed),patch.object(self.m,'pages',return_value=[candidate]) as pages,patch.object(sys,'argv',['citation_chain.py',str(seeds),str(out),'--since','2026-01-12','--exclude',str(exclude)]):
            self.m.main()
            self.assertEqual(pages.call_args.args[1],'citations')
        with (out/'candidates.csv').open(encoding='utf-8-sig') as stream:self.assertEqual(list(csv.DictReader(stream)),[])

if __name__=='__main__':unittest.main()
