import os, sys, unittest, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
LONG = "The quick brown fox jumps over the lazy dog. " * 8


def make_docx(path, paras, table=None):
    body = "".join(f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>' for p in paras)
    if table:
        body += "<w:tbl>" + "".join("<w:tr>" + "".join(f"<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>" for c in row) + "</w:tr>" for row in table) + "</w:tbl>"
    xml = f'<?xml version="1.0"?><w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


class IngestTests(TmpCase):
    def ing(self, src):
        out = self.tmp + "/o"
        p = run("ingest.py", src, "--out", out)
        return p, out

    def test_text_roundtrip_and_provenance(self):
        p, out = self.ing(SOURCE)
        self.assertEqual(p.returncode, 0, p.stderr)
        prov = load(out + "/provenance.json")
        self.assertEqual(prov["format"], "text"); self.assertEqual(prov["currency"]["supplement"], "3")
        self.assertEqual(len(prov["sha256"]), 64)

    def test_docx_paragraphs_and_tables(self):
        d = self.tmp + "/t.docx"
        make_docx(d, ["5.04.010 Revenue measure.", LONG, "(Ord. 1, 1977)."], table=[["Over", "Tax"], ["1", "$5"]])
        p, out = self.ing(d)
        self.assertEqual(p.returncode, 0, p.stderr)
        t = read(out + "/source.txt")
        self.assertIn("5.04.010 Revenue measure.\n\nThe quick", t)
        self.assertIn("| Over | Tax |", t); self.assertIn("| --- | --- |", t.replace("|  --- ", "| --- ").replace(" --- |", " --- |")) 

    def test_html_scripts_dropped_blocks_split(self):
        h = self.write("t.html", f"<html><script>var x=1;</script><body><p>5.04.010 Heading.</p><p>{LONG}</p></body></html>")
        p, out = self.ing(h)
        t = read(out + "/source.txt")
        self.assertNotIn("var x", t); self.assertIn("5.04.010 Heading.\n\nThe quick", t)

    def test_unsupported_and_missing_and_tiny(self):
        self.assertNotEqual(self.ing(self.write("x.rtf", LONG))[0].returncode, 0)
        self.assertNotEqual(self.ing(self.tmp + "/missing.txt")[0].returncode, 0)
        self.assertNotEqual(self.ing(self.write("tiny.txt", "hi"))[0].returncode, 0)

    def test_url_failure_gives_guidance(self):
        p, _ = self.ing("http://127.0.0.1:9/code")
        self.assertEqual(p.returncode, 2)
        self.assertIn("file", p.stderr)

    def test_nbsp_and_blank_runs_normalized(self):
        t = self.write("n.txt", "A B\n\n\n\n\n" + LONG)
        _, out = self.ing(t)
        s = read(out + "/source.txt")
        self.assertTrue(s.startswith("A B\n\nThe quick"))


if __name__ == "__main__":
    unittest.main()
