import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *
sys.path.insert(0, SCRIPTS)
import segment_cfr as C

PROFILE = os.path.join(SKILL, "profiles", "cfr.json")
REG = """§ 98.10 Enforcement of the findings.
(a) First paragraph of another part.
(Authority: 20 U.S.C. 1221)

Subpart A—General

§ 99.1 What is this part about?
(a) A thing applies if—
(1) It is a school; or
(2) It is a district.
(b) This part does not apply to a school solely because the school gets help.

Office of the Secretary, Education

§ 99.3

§ 99.3 What definitions apply to these
regulations?
The following definitions apply to
this part:
Act means the Family Educational
Rights Act.
(Authority: 20 U.S.C. 1232g)

Dates of attendance. (a) The term
means the period a student attends or attended a school.
(b) The term does not include daily records.
(Authority: 20 U.S.C. 1232g)

Party means an individual, agency,
institution, or organization. [53 FR 11943, Apr. 11, 1988]

Subpart B—What Rights Exist
For Parents?

§ 99.2 What can happen?
(a) The agency may disclose information without consent if the disclosure meets
one or more of the following conditions:
(1)(i)(A) The disclosure is to other officials within the agency.
(B) A contractor may be considered an official under this paragraph provided that the party—
(1) Performs a service for which the agency would otherwise use employees;
(2) Is under direct control of the agency; and
(3) Is subject to the requirements of § 99.33(a) governing use and
redisclosure of information.
(ii) The agency must use reasonable methods to ensure officials get only the records they need under paragraph
(a)(1)(i)(A) of this section.
(2) The disclosure is to officials of another school.
(b) The agency shall keep a record. In the case of an
edu-

265

VerDate Sep<11>2014

14:33 Jan 08, 2026

Jkt 265143

PO 00000

cational program, the record must be kept for five years.
(b) of this section

NOTE TO § 99.2: This note is not part of the rule and
continues on another line.
(Authority: 20 U.S.C. 1232g)
[53 FR 11943, Apr. 11, 1988, as amended at 61
FR 59295, Nov. 21, 1996]

§ 99.4 What are the letters?
(a) Item a.
(b) Item b.
(c) Item c.
(d) Item d.
(e) Item e.
(f) Item f.
(g) Item g.
(h) Item h.
(i) Item i, which is a letter and not a roman numeral.
(j) Item j.

APPENDIX A TO PART 99—CRIMES OF VIOLENCE
Arson is a crime.
"""


