import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *
sys.path.insert(0, SCRIPTS)
import graph as G


def srt(x):
    return sorted(sorted(c) for c in x)


class GraphTests(TmpCase):
    def test_analysis_matches_golden(self):
        out = self.tmp + "/analysis.json"
        run("graph.py", GOLD, "--actions", "actions.frozen.json", "--analysis-out", out, check=True)
        got, want = load(out), load(GOLD + "/expected-analysis.json")
        for view in ("explicit_only", "with_inferred"):
            self.assertEqual(sorted(got[view]["roots"]), sorted(want[view]["roots"]), view)
            self.assertEqual(sorted(got[view]["leaves"]), sorted(want[view]["leaves"]), view)
            self.assertEqual(srt(got[view]["cycles"]), srt(want[view]["cycles"]), view)
        self.assertEqual(got["with_inferred"]["external_stubs"], want["external_stubs"])

    def test_inferred_edges_merge_the_loops(self):
        got = load(GOLD + "/expected-analysis.json")
        self.assertEqual(len(got["explicit_only"]["cycles"]), 2)
        self.assertEqual(len(got["with_inferred"]["cycles"]), 1)

    def test_mermaid_has_every_node_including_isolated(self):
        out = self.tmp + "/g.mmd"
        run("graph.py", GOLD, "--actions", "actions.frozen.json", "--mermaid", out, check=True)
        text = read(out)
        self.assertTrue(text.startswith("flowchart LR"))
        for r in load(GOLD + "/actions.frozen.json"):
            if "duplicate_of" in r or "superseded_by" in r:
                self.assertNotIn(G.mm_id(r["id"]) + "[", text)
            else:
                self.assertIn(G.mm_id(r["id"]) + "[", text, r["id"])
        self.assertIn('-.->|"exception-of (inferred)"|', text)
        self.assertIn("external_Chapter_9_30", text)

    def test_explicit_view_and_hide_types(self):
        out = self.tmp + "/g.mmd"
        run("graph.py", GOLD, "--actions", "actions.frozen.json", "--mermaid", out, "--view", "explicit", "--hide-types", "enforcement", check=True)
        text = read(out)
        self.assertNotIn("(inferred)", text); self.assertNotIn('|"enforcement', text)

    def test_large_graph_is_split(self):
        p = run("graph.py", GOLD, "--actions", "actions.frozen.json", "--mermaid", self.tmp + "/g.mmd", "--max-nodes", "10", check=True)
        parts = sorted(f for f in os.listdir(self.tmp) if f.startswith("g.part"))
        self.assertGreaterEqual(len(parts), 2)
        self.assertIn("exceed", p.stdout)

    def test_tarjan_handles_deep_chain_and_self_loop(self):
        n = 6000
        adj = {str(i): {str(i + 1)} for i in range(n)}; adj[str(n)] = {str(n)}
        comps = G.sccs(list(adj), adj)
        self.assertEqual(sum(len(c) for c in comps), n + 1)
        self.assertEqual([c for c in comps if len(c) > 1], [])

    def test_group_by_chapter_and_actor(self):
        for grp in ("chapter", "actor"):
            out = self.tmp + f"/{grp}.mmd"
            run("graph.py", GOLD, "--actions", "actions.frozen.json", "--mermaid", out, "--group", grp, check=True)
            self.assertIn("subgraph", read(out))


if __name__ == "__main__":
    unittest.main()
