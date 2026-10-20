import json, os, re, shutil, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *


def embedded(page):
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S)
    return json.loads(m.group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))


class GraphHtmlTests(TmpCase):
    def setUp(self):
        super().setUp()
        self.d = self.tmp + "/run"
        os.makedirs(self.d)
        shutil.copy(GOLD + "/actions.frozen.json", self.d)
        shutil.copy(GOLD + "/provisions.json", self.d + "/provisions.frozen.json")
        shutil.copy(GOLD + "/dependencies.json", self.d)
        shutil.copy(GOLD + "/actors.json", self.d)

    def gen(self, *extra):
        p = run("graph_html.py", self.d, "--title", "Eastvale Map & Co", "--subtitle", "fixture", *extra)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return read(self.d + "/dependency-graph.html")

    def test_page_contains_all_records_and_edges(self):
        page = self.gen(); data = embedded(page)
        live = [r for r in load(GOLD + "/actions.frozen.json") if "duplicate_of" not in r and "superseded_by" not in r]
        self.assertEqual(len([n for n in data["nodes"] if n["ch"] != "external"]), len(live))
        self.assertEqual(len(data["edges"]), len(load(GOLD + "/dependencies.json")["edges"]))
        self.assertEqual(data["counts"]["nodes"], len(data["nodes"]))
        self.assertEqual(data["counts"]["stated"] + data["counts"]["inferred"], data["counts"]["edges"])
        self.assertEqual(data["counts"]["pending"], 4)
        self.assertEqual(len(data["analysis"]["explicit_only"]["cycles"]), 2)

    def test_title_escaped_and_placeholders_replaced(self):
        page = self.gen()
        self.assertIn("<title>Eastvale Map &amp; Co</title>", page)
        self.assertNotIn("__DATA__", page); self.assertNotIn("__TITLE__", page)

    def test_script_breakout_in_text_is_neutralized(self):
        acts = load(self.d + "/actions.frozen.json")
        acts[0]["source_quote"] = acts[0]["source_quote"] + " </script><b>x</b> <!-- y"
        dump(self.d + "/actions.frozen.json", acts)
        page = self.gen()
        self.assertEqual(page.count("</script>"), 2)               # the data block and the code block only
        self.assertIn("</script><b>x</b>", embedded(page)["nodes"][0]["quote"])

    def test_external_stub_becomes_a_node(self):
        data = embedded(self.gen())
        self.assertIn("external:Chapter 9.30", [n["id"] for n in data["nodes"]])

    def test_rejected_edges_are_not_drawn(self):
        deps = load(self.d + "/dependencies.json"); deps["edges"][-1]["status"] = "rejected"; dump(self.d + "/dependencies.json", deps)
        data = embedded(self.gen())
        self.assertEqual(data["counts"]["edges"], len(deps["edges"]) - 1)
        self.assertNotIn(deps["edges"][-1]["id"], [e["id"] for e in data["edges"] if e["st"] != "rejected"])


if __name__ == "__main__":
    unittest.main()
