import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from board.ticket_schedule import plan
NOW="2026-11-19T10:00:00+08:00"
def job(id,seconds,**kw): return dict(id=id,unit="job",units=1,measurement=dict(unit="job",seconds=seconds,units=1),**kw)
class TicketSchedule(unittest.TestCase):
    def test_two_then_three_hours_on_one_card(self):
        a,b=plan([job("a",7200),job("b",10800)],cards=1,now=NOW)["jobs"]
        self.assertEqual(a["finish"],"2026-11-19T12:00:00+08:00")
        self.assertEqual(b["finish"],"2026-11-19T15:00:00+08:00")
    def test_one_job_uses_one_of_four_cards(self):
        r=plan([job("a",7200)],now=NOW)
        self.assertEqual(r["jobs"][0]["finish"],"2026-11-19T12:00:00+08:00")
        self.assertEqual(r["remaining_card_hours"],2)
    def test_five_jobs_take_two_waves(self):
        r=plan([job(str(i),3600) for i in range(5)],now=NOW)
        self.assertEqual(r["finish"],"2026-11-19T12:00:00+08:00")
    def test_batch_timing_stays_per_batch(self):
        j=dict(id="a",unit="batch",units=1,measurement=dict(unit="batch",seconds=32400,units=1))
        self.assertEqual(plan([j],now=NOW)["remaining_card_hours"],9)
    def test_unit_mismatch_waits_for_trial(self):
        j=dict(id="a",unit="image",units=20,measurement=dict(unit="batch",seconds=32400,units=1))
        self.assertEqual(plan([j],now=NOW)["jobs"][0]["state"],"waiting_trial")
    def test_missing_measurement_waits_for_trial(self):
        self.assertEqual(plan([dict(id="a",unit="job",units=1)],now=NOW)["jobs"][0]["state"],"waiting_trial")
    def test_running_job_holds_its_card(self):
        a=job("a",7200,state="running",card=0,elapsed_seconds=3600)
        r=plan([a,job("b",10800)],cards=1,now=NOW)
        self.assertEqual(r["jobs"][1]["finish"],"2026-11-19T14:00:00+08:00")
    def test_dependencies_wait_and_input_stays_unchanged(self):
        a=job("a",7200);b=job("b",10800,depends_on=["a"])
        import copy
        original=copy.deepcopy([b,a]);r=plan([b,a],now=NOW)
        self.assertEqual([b,a],original)
        self.assertEqual(r["jobs"][0]["finish"],"2026-11-19T15:00:00+08:00")
    def test_completed_yesterday_stays_completed(self):
        j=job("a",7200,state="done")
        self.assertEqual(plan([j],now=NOW)["jobs"][0]["state"],"done")
        self.assertEqual(plan([j],now=NOW)["remaining_card_hours"],0)
    def test_pending_after_unmeasured_running_stays_waiting(self):
        a=dict(id="a",state="running",card=0,unit="job",units=1)
        self.assertEqual(plan([a,job("b",3600)],cards=1,now=NOW)["jobs"][1]["state"],"waiting_card")
    def test_cycle_remains_waiting(self):
        r=plan([job("a",3600,depends_on=["b"]),job("b",3600,depends_on=["a"])],now=NOW)
        self.assertTrue(all(j["state"]=="waiting_dependency" for j in r["jobs"]))
    def test_file_projection_preserves_bytes(self):
        from board.ticket_schedule import from_file
        import tempfile,json
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"plan.json"
            path.write_text(json.dumps(dict(cards=1,jobs=[job("a",3600)])),encoding="utf8")
            original=path.read_bytes()
            self.assertEqual(from_file(path,now=NOW)["remaining_card_hours"],1)
            self.assertEqual(path.read_bytes(),original)
            self.assertIsNone(from_file(Path(folder)/"missing.json",now=NOW))
    def test_completed_card_and_zero_remaining_running_are_distinct(self):
        r=plan([job("a",3600,state="running",card=0,remaining_seconds=0),job("b",3600)],cards=1,now=NOW)
        self.assertEqual(r["jobs"][1]["finish"],"2026-11-19T11:00:00+08:00")
    def test_malformed_job_inputs_raise_value_error(self):
        bad_cases=[None,{},"jobs",[None],[1],[{}],[dict(id="a",measurement="text")],
                   [dict(id="a",measurement=[])],[dict(id="a",depends_on="a")],
                   [dict(id="a",depends_on=None)],[dict(id="a",depends_on=[{}])],
                   [dict(id="a",unit=7)]]
        for bad in bad_cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError): plan(bad,now=NOW)
    def test_malformed_numbers_raise_value_error(self):
        for cards in (None,{},[],float("inf"),float("nan"),True):
            with self.subTest(cards=cards),self.assertRaises(ValueError):plan([],cards=cards,now=NOW)
        for value in ({},[],"seconds",float("inf"),True):
            with self.subTest(value=value),self.assertRaises(ValueError):plan([job("a",value)],now=NOW)
    def test_file_schema_errors_raise_value_error(self):
        from board.ticket_schedule import from_file
        import tempfile,json
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"plan.json"
            for value in ([],{},dict(jobs="bad"),dict(jobs=[None])):
                path.write_text(json.dumps(value),encoding="utf8")
                with self.subTest(value=value),self.assertRaises(ValueError):from_file(path,now=NOW)
    def test_running_start_contains_elapsed_history(self):
        r=plan([job("a",7200,state="running",card=0,elapsed_seconds=3600)],now=NOW)["jobs"][0]
        self.assertEqual(r["start"],"2026-11-19T09:00:00+08:00")
        self.assertEqual(r["finish"],"2026-11-19T11:00:00+08:00")
        self.assertEqual(r["run_elapsed_seconds"],3600)
        self.assertEqual(r["total_seconds"],7200)
        self.assertEqual(r["card_hours"],1)
    def test_running_explicit_remaining_preserves_actual_start(self):
        r=plan([dict(id="a",state="running",card=0,elapsed_seconds=3600,remaining_seconds=5400)],now=NOW)["jobs"][0]
        self.assertEqual(r["start"],"2026-11-19T09:00:00+08:00")
        self.assertEqual(r["finish"],"2026-11-19T11:30:00+08:00")
        self.assertEqual(r["total_seconds"],9000)
if __name__=="__main__": unittest.main()
