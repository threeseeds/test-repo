#!/usr/bin/env python3
"""Build the second-order dependency graph from the frozen first-order map.

Edge A -> B means "B depends on A" (direction conventions in docs/SPEC.md section 8).

Derived automatically (basis explicit, status accepted):
  triggers   one edge from every `upstream_action` signal ref to the record that carries it.
Everything else comes from the edge sheet, `dependencies.jsonl`, one JSON object per line:
  {"from": "5.16.060-3", "to": "5.16.080.A-1", "type": "produces-input",
   "basis": "explicit", "conf": "high", "ev": "<quote or reasoning>"}
  - ids may omit the leading "A-"; external stubs are written "external:Chapter 1.14"
  - type: produces-input | condition-precedent | temporal | reference | enforcement |
          exception-of | delegation   (triggers are derived; do not list them)
  - basis: explicit (the text says it) | inferred (you reasoned it)
  - conf: high | medium | low
  - status (optional): accepted | pending_review | rejected. Default: accepted for explicit,
    pending_review for inferred. Use edge_review.py to record the user's decisions here.
  - {"cycle": {"view": "explicit_only|with_inferred", "members": [...ids...], "label": "...", "exit": "..."}}
    labels a cycle reported by graph.py.
Lines starting with # and blank lines are ignored.

Nodes are the live records (duplicate/superseded records are excluded) plus external stubs.
Writes dependencies.json. Refuses (exit 1, writes nothing) on unknown ids, excluded nodes,
self-loops, duplicate edges or bad enumerations.

Usage:  build_deps.py RUN_DIR [--actions actions.frozen.json] [--sheet dependencies.jsonl] [--out dependencies.json]
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_json, read_text, write_json

TYPES = {"produces-input", "condition-precedent", "temporal", "reference", "enforcement", "exception-of", "delegation"}
CONF = {"high", "medium", "low"}
BASIS = {"explicit", "inferred"}
STATUS = {"accepted", "pending_review", "rejected"}
EXCLUDED = ("duplicate_of", "superseded_by")


def norm(i):
    return i if i.startswith(("A-", "external:")) else "A-" + i


def read_sheet(path):
    rows = []
    for no, line in enumerate(read_text(path).splitlines(), 1):
        if line.strip() and not line.lstrip().startswith("#"):
            try:
                rows.append((no, json.loads(line)))
            except json.JSONDecodeError as e:
                sys.exit(f"{os.path.basename(path)} line {no}: invalid JSON: {e}")
    return rows


def build(actions, rows):
    errs = []
    live = [r for r in actions if not any(k in r for k in EXCLUDED)]
    ids = {r["id"] for r in live}
    excluded = {r["id"] for r in actions} - ids
    edges, seen = [], set()

    def add(frm, to, typ, basis, conf, ev, status, where):
        if frm == to:
            errs.append(f"{where}: self-loop on {frm}"); return
        for end in (frm, to):
            if end.startswith("external:"):
                continue
            if end in excluded:
                errs.append(f"{where}: {end} is a duplicate/superseded record and cannot be a node")
            elif end not in ids:
                errs.append(f"{where}: unknown record {end}")
        key = (typ, frm, to)
        if key in seen:
            return False
        seen.add(key)
        edges.append({"id": f"E-{len(edges) + 1:03d}", "from": frm, "to": to, "type": typ, "basis": basis,
                      "confidence": conf, "evidence": ev, "status": status})
        return True

    for r in live:
        s = r["signal"]
        if s["type"] == "upstream_action" and s.get("ref") and s["ref"] in ids:
            add(s["ref"], r["id"], "triggers", "explicit", "high", s.get("text") or "", "accepted", f"signal of {r['id']}")
    derived = len(edges)
    notes, dupes = [], 0
    for no, row in rows:
        where = f"sheet line {no}"
        if "cycle" in row:
            c = row["cycle"]
            if c.get("view") not in ("explicit_only", "with_inferred") or not c.get("members") or not c.get("label"):
                errs.append(f"{where}: cycle needs view, members and label")
            else:
                notes.append({"view": c["view"], "members": [norm(m) for m in c["members"]], "label": c["label"],
                              **({"exit": c["exit"]} if c.get("exit") else {})})
            continue
        missing = [k for k in ("from", "to", "type", "basis", "conf", "ev") if k not in row]
        if missing:
            errs.append(f"{where}: missing {missing}"); continue
        if row["type"] == "triggers":
            errs.append(f"{where}: triggers edges are derived from signal refs; fix the record's signal instead"); continue
        if row["type"] not in TYPES: errs.append(f"{where}: bad type {row['type']!r}"); continue
        if row["basis"] not in BASIS: errs.append(f"{where}: bad basis {row['basis']!r}"); continue
        if row["conf"] not in CONF: errs.append(f"{where}: bad conf {row['conf']!r}"); continue
        status = row.get("status") or ("accepted" if row["basis"] == "explicit" else "pending_review")
        if status not in STATUS: errs.append(f"{where}: bad status {status!r}"); continue
        if not row["ev"].strip(): errs.append(f"{where}: evidence is required"); continue
        k = (row["type"], norm(row["from"]), norm(row["to"]))
        if k in seen:
            errs.append(f"{where}: duplicate edge {k}"); continue
        add(norm(row["from"]), norm(row["to"]), row["type"], row["basis"], row["conf"], row["ev"], status, where)
    nodes = sorted(ids | {e[k] for e in edges for k in ("from", "to") if e[k].startswith("external:")})
    out = {"nodes": nodes, "edges": edges}
    if notes:
        out["cycle_notes"] = notes
    return out, errs, derived


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--actions", default="actions.frozen.json")
    ap.add_argument("--sheet", default="dependencies.jsonl")
    ap.add_argument("--out", default="dependencies.json")
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    rows = read_sheet(P(a.sheet)) if os.path.exists(P(a.sheet)) else []
    out, errs, derived = build(read_json(P(a.actions)), rows)
    for e in errs:
        print("ERROR", e)
    if errs:
        print(f"{len(errs)} problem(s); nothing written")
        return 1
    write_json(P(a.out), out)
    by = {}
    for e in out["edges"]:
        by[e["type"]] = by.get(e["type"], 0) + 1
    pend = sum(1 for e in out["edges"] if e["status"] == "pending_review")
    print(f"wrote {len(out['edges'])} edges ({derived} derived triggers) over {len(out['nodes'])} nodes -> {a.out}; {pend} awaiting review")
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
