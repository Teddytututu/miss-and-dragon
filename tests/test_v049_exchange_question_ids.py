from pathlib import Path
from datetime import datetime,timezone
import tempfile,unittest
from board import exchange

class QuestionIds(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'exchange').mkdir()
    def write(self,*rows):
        text=''.join(f'### 2026-01-01T{stamp}:00+00:00 · {author} → {peer} · T101 · {title}\n{body}\n' for stamp,author,peer,title,body in rows)
        (self.root/'exchange/2026-01-01.md').write_text(text,encoding='utf8')
    def test_body_request_in_handoff_stays_a_note(self):
        self.write(('08:00','GPT','Claude','Implementation result','Please confirm the caption when reviewing.'))
        self.assertEqual(exchange.open_questions(self.root),{})
    def test_explicit_heading_opens_without_body_keywords(self):
        self.write(('08:00','GPT','Claude','问：[abcd1234] [design] Layout','A or B.'))
        self.assertEqual(len(exchange.open_questions(self.root)),1)
    def test_exact_identifier_answer_closes_despite_changed_caption(self):
        self.write(('08:00','GPT','Claude','问：[abcd1234] [design] Layout','A or B.'),
                   ('08:10','Claude','GPT','答：[abcd1234] Layout approved','A.'))
        self.assertEqual(exchange.open_questions(self.root),{})
    def test_unrelated_answer_and_quoted_identifier_keep_question(self):
        self.write(('08:00','GPT','Claude','问：[abcd1234] [design] Layout','A or B.'),
                   ('08:10','Claude','GPT','答：[eeee1234] Another choice','A.'),
                   ('08:11','Claude','GPT','Review of [abcd1234] evidence','Continue.'))
        self.assertEqual(len(exchange.open_questions(self.root)),1)
    def test_legacy_title_reply_is_preserved(self):
        self.write(('08:00','GPT','Claude','问：Layout','A or B.'),
                   ('08:10','Claude','GPT','答：Layout','A.'))
        self.assertEqual(exchange.open_questions(self.root),{})

if __name__=='__main__':unittest.main()
