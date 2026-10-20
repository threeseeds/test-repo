import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *
sys.path.insert(0, SCRIPTS)
import report as R


class ReportTests(TmpCase):
    def setUp(self):
        super().setUp()
        self.out = self.tmp + "/rep"
        run("report.py", GOLD, "--actions", "actions.frozen.json", "--out", self.out, "--title", "Eastvale 9.10", check=True)

    def test_coverage_matches_golden(self):
        self.assertEqual(json.dumps(load(self.out + "/coverage.json"), sort_keys=True),
                         json.dumps(load(GOLD + "/coverage.json"), sort_keys=True))

    def test_first_order_sections(self):
        t = read(self.out + "/first-order-map.md")
        for h in ("## By section", "## By actor", "## By counterparty", "## By signal type", "## Actor x counterparty matrix",
                  "## Linked records", "## Attachments", "## Glossary", "## Orphan log", "## Known gaps", "## External references"):
            self.assertIn(h, t, h)
        self.assertIn("9.10.080.C-1", t)                      # the accepted known gap
        self.assertIn("external:Chapter 9.30", t)
        self.assertIn("2 excluded as duplicate/superseded", t)

    def test_every_live_record_appears_by_section(self):
        t = read(self.out + "/first-order-map.md").split("## By actor")[0]
        for r in load(GOLD + "/actions.frozen.json"):
            if "duplicate_of" not in r and "superseded_by" not in r:
                self.assertIn(r["id"][2:], t, r["id"])

    def test_second_order(self):
        t = read(self.out + "/second-order-map.md")
        self.assertIn("Renewal loop", t)
        self.assertIn("Revocation loop", t)
        self.assertIn("## Edges awaiting review", t)
        self.assertIn("unpaid fine", t)

    def test_cell_escapes_pipes_and_newlines(self):
        self.assertEqual(R.cell("a|b\nc"), "a\\|b c")


if __name__ == "__main__":
    unittest.main()
