import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


class OrphanTableTests(TmpCase):
    def table(self, *extra, d=GOLD):
        p = run("orphan_table.py", d, "--status", "resolved", *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_groups_in_order_and_columns(self):
        t = self.table()
        self.assertLess(t.index("Missing signals"), t.index("Missing actors"))
        self.assertLess(t.index("Missing actors"), t.index("Everything else"))
        self.assertIn("| # | Provision | Quote | What the text doesn't say | My best guess (basis) | Options |", t)
        for o in load(GOLD + "/orphans.json"):
            row = f"| {o['id']} |"
            if o["status"] == "resolved":
                self.assertIn(row, t)
            else:
                self.assertNotIn(row, t)          # known gaps are not listed under --status resolved

    def test_options_are_lettered(self):
        t = self.table()
        self.assertIn("a) Filing of the application<br>b) Request by the director<br>c) Other", t)

    def test_quote_is_shortened_but_a_prefix(self):
        long = " ".join(f"w{i}" for i in range(60))
        d = self.golden_copy(); o = load(d + "/orphans.json"); o[0]["quote"] = long; dump(d + "/orphans.json", o)
        t = self.table("--max-words", "10", d=d)
        self.assertIn("“w0 w1 w2 w3 w4 w5 w6 w7 w8 w9 …”", t)

    def test_pipes_escaped_and_empty_status(self):
        d = self.golden_copy(); o = load(d + "/orphans.json"); o[0]["missing"] = "a|b"; dump(d + "/orphans.json", o)
        self.assertIn("a\\|b", self.table(d=d))
        p = run("orphan_table.py", GOLD, "--status", "open")
        self.assertIn("No open orphans", p.stdout)


if __name__ == "__main__":
    unittest.main()
