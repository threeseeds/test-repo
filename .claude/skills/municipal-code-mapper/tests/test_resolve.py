import json, os, shutil, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


class ResolveTests(TmpCase):
    def setUp(self):
        super().setUp()
        self.d = self.tmp + "/run"
        os.makedirs(self.d)
        shutil.copy(GOLD + "/actions.pre-resolution.json", self.d + "/actions.json")
        for f in ("provisions.json", "orphans.json"):
            shutil.copy(GOLD + "/" + f, self.d)

    def go(self):
        return run("resolve.py", self.d)

    def test_reproduces_golden_frozen_map(self):
        p = self.go(); self.assertEqual(p.returncode, 0, p.stdout)
        got = {r["id"]: r for r in load(self.d + "/actions.frozen.json")}
        want = {r["id"]: r for r in load(GOLD + "/actions.frozen.json")}
        self.assertEqual(set(got), set(want))
        for rid, w in want.items():
            for k in w:
                if k != "resolution_note":
                    self.assertEqual(got[rid][k], w[k], (rid, k))
        self.assertIn("ORP-01", got["A-9.10.050.D-1"]["resolution_note"])
        self.assertIn("ORP-02", got["A-9.10.050.D-1"]["resolution_note"])      # two answers on one record are both kept

    def test_provision_attachments_recomputed(self):
        self.go()
        got = {p["id"]: p for p in load(self.d + "/provisions.frozen.json")}
        want = {p["id"]: p for p in load(GOLD + "/provisions.json")}
        for pid, w in want.items():
            self.assertEqual(got[pid]["attaches_to"], w["attaches_to"], pid)

    def test_frozen_output_passes_validate(self):
        self.go()
        shutil.copy(GOLD + "/actors.json", self.d)
        p = run("validate.py", self.d, "--stage", "frozen", "--actions", "actions.frozen.json", "--provisions", "provisions.frozen.json", "--source", SOURCE)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_inputs_unchanged_and_rerun_identical(self):
        before = read(self.d + "/actions.json")
        self.go(); first = read(self.d + "/actions.frozen.json")
        self.go()
        self.assertEqual(read(self.d + "/actions.json"), before)
        self.assertEqual(read(self.d + "/actions.frozen.json"), first)

    def refuses(self, mutate, needle):
        o = load(self.d + "/orphans.json"); mutate(o); dump(self.d + "/orphans.json", o)
        p = self.go(); self.assertEqual(p.returncode, 1, p.stdout); self.assertIn(needle, p.stdout)
        self.assertFalse(os.path.exists(self.d + "/actions.frozen.json"))

    def test_refuses_open_orphan(self):
        self.refuses(lambda o: o[0].update(status="open"), "still open")

    def test_refuses_unknown_record_and_field(self):
        self.refuses(lambda o: o[0]["resolution"]["patch"].update({"A-9.99.999-1": {"status": "resolved"}}), "unknown record")

    def test_refuses_bad_patch_field(self):
        self.refuses(lambda o: o[0]["resolution"]["patch"]["A-9.10.050.D-1"].update(colour="red"), "not a record field")

    def test_refuses_record_left_orphan(self):
        self.refuses(lambda o: o[1]["resolution"]["patch"]["A-9.10.050.D-1"].update(status="orphan"), "still an orphan")

    def test_refuses_resolved_without_clearing_flags(self):
        self.refuses(lambda o: o[1]["resolution"]["patch"]["A-9.10.050.D-1"].update(orphan_flags=["O-ACT"]), "still carries flags")


if __name__ == "__main__":
    unittest.main()
