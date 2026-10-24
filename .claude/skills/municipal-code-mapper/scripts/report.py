#!/usr/bin/env python3
"""Render the human-readable reports from a run's JSON files.

Writes into RUN_DIR (or --out):
  first-order-map.md    register and views (by section, actor, counterparty, signal type,
                        actor x counterparty matrix, glossary, attachments, orphan log)
  second-order-map.md   dependency summary, graph analysis, cycles, edges awaiting review
  coverage.md / coverage.json   every provision -> records / attachments

Usage:
  report.py RUN_DIR [--actions actions.json] [--deps dependencies.json] [--title "Brisbane Title 5"]
"""
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_text, write_text, read_json, write_json


import graph as G


def section_of(pid):
    """Section a provision id belongs to: 5.16.090 for municode ids, 99.31 for CFR ids (99.31.a.1.i)."""
    parts = pid.split(".")
    if len(parts) > 2 and not all(x.isdigit() for x in parts):
        return ".".join(parts[:2])
    return pid.rsplit(".", 1)[0] if pid.count(".") > 2 else pid

def cell(s):
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def who(a):
    return a["id"][4:] if a else "(unknown)"


def sig(r):
    s = r["signal"]
    t = s["type"]
    txt = s.get("text") or ""
    mark = "" if s.get("confidence") in ("explicit", None) else " *(inferred)*"
    return f"{t}: {txt}{mark}" if txt else t


def tim(r):
    t = r["timing"]
    if not t:
        return ""
    if t.get("text"):
        return t["text"]
    return " ".join(str(x) for x in (t.get("amount"), t.get("unit")) if x)


def live(actions):
    return [r for r in actions if not any(k in r for k in G.GRAPH_EXCLUDED)]


def row(r, with_id=True):
    return [r["id"][2:], who(r["actor"]), r["modality"], f'{r["action"]["verb"]} {r["action"]["object"]}', sig(r),
            who(r["counterparty"]), tim(r)]


HEAD = ["Record", "Actor", "Modality", "Action", "Signal", "To whom", "Timing"]


def first_order(actions, orphans, prov, actors, glossary, title):
    L = [f"# First-order map: {title}\n"]
    recs = live(actions)
    L.append(f"{len(prov)} provisions, {len(actions)} action records "
             f"({len(actions) - len(recs)} excluded as duplicate/superseded), {len(orphans)} orphans.\n")
    c = collections.Counter(r["modality"] for r in recs)
    L.append("**By modality:** " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + "  ")
    c = collections.Counter(r["status"] for r in actions)
    L.append("**By status:** " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + "\n")
    L.append("## By section\n")
    bysec = collections.defaultdict(list)
    for r in recs:
        bysec[section_of(r["provision_refs"][0])].append(r)
    for sec in sorted(bysec, key=lambda s: [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in s.split(".")]):
        L.append(f"### {sec}\n")
        L.append(table(HEAD, [row(r) for r in bysec[sec]]))
    L.append("## By actor (obligation load)\n")
    ba = collections.defaultdict(list)
    for r in recs:
        ba[who(r["actor"])].append(r)
    for a in sorted(ba):
        c = collections.Counter(r["modality"] for r in ba[a])
        L.append(f"### {a}\n\n" + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + "\n")
        L.append(table(["Record", "Modality", "Action", "Signal", "To whom", "Timing"],
                       [[r["id"][2:], r["modality"], f'{r["action"]["verb"]} {r["action"]["object"]}', sig(r), who(r["counterparty"]), tim(r)] for r in ba[a]]))
    L.append("## By counterparty (who owes what to whom)\n")
    bc = collections.defaultdict(list)
    for r in recs:
        if r["counterparty"]:
            bc[who(r["counterparty"])].append(r)
    for cp in sorted(bc):
        L.append(f"### Owed to {cp}\n")
        L.append(table(["Record", "Actor", "Modality", "Action", "Basis"],
                       [[r["id"][2:], who(r["actor"]), r["modality"], f'{r["action"]["verb"]} {r["action"]["object"]}', r["counterparty"]["confidence"]] for r in bc[cp]]))
    L.append("## By signal type\n")
    bs = collections.defaultdict(list)
    for r in recs:
        bs[r["signal"]["type"]].append(r["id"][2:])
    L.append(table(["Signal type", "Count", "Records"], [[k, len(v), ", ".join(v)] for k, v in sorted(bs.items())]))
    L.append("## Actor x counterparty matrix\n")
    cps = sorted({who(r["counterparty"]) if r["counterparty"] else "—" for r in recs})
    acs = sorted({who(r["actor"]) for r in recs})
    m = collections.Counter((who(r["actor"]), who(r["counterparty"]) if r["counterparty"] else "—") for r in recs)
    L.append(table(["Actor \\ To whom"] + cps, [[a] + [m[(a, c)] or "" for c in cps] for a in acs]))
    alts = collections.defaultdict(list)
    for r in recs:
        if r["link"]:
            alts[(r["link"]["link_id"], r["link"]["relation"])].append(r["id"][2:])
    if alts:
        L.append("## Linked records (joint / alternative actors)\n")
        L.append(table(["Link", "Relation", "Records"], [[k[0], k[1], ", ".join(v)] for k, v in sorted(alts.items())]))
    att = [(r["id"][2:], a["kind"], a["provision"], a["summary"]) for r in recs for a in r["attachments"] if a["kind"] != "definition"]
    if att:
        L.append("## Attachments (fees, terms, applicability)\n")
        L.append(table(["Record", "Kind", "Provision", "Summary"], att))
    if glossary:
        L.append("## Glossary\n")
        L.append(table(["Term", "Provision", "Definition"], [[g["term"], g["provision"], g["text"]] for g in glossary]))
    L.append("## Orphan log\n")
    L.append(table(["Orphan", "Code", "Records", "Status", "Resolution"],
                   [[o["id"], o["code"], ", ".join(x[2:] for x in o["records"]), o["status"], (o.get("resolution") or {}).get("answer", "")] for o in orphans]))
    gaps = [r for r in actions if r["status"] == "known_gap"]
    if gaps:
        L.append("## Known gaps (accepted by the user, not resolved)\n")
        L.append(table(["Record", "Flags", "Quote"], [[r["id"][2:], ", ".join(r["orphan_flags"]), r["source_quote"]] for r in gaps]))
    ext = sorted({x for r in actions for x in r.get("external_refs", [])} | {x for p in prov for x in p.get("external_refs", [])})
    if ext:
        L.append("## External references (outside this run)\n\n" + "\n".join(f"- {x}" for x in ext) + "\n")
    return "\n".join(L)


