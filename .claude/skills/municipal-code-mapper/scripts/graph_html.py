#!/usr/bin/env python3
"""Write a self-contained interactive HTML page of the dependency graph.

Reads the frozen first-order map and dependencies.json from a run, computes the graph analysis,
and bakes everything into assets/dependency-graph.template.html. The page needs no server and no
network except an optional web font; it supports pan and zoom, edge-type and basis filters,
search, color by chapter/modality/actor type, highlights (longest chain, cycles, entry points,
edges awaiting review), and a detail panel with each record's verbatim quote and its upstream and
downstream records.

Usage:
  graph_html.py RUN_DIR --title "Brisbane Dependency Map" --subtitle "Title 5, Division I ..."
                [--actions actions.frozen.json] [--provisions provisions.frozen.json]
                [--deps dependencies.json] [--out dependency-graph.html]
"""
import argparse, html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph as G
from fileio import read_json, read_text, write_text

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODAL = {"duty": "must", "prohibition": "must not", "permission": "may", "power": "has the power to", "entitlement": "is entitled to"}
SIG = {"event": "when", "state": "while", "time": "on a schedule", "request": "on request", "upstream_action": "after",
       "discretionary": "at its discretion", "standing": "at all times", "unknown": "not stated"}


def short(i):
    return i[2:] if i.startswith("A-") else i


def build(actions, prov, deps, actors, titles, title, subtitle):
    akind = {a["id"]: a for a in actors}
    heading = {p["id"]: p["heading"] for p in prov}
    chapter_of = {p["id"]: p["chapter"] for p in prov}
    live = [r for r in actions if not any(k in r for k in G.GRAPH_EXCLUDED)]
    nodes = []
    for r in live:
        a = r["actor"]
        ent = akind.get(a["id"], {}) if a else {}
        cp = r["counterparty"]
        t = r["timing"] or {}
        pid = r["provision_refs"][0]
        nodes.append({
            "id": short(r["id"]), "ch": chapter_of.get(pid, ""), "heading": heading.get(pid, ""),
            "actor": ent.get("label", "unspecified actor") if a else "unspecified actor", "kind": ent.get("kind", "public"),
            "mod": r["modality"], "modalityWord": MODAL[r["modality"]], "verb": r["action"]["verb"], "obj": r["action"]["object"],
            "quote": r["source_quote"], "sigType": SIG[r["signal"]["type"]], "sigText": r["signal"].get("text") or "",
            "cp": akind.get(cp["id"], {}).get("label", "") if cp else "", "timing": t.get("text") or "",
            "out": [o.replace("artifact:", "").replace("-", " ") for o in r["outputs"]],
            "consequence": r["consequence"]["summary"] if r["consequence"] else "",
            "exceptions": r["exceptions"], "att": [x for x in r["attachments"] if x["kind"] != "definition"],
            "note": r["resolution_note"] or "", "status": r["status"]})
    ids = {n["id"] for n in nodes}
    edges = []
    for e in deps["edges"]:
        f, t = short(e["from"]), short(e["to"])
        for x in (f, t):
            if x not in ids and x.startswith("external:"):
                ids.add(x)
                nodes.append({"id": x, "ch": "external", "heading": "outside this run", "actor": "other law", "kind": "external_agency", "mod": "", "modalityWord": "applies:",
                              "verb": x[9:], "obj": "", "quote": "", "sigType": "", "sigText": "", "cp": "", "timing": "", "out": [], "consequence": "",
                              "exceptions": [], "att": [], "note": "", "status": "external"})
        edges.append({"id": e["id"], "f": f, "t": t, "ty": e["type"], "ba": e["basis"], "cf": e["confidence"], "ev": e["evidence"], "st": e["status"]})
    views = G.analyze_views(actions, deps)
    an = {}
    for k, v in views.items():
        an[k] = {"roots": [short(x) for x in v["roots"]], "cycles": [[short(x) for x in c] for c in v["cycles"]],
                 "longest_chain": {"length": v["longest_chain"]["length"],
                                   "path": [[short(y) for y in x] if isinstance(x, list) else short(x) for x in v["longest_chain"]["path"]]}}
    live_e = [e for e in edges if e["st"] != "rejected"]
    chapters = sorted({n["ch"] for n in nodes if n["ch"] and n["ch"] != "external"}, key=lambda c: [int(x) for x in c.split(".")])
    if any(n["ch"] == "external" for n in nodes):
        chapters.append("external")
    counts = {"nodes": len(nodes), "edges": len(live_e), "stated": sum(1 for e in live_e if e["ba"] == "explicit"),
              "inferred": sum(1 for e in live_e if e["ba"] == "inferred"), "pending": sum(1 for e in live_e if e["st"] == "pending_review"),
              "enforcement": sum(1 for e in live_e if e["ty"] == "enforcement")}
    return {"title": title, "subtitle": subtitle, "chapters": chapters, "chapterTitles": titles, "counts": counts,
            "analysis": an, "nodes": nodes, "edges": edges}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--title", default="Dependency Map")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--actions", default="actions.frozen.json")
    ap.add_argument("--provisions", default="provisions.frozen.json")
    ap.add_argument("--deps", default="dependencies.json")
    ap.add_argument("--actors", default="actors.json")
    ap.add_argument("--chapters", default="chapters.json")
    ap.add_argument("--template", default=os.path.join(SKILL, "assets", "dependency-graph.template.html"))
    ap.add_argument("--out", default="dependency-graph.html")
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    titles = read_json(P(a.chapters)) if os.path.exists(P(a.chapters)) else {}
    data = build(read_json(P(a.actions)), read_json(P(a.provisions)), read_json(P(a.deps)), read_json(P(a.actors)), titles, a.title, a.subtitle)
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
    page = read_text(a.template).replace("__TITLE__", html.escape(a.title)).replace("__DATA__", blob)
    write_text(P(a.out), page)
    print(f"wrote {P(a.out)} ({len(page) // 1024} KB): {data['counts']['nodes']} records, {data['counts']['edges']} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
