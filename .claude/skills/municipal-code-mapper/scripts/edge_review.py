#!/usr/bin/env python3
"""Show the edges awaiting review as a table, and record the user's decisions.

  edge_review.py RUN table                       # pending edges, grouped by type
  edge_review.py RUN apply --accept E-050,E-051 --reject E-060
  edge_review.py RUN apply --accept-all [--reject E-060]

Decisions are written into the edge sheet (dependencies.jsonl) as each line's `status`, so they
survive rebuilding. Rejected edges stay in the graph file as `rejected` and are ignored by
graph analysis and diagrams, so they are not proposed again. Re-run build_deps.py afterwards.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_deps import norm
from fileio import read_json, read_text, write_text


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def short(i):
    return i[2:] if i.startswith("A-") else i


def table(deps, actions):
    by = {r["id"]: r for r in actions}
    pend = [e for e in deps["edges"] if e["status"] == "pending_review"]
    if not pend:
        return "No edges awaiting review.\n"
    out = [f"**{len(pend)} edges awaiting review** (inferred from context, not stated in the text).\n"]
    for typ in sorted({e["type"] for e in pend}):
        rows = [e for e in pend if e["type"] == typ]
        out += [f"### {typ}: {len(rows)}\n", "| # | From | To | Confidence | Why | Decision |", "|---|---|---|---|---|---|"]
        for e in rows:
            def lab(x):
                r = by.get(x)
                return cell(f"{short(x)} ({r['action']['verb']})") if r else cell(x)
            out.append(f"| {e['id']} | {lab(e['from'])} | {lab(e['to'])} | {e['confidence']} | {cell(e['evidence'])} | accept / reject |")
        out.append("")
    return "\n".join(out)


def apply(sheet_path, deps, accept, reject, accept_all):
    lines = read_text(sheet_path).splitlines()
    ids = {e["id"]: e for e in deps["edges"]}
    unknown = [i for i in accept + reject if i not in ids]
    if unknown:
        sys.exit(f"unknown edge ids: {unknown}")
    if set(accept) & set(reject):
        sys.exit("an edge cannot be both accepted and rejected")
    decide = {}
    if accept_all:
        for e in deps["edges"]:
            if e["status"] == "pending_review":
                decide[(e["type"], e["from"], e["to"])] = "accepted"
    for i in accept:
        decide[(ids[i]["type"], ids[i]["from"], ids[i]["to"])] = "accepted"
    for i in reject:
        decide[(ids[i]["type"], ids[i]["from"], ids[i]["to"])] = "rejected"
    out, done = [], set()
    for line in lines:
        if line.strip() and not line.lstrip().startswith("#"):
            row = json.loads(line)
            if "cycle" not in row:
                k = (row["type"], norm(row["from"]), norm(row["to"]))
                if k in decide:
                    row["status"] = decide[k]; done.add(k)
                    line = json.dumps(row, ensure_ascii=False)
        out.append(line)
    missing = set(decide) - done
    if missing:
        sys.exit(f"edges not found in the sheet (derived triggers cannot be reviewed): {sorted(missing)}")
    write_text(sheet_path, "\n".join(out) + "\n")
    return len(done)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("command", choices=["table", "apply"])
    ap.add_argument("--accept", default="")
    ap.add_argument("--reject", default="")
    ap.add_argument("--accept-all", action="store_true")
    ap.add_argument("--actions", default="actions.frozen.json")
    ap.add_argument("--deps", default="dependencies.json")
    ap.add_argument("--sheet", default="dependencies.jsonl")
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    deps = read_json(P(a.deps))
    if a.command == "table":
        sys.stdout.write(table(deps, read_json(P(a.actions))))
    else:
        n = apply(P(a.sheet), deps, [x for x in a.accept.split(",") if x], [x for x in a.reject.split(",") if x], a.accept_all)
        print(f"updated {n} edge(s) in {a.sheet}; re-run build_deps.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