def second_order(actions, deps, title):
    views = G.analyze_views(actions, deps)
    L = [f"# Second-order map: {title}\n"]
    c = collections.Counter((e["type"], e["basis"]) for e in deps["edges"])
    L.append("## Edges by type\n")
    types = sorted({t for t, _ in c})
    L.append(table(["Type", "Explicit", "Inferred"], [[t, c[(t, "explicit")], c[(t, "inferred")]] for t in types]))
    for name, v in views.items():
        L.append(f"## Analysis: {name.replace('_', ' ')}\n")
        L.append(f"{v['nodes']} nodes, {v['edges']} edges.\n")
        L.append("- **Roots (entry points):** " + ", ".join(x[2:] for x in v["roots"]))
        L.append("- **Leaves (terminal actions):** " + ", ".join(x[2:] for x in v["leaves"]))
        ch = v["longest_chain"]
        L.append(f"- **Longest chain ({ch['length']} actions):** " + " → ".join(
            ("{" + ", ".join(y[2:] for y in x) + "}") if isinstance(x, list) else x[2:] for x in ch["path"]))
        if v["dangling_outputs"]:
            L.append("- **Outputs nothing consumes:** " + ", ".join(x[2:] for x in v["dangling_outputs"]))
        if v["depends_on_external"]:
            L.append("- **Depend on code outside this run:** " + ", ".join(x[2:] for x in v["depends_on_external"]))
        if v["unresolved_upstream"]:
            L.append("- **Upstream action not in the map:** " + ", ".join(x[2:] for x in v["unresolved_upstream"]))
        L.append("")
        notes = {tuple(sorted(n["members"])): n for n in deps.get("cycle_notes", []) if n["view"] == name}
        if v["cycles"]:
            L.append("**Cycles**\n")
            rows = []
            for cyc in v["cycles"]:
                n = notes.get(tuple(sorted(cyc)))
                rows.append([n["label"] if n else "(unlabeled)", ", ".join(x[2:] for x in cyc), n.get("exit", "") if n else "no stated exit checked"])
            L.append(table(["Cycle", "Members", "Exit"], rows))
        else:
            L.append("No cycles.\n")
    pend = [e for e in deps["edges"] if e["status"] == "pending_review"]
    L.append("## Edges awaiting review\n")
    L.append(table(["Edge", "From", "To", "Type", "Confidence", "Evidence"],
                   [[e["id"], e["from"][2:] if e["from"].startswith("A-") else e["from"], e["to"][2:] if e["to"].startswith("A-") else e["to"],
                     e["type"], e["confidence"], e["evidence"]] for e in pend]) if pend else "None.\n")
    L.append("## All edges\n")
    L.append(table(["Edge", "From", "To", "Type", "Basis", "Status"],
                   [[e["id"], e["from"][2:] if e["from"].startswith("A-") else e["from"], e["to"][2:] if e["to"].startswith("A-") else e["to"],
                     e["type"], e["basis"], e["status"]] for e in deps["edges"]]))
    return "\n".join(L)


def coverage(prov):
    cov = [{"provision": p["id"], "class": p["class"], "records": p["record_ids"], "attached_to": p["attaches_to"]} for p in prov]
    md = ["# Coverage ledger\n", table(["Provision", "Class", "Records", "Attached to"],
          [[c["provision"], c["class"], ", ".join(x[2:] for x in c["records"]), ", ".join(x[2:] if x.startswith("A-") else x for x in c["attached_to"])] for c in cov])]
    return cov, "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out")
    ap.add_argument("--title", default="municipal code")
    for f, d in (("provisions", "provisions.json"), ("actors", "actors.json"), ("actions", "actions.json"),
                 ("orphans", "orphans.json"), ("deps", "dependencies.json"), ("glossary", "glossary.json")):
        ap.add_argument("--" + f, default=d)
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    out = a.out or a.run_dir
    os.makedirs(out, exist_ok=True)
    prov, actors, actions, orphans = read_json(P(a.provisions)), read_json(P(a.actors)), read_json(P(a.actions)), read_json(P(a.orphans))
    glossary = read_json(P(a.glossary)) if os.path.exists(P(a.glossary)) else []
    write_text(os.path.join(out, "first-order-map.md"), first_order(actions, orphans, prov, actors, glossary, a.title))
    cov, md = coverage(prov)
    write_text(os.path.join(out, "coverage.md"), md)
    write_json(os.path.join(out, "coverage.json"), cov)
    wrote = ["first-order-map.md", "coverage.md", "coverage.json"]
    if os.path.exists(P(a.deps)):
        write_text(os.path.join(out, "second-order-map.md"), second_order(actions, read_json(P(a.deps)), a.title))
        wrote.append("second-order-map.md")
    print("wrote " + ", ".join(wrote) + f" in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
