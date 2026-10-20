#!/usr/bin/env python3
"""Apply orphan resolutions and freeze the first-order map.

Reads actions.json (the pre-resolution records from expand.py), provisions.json and
orphans.json. Applies each orphan's resolution patch to the records, in orphan-id order,
and writes actions.frozen.json and provisions.frozen.json. The inputs are never modified, so
re-running after expand.py (or after changing an answer) reproduces the same frozen map from the
saved resolutions.

A resolution is {"type": ..., "answer": "...", "patch": {"<record id>": {<fields replaced>}}}.
Patches must be self-contained: set `status` and the remaining `orphan_flags`.

Refuses (exit 1, writes nothing) when:
  - an orphan is still open,
  - a patch names an unknown record or an unknown field,
  - a record is still an orphan after patching, or a resolved record keeps flags,
  - a known gap loses its flag.

Provision `attaches_to` is recomputed from the frozen records: duplicate/superseded records drop
out, while `chapter` and `glossary` targets are kept.

Usage:  resolve.py RUN_DIR [--actions actions.json] [--provisions provisions.json] [--orphans orphans.json]
"""
import argparse, copy, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_json, write_json

GRAPH_EXCLUDED = ("duplicate_of", "superseded_by")
ALLOWED = {"signal", "actor", "modality", "action", "counterparty", "timing", "conditions", "exceptions", "consequence",
           "attachments", "outputs", "status", "orphan_flags", "link", "conflict_with", "resolution_note", "duplicate_of",
           "superseded_by", "external_refs", "source_quote", "provision_refs"}


def resolve(actions, prov, orphans):
    errs = []
    recs = {r["id"]: copy.deepcopy(r) for r in actions}
    notes = {}
    for o in sorted(orphans, key=lambda x: x["id"]):
        if o["status"] == "open":
            errs.append(f"{o['id']} ({o['code']}) is still open")
            continue
        res = o.get("resolution")
        if not res:
            errs.append(f"{o['id']} has status {o['status']} but no resolution")
            continue
        for rid, patch in res.get("patch", {}).items():
            if rid not in recs:
                errs.append(f"{o['id']}: patch names unknown record {rid}")
                continue
            for k in patch:
                if k not in ALLOWED:
                    errs.append(f"{o['id']}: patch field {k!r} on {rid} is not a record field")
            recs[rid].update(copy.deepcopy(patch))
            notes.setdefault(rid, []).append(f"{o['id']} ({o['code']}): {res['answer']}")
    for rid, n in notes.items():
        recs[rid]["resolution_note"] = "; ".join(n)
    for r in recs.values():
        if r["status"] == "orphan":
            errs.append(f"{r['id']} is still an orphan after patching")
        if r["status"] == "resolved" and r["orphan_flags"]:
            errs.append(f"{r['id']} is resolved but still carries flags {r['orphan_flags']}")
        if r["status"] == "known_gap" and not r["orphan_flags"]:
            errs.append(f"{r['id']} is a known gap but lost its orphan flag")
    frozen = [recs[r["id"]] for r in actions]
    live = [r for r in frozen if not any(k in r for k in GRAPH_EXCLUDED)]
    targets = {}
    for r in live:
        for a in r["attachments"]:
            targets.setdefault(a["provision"], set()).add(r["id"])
        if r["consequence"]:
            for p in r["consequence"]["provision_refs"]:
                targets.setdefault(p, set()).add(r["id"])
        for p in r["exceptions"]:
            targets.setdefault(p, set()).add(r["id"])
    out = copy.deepcopy(prov)
    for p in out:
        keep = [t for t in p["attaches_to"] if t in ("chapter", "glossary")]
        p["attaches_to"] = sorted(set(keep) | targets.get(p["id"], set()))
        if p["class"] == "definition" and not p["attaches_to"]:
            p["attaches_to"] = ["glossary"]
    return frozen, out, errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--actions", default="actions.json")
    ap.add_argument("--provisions", default="provisions.json")
    ap.add_argument("--orphans", default="orphans.json")
    ap.add_argument("--out-actions", default="actions.frozen.json")
    ap.add_argument("--out-provisions", default="provisions.frozen.json")
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    frozen, prov, errs = resolve(read_json(P(a.actions)), read_json(P(a.provisions)), read_json(P(a.orphans)))
    for e in errs:
        print("ERROR", e)
    if errs:
        print(f"{len(errs)} problem(s); nothing written")
        return 1
    write_json(P(a.out_actions), frozen)
    write_json(P(a.out_provisions), prov)
    gaps = sum(1 for r in frozen if r["status"] == "known_gap")
    ex = sum(1 for r in frozen if any(k in r for k in GRAPH_EXCLUDED))
    print(f"froze {len(frozen)} records ({gaps} known gaps, {ex} excluded as duplicate/superseded) -> {a.out_actions}, {a.out_provisions}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
