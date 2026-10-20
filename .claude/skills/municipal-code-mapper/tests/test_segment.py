import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

KEYS = ("id", "section", "chapter", "division", "label", "heading", "article", "text", "history")
SYN = """Chapter 1.01 FIRST CHAPTER

1.01.010 Alpha.

The alpha rule applies.

(Ord. 1, 2000).

1.01.020 Beta.

A. First thing.

B. Second thing; C. Third thing run on here.

D. Fourth thing.

(Ord. 2, 2000).

Chapter 2.02 SECOND CHAPTER

2.02.010 Gamma.

The gamma rule applies.

(Ord. 3, 2000).
"""


class SegmentTests(TmpCase):
    def seg(self, src, *extra):
        out = os.path.join(self.tmp, "seg")
        p = run("segment.py", src, "--out", out, *extra)
        return p, out

    def test_fixture_matches_golden(self):
        p, out = self.seg(SOURCE)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        got, want = load(out + "/provisions.json"), load(GOLD + "/provisions.json")
        self.assertEqual(len(got), 40)
        self.assertEqual([{k: x[k] for k in KEYS} for x in got], [{k: x[k] for k in KEYS} for x in want])

    def test_ingest_then_segment_is_identical(self):
        run("ingest.py", SOURCE, "--out", self.tmp + "/ing", check=True)
        _, out = self.seg(self.tmp + "/ing/source.txt")
        want = load(GOLD + "/provisions.json")
        self.assertEqual([x["id"] for x in load(out + "/provisions.json")], [x["id"] for x in want])

    def test_reserved_and_toc_dedup(self):
        _, out = self.seg(SOURCE)
        by = {p["id"]: p for p in load(out + "/provisions.json")}
        self.assertEqual(by["9.10.150"]["text"], "Reserved.")
        self.assertEqual(by["9.10.010"]["text"].startswith("The purpose"), True)   # body wins over table-of-contents entry

    def test_noise_is_removed_and_nothing_unassigned(self):
        _, out = self.seg(SOURCE)
        r = load(out + "/segment-report.json")
        self.assertEqual(r["unassigned_body_lines"], [])
        self.assertGreater(r["line_stats"]["noise"], 0)
        for p in load(out + "/provisions.json"):
            self.assertNotIn("Created:", p["text"]); self.assertNotIn("Supp. No.", p["text"])

    def test_skipped_label_starts_new_provision_with_warning(self):
        p, out = self.seg(self.write("syn.txt", SYN))
        ids = [x["id"] for x in load(out + "/provisions.json")]
        self.assertIn("1.01.020.D", ids)
        self.assertTrue(any("skips" in w for w in load(out + "/segment-report.json")["warnings"]))

    def test_editors_notes_after_history_are_not_provision_text(self):
        syn = SYN.replace("(Ord. 1, 2000).", "(Ord. 1, 2000).\n\nEditor's note(s)—Ord. 1 repealed the former section.")
        _, out = self.seg(self.write("syn.txt", syn))
        by = {p["id"]: p for p in load(out + "/provisions.json")}
        self.assertEqual(by["1.01.010"]["text"], "The alpha rule applies.")
        self.assertIn("repealed the former", load(out + "/notes.json")["1.01.010"][0])
        p = run("validate.py", out, "--stage", "segment", "--source", self.tmp + "/syn.txt")
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_chapter_filter(self):
        _, out = self.seg(self.write("syn.txt", SYN), "--chapters", "2.02")
        self.assertEqual({x["chapter"] for x in load(out + "/provisions.json")}, {"2.02"})
        _, out = self.seg(self.write("syn.txt", SYN), "--chapters", "1.01:2.02")
        self.assertEqual({x["chapter"] for x in load(out + "/provisions.json")}, {"1.01", "2.02"})

    def test_strict_fails_on_empty_non_reserved_section(self):
        bad = SYN.replace("1.01.010 Alpha.\n\nThe alpha rule applies.\n\n(Ord. 1, 2000).", "1.01.010 Alpha.")
        p, _ = self.seg(self.write("bad.txt", bad), "--strict")
        self.assertEqual(p.returncode, 1)

    def test_ids_are_stable_across_runs(self):
        _, a = self.seg(SOURCE); first = load(a + "/provisions.json")
        _, b = self.seg(SOURCE); self.assertEqual(first, load(b + "/provisions.json"))

    def test_real_title5_if_available(self):
        path = os.environ.get("TITLE5_TEXT")
        if not path or not os.path.exists(path):
            self.skipTest("set TITLE5_TEXT to the extracted Brisbane Title 5 text to run this")
        p, out = self.seg(path, "--strict")
        self.assertEqual(p.returncode, 0, p.stdout)
        r = load(out + "/segment-report.json")
        self.assertEqual(r["sections_found"], 227)
        self.assertEqual(len(r["chapters"]), 18)
        self.assertEqual(r["per_chapter"]["5.20"], 40)
        self.assertEqual(r["per_chapter"]["5.32"], 38)
        self.assertEqual(r["empty_provisions"], [])
        v = run("validate.py", out, "--stage", "segment", "--source", path)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertEqual(len(load(out + "/notes.json")), 3)


if __name__ == "__main__":
    unittest.main()
