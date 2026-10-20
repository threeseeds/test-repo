import json, os, shutil, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


def norm(r):
    r = json.loads(json.dumps(r))
    r["attachments"] = sorted(r["attachments"], key=lambda a: (a["kind"], a["provision"]))
    return r


class ExpandTests(TmpCase):
    def setUp(self):
        super().setUp()
        self.run_dir = self.tmp + "/run"
        run("segment.py", SOURCE, "--out", self.run_dir, check=True)
        for f in ("extraction.jsonl", "classification.json"):
            shutil.copy(os.path.join(FIX, f), self.run_dir)
        shutil.copy(GOLD + "/actors.json", self.run_dir)

    def sheet_lines(self):
        return [l for l in read(self.run_dir + "/extraction.jsonl").splitlines() if l.strip() and not l.startswith("#")]

    def set_sheet(self, lines):
        with open(self.run_dir + "/extraction.jsonl", "w") as f:
            f.write("\n".join(lines) + "\n")

    def test_sheet_expands_to_golden_records(self):
        run("expand.py", self.run_dir, check=True)
        got = {r["id"]: norm(r) for r in load(self.run_dir + "/actions.json")}
        want = {r["id"]: norm(r) for r in load(GOLD + "/actions.pre-resolution.json")}
        self.assertEqual(got, want)

    def test_provisions_classified_and_linked(self):
        run("expand.py", self.run_dir, check=True)
        got = {p["id"]: p for p in load(self.run_dir + "/provisions.json")}
        want = {p["id"]: p for p in load(GOLD + "/provisions.json")}
        for pid, w in want.items():
            self.assertEqual((got[pid]["class"], got[pid]["record_ids"]), (w["class"], w["record_ids"]), pid)
        # golden provisions are frozen-state: they omit the two records a resolution excludes
        excluded = {"A-9.10.070.B-1", "A-9.10.100-1"}
        for pid, w in want.items():
            self.assertEqual(set(got[pid]["attaches_to"]) - excluded, set(w["attaches_to"]), pid)

    def test_expanded_run_passes_validate_extract(self):
        run("expand.py", self.run_dir, check=True)
        shutil.copy(GOLD + "/orphans.json", self.run_dir)
        p = run("validate.py", self.run_dir, "--stage", "extract", "--source", SOURCE)
        self.assertEqual(p.returncode, 0, p.stdout)

    def fails(self, mutate, needle):
        lines = self.sheet_lines(); mutate(lines); self.set_sheet(lines)
        before = os.path.exists(self.run_dir + "/actions.json")
        p = run("expand.py", self.run_dir)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn(needle, p.stdout)
        self.assertEqual(os.path.exists(self.run_dir + "/actions.json"), before)   # nothing written on error

    def test_quote_must_be_verbatim(self):
        self.fails(lambda L: L.__setitem__(0, L[0].replace("No person shall", "Nobody shall")), "verbatim substring")

    def test_unknown_actor(self):
        self.fails(lambda L: L.__setitem__(0, L[0].replace("ACT-any-person", "ACT-nobody")), "not in actors.json")

    def test_unknown_provision(self):
        self.fails(lambda L: L.__setitem__(0, L[0].replace('"p": "9.10.040"', '"p": "9.99.999"')), "unknown provision")

    def test_dangling_reference(self):
        self.fails(lambda L: L.__setitem__(2, L[2].replace('"ref": "9.10.050.A"', '"ref": "9.10.050.A#9"')), "does not exist")

    def test_invalid_json_line(self):
        lines = self.sheet_lines(); lines[1] = lines[1][:-5]; self.set_sheet(lines)
        p = run("expand.py", self.run_dir)
        self.assertNotEqual(p.returncode, 0); self.assertIn("invalid JSON", p.stdout + p.stderr)

    def test_shorthand_inferred_actor(self):
        run("expand.py", self.run_dir, check=True)
        rec = next(r for r in load(self.run_dir + "/actions.json") if r["id"] == "A-9.10.040-1")
        self.assertEqual(rec["counterparty"], {"id": "ACT-public", "text": None, "confidence": "inferred"})

    def test_exemption_populates_exceptions_and_kind_override_works(self):
        c = load(self.run_dir + "/classification.json")
        c["classes"]["9.10.030"] = "exemption"
        c["attach"]["9.10.030"] = {"to": ["9.10.040"], "summary": "farmers' markets are exempt"}
        c["attach"]["9.10.080.D"] = {"to": ["9.10.080.A"], "kind": "fee", "summary": "x"}    # operative provision, kind forced
        dump(self.run_dir + "/classification.json", c)
        run("expand.py", self.run_dir, check=True)
        recs = {r["id"]: r for r in load(self.run_dir + "/actions.json")}
        self.assertEqual(recs["A-9.10.040-1"]["exceptions"], ["9.10.030"])
        self.assertNotIn("exemption", [a["kind"] for a in recs["A-9.10.040-1"]["attachments"]])
        self.assertIn(("fee", "9.10.080.D"), [(a["kind"], a["provision"]) for a in recs["A-9.10.080.A-1"]["attachments"]])
        prov = {p["id"]: p for p in load(self.run_dir + "/provisions.json")}
        self.assertIn("A-9.10.040-1", prov["9.10.030"]["attaches_to"])

    def test_legal_effect_class_attaches(self):
        c = load(self.run_dir + "/classification.json")
        c["classes"]["9.10.160"] = "legal_effect"
        c["attach"]["9.10.160"] = {"to": ["9.10.040", "chapter"], "summary": "severability"}
        dump(self.run_dir + "/classification.json", c)
        run("expand.py", self.run_dir, check=True)
        recs = {r["id"]: r for r in load(self.run_dir + "/actions.json")}
        self.assertIn(("legal_effect", "9.10.160"), [(a["kind"], a["provision"]) for a in recs["A-9.10.040-1"]["attachments"]])
        shutil.copy(GOLD + "/orphans.json", self.run_dir)
        v = run("validate.py", self.run_dir, "--stage", "extract")
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_attach_can_target_a_single_record(self):
        c = load(self.run_dir + "/classification.json")
        c["attach"]["9.10.050.B"]["to"] = ["A-9.10.060.C-2"]
        dump(self.run_dir + "/classification.json", c)
        run("expand.py", self.run_dir, check=True)
        recs = {r["id"]: r for r in load(self.run_dir + "/actions.json")}
        self.assertIn("fee", [a["kind"] for a in recs["A-9.10.060.C-2"]["attachments"]])
        self.assertNotIn("fee", [a["kind"] for a in recs["A-9.10.060.C-1"]["attachments"]])
        c["attach"]["9.10.050.B"]["to"] = ["A-9.10.999-1"]
        dump(self.run_dir + "/classification.json", c)
        p = run("expand.py", self.run_dir); self.assertEqual(p.returncode, 1); self.assertIn("unknown record", p.stdout)

    def test_attach_to_provision_without_records_is_an_error(self):
        c = load(self.run_dir + "/classification.json"); c["attach"]["9.10.050.B"]["to"] = ["9.10.150"]; dump(self.run_dir + "/classification.json", c)
        p = run("expand.py", self.run_dir); self.assertEqual(p.returncode, 1); self.assertIn("has no records", p.stdout)


if __name__ == "__main__":
    unittest.main()
