import json, os, shutil, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


def load_analysis(d):
    run("graph.py", d, "--actions", "actions.frozen.json", "--analysis-out", "a.json", check=True)
    return load(d + "/a.json")


def load_analysis_edges(deps):
    return len([e for e in deps["edges"] if e["status"] != "rejected"])


class DepsCase(TmpCase):
    def setUp(self):
        super().setUp()
        self.d = self.tmp + "/run"
        os.makedirs(self.d)
        shutil.copy(GOLD + "/actions.frozen.json", self.d)
        shutil.copy(FIX + "/dependencies.jsonl", self.d)

    def build(self):
        return run("build_deps.py", self.d)

    def sheet(self):
        return [l for l in read(self.d + "/dependencies.jsonl").splitlines() if l.strip() and not l.startswith("#")]

    def set_sheet(self, lines):
        with open(self.d + "/dependencies.jsonl", "w") as f:
            f.write("\n".join(lines) + "\n")


class BuildDepsTests(DepsCase):
    def test_reproduces_golden_graph(self):
        p = self.build(); self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(load(self.d + "/dependencies.json"), load(GOLD + "/dependencies.json"))

    def test_output_passes_validate_deps_stage(self):
        self.build()
        shutil.copy(GOLD + "/provisions.json", self.d); shutil.copy(GOLD + "/actors.json", self.d); shutil.copy(GOLD + "/orphans.json", self.d)
        p = run("validate.py", self.d, "--stage", "deps", "--actions", "actions.frozen.json", "--source", SOURCE)
        self.assertEqual(p.returncode, 0, p.stdout)

    def fails(self, edit, needle):
        shutil.copy(FIX + "/dependencies.jsonl", self.d)
        lines = self.sheet(); edit(lines); self.set_sheet(lines)
        p = self.build(); self.assertEqual(p.returncode, 1, p.stdout); self.assertIn(needle, p.stdout)
        self.assertFalse(os.path.exists(self.d + "/dependencies.json"))

    def test_unknown_record(self):
        self.fails(lambda L: L.append(json.dumps({"from": "9.99.999-1", "to": "9.10.040-1", "type": "reference", "basis": "explicit", "conf": "high", "ev": "x"})), "unknown record")

    def test_excluded_record_cannot_be_a_node(self):
        self.fails(lambda L: L.append(json.dumps({"from": "9.10.100-1", "to": "9.10.040-1", "type": "reference", "basis": "explicit", "conf": "high", "ev": "x"})), "duplicate/superseded")

    def test_self_loop(self):
        self.fails(lambda L: L.append(json.dumps({"from": "9.10.040-1", "to": "9.10.040-1", "type": "reference", "basis": "explicit", "conf": "high", "ev": "x"})), "self-loop")

    def test_triggers_cannot_be_hand_written(self):
        self.fails(lambda L: L.append(json.dumps({"from": "9.10.050.A-1", "to": "9.10.050.C-1", "type": "triggers", "basis": "explicit", "conf": "high", "ev": "x"})), "derived from signal refs")

    def test_duplicate_edge_and_missing_evidence_and_bad_enum(self):
        self.fails(lambda L: L.append(L[0]), "duplicate edge")
        self.fails(lambda L: L.__setitem__(0, json.dumps({**json.loads(L[0]), "ev": " "})), "evidence is required")
        self.fails(lambda L: L.__setitem__(0, json.dumps({**json.loads(L[0]), "type": "causes"})), "bad type")
        self.fails(lambda L: L.__setitem__(0, json.dumps({**json.loads(L[0]), "conf": "certain"})), "bad conf")

    def test_status_defaults_and_ids_stable(self):
        self.build()
        first = load(self.d + "/dependencies.json")
        for e in first["edges"]:
            self.assertEqual(e["status"], "accepted" if e["basis"] == "explicit" else "pending_review")
        self.build()
        self.assertEqual(load(self.d + "/dependencies.json"), first)

    def test_external_stub_and_short_ids(self):
        lines = self.sheet()
        lines.append(json.dumps({"from": "external:Chapter 1.14", "to": "9.10.120.B-1", "type": "reference", "basis": "inferred", "conf": "low", "ev": "x"}))
        self.set_sheet(lines)
        self.assertEqual(self.build().returncode, 0)
        g = load(self.d + "/dependencies.json")
        self.assertIn("external:Chapter 1.14", g["nodes"])


class EdgeReviewTests(DepsCase):
    def setUp(self):
        super().setUp()
        self.build()

    def test_table_lists_only_pending_grouped_by_type(self):
        p = run("edge_review.py", self.d, "table"); self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("4 edges awaiting review", p.stdout)
        self.assertIn("### exception-of: 2", p.stdout); self.assertIn("### condition-precedent: 1", p.stdout)
        self.assertIn("| E-", p.stdout); self.assertIn("accept / reject", p.stdout)

    def test_apply_writes_decisions_into_sheet_and_survives_rebuild(self):
        pend = [e for e in load(self.d + "/dependencies.json")["edges"] if e["status"] == "pending_review"]
        a, b = pend[0]["id"], pend[1]["id"]
        p = run("edge_review.py", self.d, "apply", "--accept", a, "--reject", b); self.assertEqual(p.returncode, 0, p.stderr)
        self.build()
        edges = {e["id"]: e for e in load(self.d + "/dependencies.json")["edges"]}
        self.assertEqual(edges[a]["status"], "accepted"); self.assertEqual(edges[b]["status"], "rejected")
        self.assertEqual(sum(1 for e in edges.values() if e["status"] == "pending_review"), 2)

    def test_rejected_edge_is_ignored_by_graph_analysis(self):
        deps = load(self.d + "/dependencies.json")
        inf = next(e for e in deps["edges"] if e["type"] == "condition-precedent" and e["status"] == "pending_review")
        before = len(load_analysis(self.d)["with_inferred"]["cycles"][0])
        run("edge_review.py", self.d, "apply", "--reject", inf["id"], check=True); self.build()
        after = load_analysis(self.d)["with_inferred"]
        self.assertEqual(after["edges"], load_analysis_edges(deps) - 1)
        run("graph.py", self.d, "--actions", "actions.frozen.json", "--mermaid", "g.mmd", check=True)
        self.assertNotIn("condition-precedent (inferred)", read(self.d + "/g.mmd"))

    def test_accept_all(self):
        run("edge_review.py", self.d, "apply", "--accept-all", check=True); self.build()
        self.assertEqual([e for e in load(self.d + "/dependencies.json")["edges"] if e["status"] == "pending_review"], [])
        p = run("edge_review.py", self.d, "table"); self.assertIn("No edges awaiting review", p.stdout)

    def test_unknown_edge_and_derived_edge_errors(self):
        p = run("edge_review.py", self.d, "apply", "--accept", "E-999"); self.assertNotEqual(p.returncode, 0)
        derived = load(self.d + "/dependencies.json")["edges"][0]["id"]
        p = run("edge_review.py", self.d, "apply", "--reject", derived); self.assertNotEqual(p.returncode, 0)
        self.assertIn("derived", p.stderr + p.stdout)


if __name__ == "__main__":
    unittest.main()
