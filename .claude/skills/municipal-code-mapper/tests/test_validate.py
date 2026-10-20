import copy, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


class ValidateTests(TmpCase):
    def v(self, d, stage, actions, source=True):
        args = [d, "--stage", stage, "--actions", actions, "--json"]
        if source:
            args += ["--source", SOURCE]
        p = run("validate.py", *args)
        import json
        return p.returncode, {e["code"] for e in json.loads(p.stdout)["errors"]}

    def test_golden_passes_every_stage(self):
        self.assertEqual(self.v(GOLD, "segment", "actions.frozen.json"), (0, set()))
        self.assertEqual(self.v(GOLD, "extract", "actions.pre-resolution.json"), (0, set()))
        self.assertEqual(self.v(GOLD, "frozen", "actions.frozen.json"), (0, set()))
        self.assertEqual(self.v(GOLD, "deps", "actions.frozen.json"), (0, set()))

    def mutate(self, fname, fn, stage="deps", actions="actions.frozen.json"):
        d = self.golden_copy(); data = load(f"{d}/{fname}"); fn(data); dump(f"{d}/{fname}", data)
        return self.v(d, stage, actions)

    def rec(self, data, rid):
        return next(r for r in data if r["id"] == rid)

    def test_altered_quote(self):
        rc, codes = self.mutate("actions.frozen.json", lambda d: self.rec(d, "A-9.10.040-1").update(source_quote="Nobody may vend."))
        self.assertEqual(rc, 1); self.assertIn("quote-not-in-provision", codes)

    def test_quote_not_in_source_text(self):
        # still a substring of the provision, but the provided source text does not contain it
        d = self.golden_copy(); prov = load(d + "/provisions.json")
        next(p for p in prov if p["id"] == "9.10.040")["text"] += " Extra words."
        dump(d + "/provisions.json", prov)
        rc, codes = self.v(d, "segment", "actions.frozen.json"); self.assertEqual(rc, 1); self.assertIn("text-not-in-source", codes)

    def test_dangling_edge(self):
        rc, codes = self.mutate("dependencies.json", lambda d: d["edges"][0].update(to="A-9.99.999-1"))
        self.assertEqual(rc, 1); self.assertIn("dangling-edge", codes)

    def test_superseded_record_in_graph(self):
        def f(d):
            d["edges"].append({"id": "E-900", "from": "A-9.10.100-1", "to": "A-9.10.120.B-1", "type": "enforcement", "basis": "explicit",
                               "confidence": "high", "evidence": "x", "status": "accepted"})
            d["nodes"].append("A-9.10.100-1")
        rc, codes = self.mutate("dependencies.json", f); self.assertEqual(rc, 1); self.assertIn("excluded-node-in-graph", codes)

    def test_missing_triggers_edge(self):
        def f(d):
            d["edges"] = [e for e in d["edges"] if not (e["type"] == "triggers" and e["to"] == "A-9.10.130.B-1")]
        rc, codes = self.mutate("dependencies.json", f); self.assertEqual(rc, 1); self.assertIn("missing-triggers-edge", codes)

    def test_bad_modality_is_schema_error(self):
        rc, codes = self.mutate("actions.frozen.json", lambda d: self.rec(d, "A-9.10.040-1").update(modality="must"))
        self.assertEqual(rc, 1); self.assertIn("schema", codes)

    def test_unknown_actor(self):
        rc, codes = self.mutate("actions.frozen.json", lambda d: self.rec(d, "A-9.10.040-1")["actor"].update(id="ACT-nobody"))
        self.assertEqual(rc, 1); self.assertIn("unknown-actor", codes)

    def test_silent_orphan_missing_actor_without_flag(self):
        rc, codes = self.mutate("actions.pre-resolution.json", lambda d: self.rec(d, "A-9.10.040-1").update(actor=None), "extract", "actions.pre-resolution.json")
        self.assertEqual(rc, 1); self.assertIn("silent-orphan", codes)

    def test_flag_without_orphan_entry(self):
        def f(d):
            r = self.rec(d, "A-9.10.040-1"); r["orphan_flags"] = ["O-VERB"]; r["status"] = "orphan"
        rc, codes = self.mutate("actions.pre-resolution.json", f, "extract", "actions.pre-resolution.json")
        self.assertEqual(rc, 1); self.assertIn("flag-without-orphan", codes)

    def test_open_orphan_blocks_freeze(self):
        rc, codes = self.mutate("orphans.json", lambda d: d[0].update(status="open"), "frozen")
        self.assertEqual(rc, 1); self.assertIn("open-orphan", codes)

    def test_pre_resolution_records_cannot_freeze(self):
        rc, codes = self.v(GOLD, "frozen", "actions.pre-resolution.json")
        self.assertEqual(rc, 1); self.assertIn("open-record", codes)

    def test_uncovered_operative_provision(self):
        def f(d):
            p = next(x for x in d if x["id"] == "9.10.140.B"); p["record_ids"] = []; p["attaches_to"] = []
        d = self.golden_copy(); prov = load(d + "/provisions.json"); f(prov); dump(d + "/provisions.json", prov)
        acts = load(d + "/actions.frozen.json"); acts = [r for r in acts if r["id"] != "A-9.10.140.B-1"]; dump(d + "/actions.frozen.json", acts)
        rc, codes = self.v(d, "extract", "actions.frozen.json"); self.assertEqual(rc, 1); self.assertIn("uncovered", codes)

    def test_dropped_class_blocks_extract(self):
        rc, codes = self.mutate("provisions.json", lambda d: d[0].update({"class": None}), "extract", "actions.frozen.json")
        self.assertEqual(rc, 1); self.assertIn("unclassified", codes)


if __name__ == "__main__":
    unittest.main()
