import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from board import project,storage,lifecycle

ROOT=Path(__file__).resolve().parents[1]

class ReviewGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);project.initialize(self.root,'Example')
        (self.root/'board.md').write_text('| T001 | Old delivery | 已交 · 待验收 | GPT | 2020-01-01 |\n| T002 | Other chat | delivered · awaiting review | GPT | 2020-01-02 |\n',encoding='utf-8')

    def test_all_deliveries_block_before_patrol_writes(self):
        before=(self.root/'overview.json').read_bytes()
        with self.assertRaises(ValueError):lifecycle.log_patrol(self.root,'Claude','Reviewed')
        self.assertEqual(before,(self.root/'overview.json').read_bytes())
        self.assertFalse((self.root/'attachments/patrol-log.jsonl').exists())

    def test_each_card_needs_a_reason(self):
        for defer in [['T001:preview'],['T001:','T002:decision'],['T001:preview','T002:  '],['T001:preview','T002:decision','T999:typo']]:
            with self.subTest(defer=defer),self.assertRaises(ValueError):
                lifecycle.log_patrol(self.root,'Claude','Reviewed',defer=defer)

    def test_valid_deferrals_persist_full_reasons(self):
        reason='A specific preview review requested by the user, with a full description longer than eighty characters preserved in the structured record'
        row=lifecycle.log_patrol(self.root,'Claude','Reviewed',defer=['T001:'+reason,'T002:Awaiting lead decision'])
        self.assertEqual(row['deferred'],{'T001':reason,'T002':'Awaiting lead decision'})
        saved=storage.lines(self.root/'attachments/patrol-log.jsonl')[-1]
        self.assertEqual(row['deferred'],saved['deferred'])

    def test_gpt_patrol_continues_and_cleared_board_passes(self):
        self.assertEqual(lifecycle.log_patrol(self.root,'GPT','Delivered')['who'],'GPT')
        (self.root/'board.md').write_text('| T001 | Accepted | accepted | GPT |\n| T002 | Rework | rejected | GPT |\n',encoding='utf-8')
        self.assertEqual(lifecycle.log_patrol(self.root,'Claude','Reviewed')['who'],'Claude')

    def test_direct_cli_enforces_gate(self):
        p=subprocess.run([sys.executable,str(ROOT/'scripts/patrol_log.py'),'Claude','Reviewed','--data-dir',str(self.root)],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('T001',p.stderr)

    def test_agent_blocks_before_mood_or_patrol_side_effects(self):
        before=(self.root/'overview.json').read_bytes()
        p=subprocess.run([sys.executable,str(ROOT/'scripts/agent.py'),'--as','Claude','patrol','Reviewed','--mood','calm','--data-dir',str(self.root)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(json.loads(p.stdout)['ok'],False)
        self.assertEqual((self.root/'overview.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