class CfrTests(TmpCase):
    def seg(self, *extra, text=REG):
        src = self.write("reg.txt", text)
        out = self.tmp + "/out"
        p = run("segment.py", src, "--out", out, "--profile", PROFILE, *extra)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return {x["id"]: x for x in load(out + "/provisions.json")}, out

    def test_label_placement_rules(self):
        self.assertEqual(C.place([], "a"), ["a"])
        self.assertEqual(C.place(["a", "1", "i"], "A"), ["a", "1", "i", "A"])
        self.assertEqual(C.place(["a", "1", "i", "B"], "ii"), ["a", "1", "ii"])      # back up a level
        self.assertEqual(C.place(["a", "1"], "i"), ["a", "1", "i"])                    # roman as first child
        self.assertEqual(C.place(["h", "1"], "i"), ["i"])                              # letter i after h, not a roman
        self.assertIsNone(C.place(["a"], "c"))                                         # skipped (b)

    def test_sections_headings_and_division(self):
        p, _ = self.seg()
        self.assertEqual({x["section"] for x in p.values()}, {"98.10", "99.1", "99.3", "99.2", "99.4"})
        self.assertEqual(p["99.3"]["heading"], "What definitions apply to these regulations")
        self.assertEqual(p["99.1.a"]["division"], "A")
        self.assertEqual(p["99.2.a"]["division"], "B")             # subpart title spread over two lines was consumed
        self.assertNotIn("For Parents", " ".join(x["text"] for x in p.values()))

    def test_nested_paths_and_chain_labels(self):
        p, _ = self.seg()
        for pid in ("99.2.a", "99.2.a.1.i.A", "99.2.a.1.i.B", "99.2.a.1.i.B.1", "99.2.a.1.i.B.2", "99.2.a.1.i.B.3", "99.2.a.1.ii", "99.2.a.2"):
            self.assertIn(pid, p)
        self.assertTrue(p["99.2.a.1.i.B"]["text"].startswith("A contractor may be considered"))
        self.assertEqual(p["99.2.a.1.i.B.1"]["text"], "Performs a service for which the agency would otherwise use employees;")

    def test_wrapped_lines_are_joined_and_references_are_not_labels(self):
        p, _ = self.seg()
        self.assertIn("under paragraph (a)(1)(i)(A) of this section", p["99.2.a.1.ii"]["text"])
        self.assertNotIn("99.2.a.1.ii.A", p)

    def test_hyphen_split_across_page_furniture_is_rejoined(self):
        p, out = self.seg()
        self.assertIn("In the case of an educational program, the record must be kept for five years.", p["99.2.b"]["text"])
        self.assertTrue(any("educational" in w for w in load(out + "/segment-report.json")["warnings"]))

    def test_unlabeled_continuation_starting_with_label_syntax_stays_in_text(self):
        p, _ = self.seg()
        self.assertTrue(p["99.2.b"]["text"].endswith("(b) of this section"))

    def test_letter_i_after_h_is_a_sibling(self):
        p, _ = self.seg()
        self.assertIn("99.4.h", p); self.assertIn("99.4.i", p); self.assertIn("99.4.j", p)
        self.assertEqual(p["99.4.i"]["text"], "Item i, which is a letter and not a roman numeral.")

    def test_definitions_split_by_term_with_inline_label(self):
        p, _ = self.seg()
        for pid in ("99.3.act", "99.3.dates-of-attendance", "99.3.dates-of-attendance.a", "99.3.dates-of-attendance.b", "99.3.party"):
            self.assertIn(pid, p)
        self.assertEqual(p["99.3"]["text"], "The following definitions apply to this part:")
        self.assertTrue(p["99.3.act"]["text"].startswith("Act means the Family Educational Rights Act"))

    def test_history_and_notes_are_not_provision_text(self):
        p, out = self.seg()
        self.assertNotIn("Authority", p["99.2.b"]["text"]); self.assertNotIn("NOTE", p["99.2.b"]["text"])
        self.assertIn("20 U.S.C. 1232g", p["99.2.b"]["history"]); self.assertIn("53 FR 11943", p["99.2.b"]["history"])
        self.assertIn("This note is not part of the rule", load(out + "/notes.json")["99.2"][0])

    def test_appendix_stops_the_parse(self):
        p, out = self.seg()
        self.assertNotIn("Arson", " ".join(x["text"] for x in p.values()))
        self.assertTrue(any("appendix marker" in w for w in load(out + "/segment-report.json")["warnings"]))

    def test_scope_filters(self):
        p, _ = self.seg("--chapters", "99.1:99.2")
        self.assertEqual({x["section"] for x in p.values()}, {"99.1", "99.2"})
        p, _ = self.seg("--chapters", "99.2", "--only", "99.2:a.1")
        self.assertIn("99.2.a", p)                                  # ancestor kept
        self.assertIn("99.2.a.1.i.B.3", p)
        self.assertNotIn("99.2.a.2", p); self.assertNotIn("99.2.b", p)

    def test_clean_source_validates_provision_text(self):
        p, out = self.seg()
        v = run("validate.py", out, "--stage", "segment", "--source", out + "/source.clean.txt")
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertNotIn("VerDate", read(out + "/source.clean.txt"))

    def test_real_part_99_if_available(self):
        path = os.environ.get("FERPA_PDF")
        if not path or not os.path.exists(path):
            self.skipTest("set FERPA_PDF to the 34 CFR Part 99 PDF to run this")
        ing = self.tmp + "/ing"
        run("ingest.py", path, "--out", ing, check=True)
        out = self.tmp + "/seg"
        run("segment.py", ing + "/source.txt", "--out", out, "--profile", PROFILE, "--chapters", "99.1:99.5,99.7,99.30:99.33", "--only", "99.31:a.1", check=True)
        ids = {x["id"] for x in load(out + "/provisions.json")}
        for pid in ("99.31.a.1.i.B.1", "99.31.a.1.i.B.2", "99.31.a.1.i.B.3", "99.31.a.1.ii", "99.7.a.3.iii", "99.33.a.1", "99.33.a.2", "99.32.d.2"):
            self.assertIn(pid, ids)
        v = run("validate.py", out, "--stage", "segment", "--source", out + "/source.clean.txt")
        self.assertEqual(v.returncode, 0, v.stdout)


if __name__ == "__main__":
    unittest.main()
