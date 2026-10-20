import os, shutil, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


class ScoreTests(TmpCase):
    def score(self, run_dir, *extra):
        p = run("score.py", run_dir, GOLD, "--json", *extra)
        import json
        return p.returncode, json.loads(p.stdout)

    def test_identical_is_perfect(self):
        rc, out = self.score(GOLD, "--actions", "actions.pre-resolution.json")
        self.assertEqual(rc, 0)
        self.assertEqual(out["records"]["f1"], 1.0); self.assertEqual(out["orphans"]["f1"], 1.0)
        self.assertEqual(out["classification"]["accuracy"], 1.0)
        self.assertEqual(out["edges_explicit"]["f1"], 1.0); self.assertEqual(out["edges_inferred_recall"]["found"], 4)

    def test_renumbered_records_still_match(self):
        d = self.golden_copy()
        recs = load(d + "/actions.pre-resolution.json")
        recs.reverse()
        for r in recs:
            r["id"] = "X" + r["id"][1:]
        dump(d + "/actions.pre-resolution.json", recs)
        rc, out = self.score(d, "--actions", "actions.pre-resolution.json")
        self.assertEqual(out["records"]["f1"], 1.0)

    def test_missing_record_lowers_recall(self):
        d = self.golden_copy()
        recs = [r for r in load(d + "/actions.pre-resolution.json") if r["id"] != "A-9.10.040-1"]
        dump(d + "/actions.pre-resolution.json", recs)
        rc, out = self.score(d, "--actions", "actions.pre-resolution.json", "--min-record-f1", "0.99")
        self.assertEqual(rc, 1)
        self.assertEqual(out["records"]["missed"], ["A-9.10.040-1"]); self.assertLess(out["records"]["recall"], 1.0)

    def test_wrong_field_and_class_are_reported(self):
        d = self.golden_copy()
        recs = load(d + "/actions.pre-resolution.json")
        next(r for r in recs if r["id"] == "A-9.10.050.C-1")["timing"]["amount"] = 9
        next(r for r in recs if r["id"] == "A-9.10.080.B-1")["signal"]["type"] = "event"
        dump(d + "/actions.pre-resolution.json", recs)
        prov = load(d + "/provisions.json"); prov[0]["class"] = "operative"; dump(d + "/provisions.json", prov)
        rc, out = self.score(d, "--actions", "actions.pre-resolution.json")
        self.assertEqual(out["fields"]["timing"]["correct"], out["fields"]["timing"]["total"] - 1)
        self.assertEqual(out["fields"]["signal_type"]["correct"], out["fields"]["signal_type"]["total"] - 1)
        self.assertIn("9.10.010", out["classification"]["wrong"])

    def test_false_orphan_and_missed_orphan(self):
        d = self.golden_copy()
        o = load(d + "/orphans.json")
        o = [x for x in o if x["code"] != "O-VERB"]                       # missed
        o.append(dict(o[0], id="ORP-99", code="O-ACT", records=["A-9.10.040-1"]))   # false
        dump(d + "/orphans.json", o)
        rc, out = self.score(d, "--actions", "actions.pre-resolution.json")
        self.assertIn(["O-VERB", "9.10.080.C"], [list(x) for x in out["orphans"]["missed"]])
        self.assertIn(["O-ACT", "9.10.040"], [list(x) for x in out["orphans"]["false"]])


if __name__ == "__main__":
    unittest.main()
