#!/usr/bin/env python3
"""Validate a mapper run. Exit code 0 = clean, 1 = problems found.

Stages (each includes the checks of the one before):
  segment  provisions.json: schema, unique ids, non-empty text, text found in source
  extract  + actors, actions, orphans: schema, verbatim quotes, coverage invariant,
           actor and reference integrity, orphan <-> flag consistency
  frozen   + no open orphans; every orphan resolved or an accepted known gap
  deps     + dependencies.json: endpoints, graph membership, triggers-edge consistency

Usage:
  validate.py RUN_DIR --stage extract
  validate.py RUN_DIR --stage deps --actions actions.frozen.json --source source.md

Files in RUN_DIR (override with flags): provisions.json actors.json actions.json
orphans.json dependencies.json; --source (relative to the current directory) is the normalized source
text; optional, enables the whole-source quote check.
"""
import argparse, json, os, re, sys

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("validate.py needs the jsonschema package (pip install jsonschema)")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_text, read_json

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = ["segment", "extract", "frozen", "deps"]
GRAPH_EXCLUDED = ("duplicate_of", "superseded_by")


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


class Report:
    def __init__(self):
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append({"code": code, "where": where, "message": msg})


def schema_check(rep, schema_file, data, label):
    schema = read_json(os.path.join(SKILL, "schemas", schema_file))
    for e in list(Draft202012Validator(schema).iter_errors(data))[:25]:
        path = "/".join(str(p) for p in e.absolute_path)
        rep.err("schema", f"{label}:{path}", e.message[:200])


def check_segment(rep, prov, src_norm, require_class):
    ids = set()
    for p in prov:
        if p["id"] in ids:
            rep.err("dup-provision", p["id"], "duplicate provision id")
        ids.add(p["id"])
        if not p["text"]:
            rep.err("empty-provision", p["id"], "provision has no text")
        elif src_norm is not None and ws(p["text"]) not in src_norm:
            rep.err("text-not-in-source", p["id"], "provision text not found in source")
        if require_class and p["class"] is None:
            rep.err("unclassified", p["id"], "provision has no class")
    return ids


def attach_ok(p):
    return bool(p["attaches_to"])


def check_extract(rep, prov, actors, actions, orphans, src_norm, stage):
    pd = {p["id"]: p for p in prov}
    actor_ids = {a["id"] for a in actors}
    rids = [r["id"] for r in actions]
    ridset = set(rids)
    if len(rids) != len(ridset):
        rep.err("dup-record", "actions", "duplicate record ids")
    for r in actions:
        rid = r["id"]
        for pid in r["provision_refs"]:
            if pid not in pd:
                rep.err("bad-provision-ref", rid, f"unknown provision {pid}")
        q = r["source_quote"]
        if not any(pid in pd and q in pd[pid]["text"] for pid in r["provision_refs"]):
            rep.err("quote-not-in-provision", rid, "source_quote is not a verbatim substring of its provision")
        elif src_norm is not None and ws(q) not in src_norm:
            rep.err("quote-not-in-source", rid, "source_quote not found in source text")
        for k in ("actor", "counterparty"):
            a = r[k]
            if a and a["id"] not in actor_ids:
                rep.err("unknown-actor", rid, f"{k} {a['id']} not in actor registry")
        ref = r["signal"].get("ref")
        if ref and ref not in ridset:
            rep.err("bad-signal-ref", rid, f"signal ref {ref} is not a record")
        if r["signal"]["type"] == "upstream_action" and not ref:
            rep.err("missing-signal-ref", rid, "upstream_action signal has no ref")
        for c in r["conflict_with"]:
            if c not in ridset:
                rep.err("bad-conflict-ref", rid, f"conflict_with {c} is not a record")
        for k in GRAPH_EXCLUDED:
            if k in r and r[k] not in ridset:
                rep.err("bad-resolution-ref", rid, f"{k} {r[k]} is not a record")
        for a in r["attachments"]:
            if a["provision"] not in pd:
                rep.err("bad-attachment", rid, f"attachment provision {a['provision']} unknown")
        if r["consequence"]:
            for pid in r["consequence"]["provision_refs"]:
                if pid not in pd:
                    rep.err("bad-consequence", rid, f"consequence provision {pid} unknown")
        if r["link"]:
            peers = [x for x in actions if x["link"] and x["link"]["link_id"] == r["link"]["link_id"]]
            if len(peers) < 2:
                rep.err("lonely-link", rid, "linked record has no partner")
        flags = set(r["orphan_flags"])
        excluded = any(k in r for k in GRAPH_EXCLUDED)
        if r["signal"]["type"] == "unknown" and "O-SIG" not in flags and not excluded:
            rep.err("silent-orphan", rid, "signal is unknown but not flagged O-SIG")
        if r["actor"] is None and "O-ACT" not in flags and not excluded:
            rep.err("silent-orphan", rid, "actor is unknown but not flagged O-ACT")
        if r["status"] == "orphan" and not flags:
            rep.err("status-flags", rid, "status orphan with no orphan_flags")
        if flags and r["status"] not in ("orphan", "known_gap"):
            rep.err("status-flags", rid, f"flags {sorted(flags)} remain but status is {r['status']}")
        if r["status"] == "complete" and flags:
            rep.err("status-flags", rid, "complete record carries orphan flags")
    # coverage invariant
    covered = {}
    for r in actions:
        for pid in r["provision_refs"]:
            covered.setdefault(pid, set()).add(r["id"])
    for p in prov:
        if p["class"] in (None, "reserved"):
            continue
        if p["class"] == "operative" and p["id"] not in covered and not attach_ok(p):
            rep.err("uncovered", p["id"], "operative provision yields no record and has no attachment")
        elif p["class"] != "operative" and not attach_ok(p) and p["id"] not in covered:
            rep.err("uncovered", p["id"], f"{p['class']} provision attaches to nothing")
        for rid in p["record_ids"]:
            if rid not in ridset:
                rep.err("bad-record-id", p["id"], f"record_ids lists unknown record {rid}")
        for t in p["attaches_to"]:
            if t not in ("chapter", "glossary") and t not in ridset:
                rep.err("bad-attach-target", p["id"], f"attaches_to unknown record {t}")
    for r in actions:
        for pid in r["provision_refs"]:
            if pid in pd and r["id"] not in pd[pid]["record_ids"]:
                rep.err("record-missing-from-provision", r["id"], f"{pid}.record_ids does not list this record")
    # orphans <-> flags
    flag_pairs = {(c, r["id"]) for r in actions for c in r["orphan_flags"]}
    orph_pairs = {(o["code"], rid) for o in orphans for rid in o["records"]}
    for code, rid in sorted(orph_pairs - flag_pairs):
        if stage == "extract":
            rep.err("orphan-without-flag", rid, f"orphan {code} has no matching flag on the record")
    if stage == "extract":
        for code, rid in sorted(flag_pairs - orph_pairs):
            rep.err("flag-without-orphan", rid, f"flag {code} has no orphan entry")
    for o in orphans:
        for rid in o["records"]:
            if rid not in ridset:
                rep.err("bad-orphan-record", o["id"], f"orphan names unknown record {rid}")
    return ridset


def check_frozen(rep, actions, orphans):
    rd = {r["id"]: r for r in actions}
    for o in orphans:
        if o["status"] == "open":
            rep.err("open-orphan", o["id"], f"{o['code']} is still open")
        if o["status"] in ("resolved", "known_gap") and "resolution" not in o:
            rep.err("no-resolution", o["id"], "resolved orphan has no resolution")
        if o["status"] == "known_gap":
            for rid in o["records"]:
                if rid in rd and rd[rid]["status"] != "known_gap":
                    rep.err("gap-status", rid, "accepted known gap but record status is not known_gap")
    for r in actions:
        if r["status"] == "orphan":
            rep.err("open-record", r["id"], "record is still an orphan")
        if r["status"] == "known_gap" and not r["orphan_flags"]:
            rep.err("gap-without-flag", r["id"], "known_gap record lost its orphan flag")
        if r["status"] == "resolved" and r["orphan_flags"]:
            rep.err("resolved-with-flags", r["id"], "resolved record still carries flags")


def check_deps(rep, actions, deps):
    schema_check(rep, "dependency.schema.json", deps, "dependencies")
    rd = {r["id"]: r for r in actions}
    nodes = set(deps["nodes"])
    seen = set()
    triggers = set()
    for e in deps["edges"]:
        if e["id"] in seen:
            rep.err("dup-edge-id", e["id"], "duplicate edge id")
        seen.add(e["id"])
        for end in (e["from"], e["to"]):
            if end.startswith("external:"):
                pass
            elif end not in rd:
                rep.err("dangling-edge", e["id"], f"endpoint {end} is not a record")
            elif any(k in rd[end] for k in GRAPH_EXCLUDED):
                rep.err("excluded-node-in-graph", e["id"], f"{end} is a duplicate/superseded record and must not be a graph node")
            if end not in nodes:
                rep.err("node-missing", e["id"], f"{end} not listed in nodes")
        if e["from"] == e["to"]:
            rep.err("self-loop", e["id"], "edge from a node to itself")
        if e["type"] == "triggers":
            triggers.add((e["from"], e["to"]))
            tgt = rd.get(e["to"])
            if tgt is not None and tgt["signal"].get("ref") != e["from"]:
                rep.err("triggers-without-signal-ref", e["id"], f"{e['to']} has no signal ref to {e['from']}")
        if e["basis"] == "explicit" and e["status"] == "pending_review":
            rep.err("explicit-pending", e["id"], "explicit edges are accepted, not pending")
    for r in actions:
        if any(k in r for k in GRAPH_EXCLUDED):
            continue
        ref = r["signal"].get("ref")
        if r["signal"]["type"] == "upstream_action" and ref and ref in rd and (ref, r["id"]) not in triggers:
            rep.err("missing-triggers-edge", r["id"], f"signal ref {ref} has no triggers edge")
    for n in nodes:
        if not n.startswith("external:") and n not in rd:
            rep.err("bad-node", n, "node is not a record")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--stage", choices=STAGES, default="extract")
    for f, d in (("provisions", "provisions.json"), ("actors", "actors.json"), ("actions", "actions.json"),
                 ("orphans", "orphans.json"), ("deps", "dependencies.json"), ("source", None)):
        ap.add_argument("--" + f, default=d)
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    a = ap.parse_args(argv)
    P = lambda name: name if os.path.isabs(name) else os.path.join(a.run_dir, name)
    rep = Report()
    stage = STAGES.index(a.stage)
    src_norm = ws(read_text(a.source)) if a.source else None
    prov = read_json(P(a.provisions))
    schema_check(rep, "provision.schema.json", prov, "provisions")
    check_segment(rep, prov, src_norm, require_class=stage >= 1)
    counts = {"provisions": len(prov)}
    if stage >= 1:
        actors, actions, orphans = read_json(P(a.actors)), read_json(P(a.actions)), read_json(P(a.orphans))
        schema_check(rep, "actor.schema.json", actors, "actors")
        schema_check(rep, "action.schema.json", actions, "actions")
        schema_check(rep, "orphan.schema.json", orphans, "orphans")
        if not rep.errors or all(e["code"] != "schema" for e in rep.errors):
            check_extract(rep, prov, actors, actions, orphans, src_norm, "extract" if stage == 1 else "frozen")
            if stage >= 2:
                check_frozen(rep, actions, orphans)
        counts.update(records=len(actions), orphans=len(orphans))
    if stage >= 3:
        deps = read_json(P(a.deps))
        if not any(e["code"] == "schema" for e in rep.errors):
            check_deps(rep, actions, deps)
        counts["edges"] = len(deps["edges"])
    if a.json:
        print(json.dumps({"ok": not rep.errors, "counts": counts, "errors": rep.errors}, indent=2))
    else:
        for e in rep.errors:
            print(f"ERROR [{e['code']}] {e['where']}: {e['message']}")
        print(f"stage={a.stage} " + " ".join(f"{k}={v}" for k, v in counts.items()) +
              (" -> OK" if not rep.errors else f" -> {len(rep.errors)} problem(s)"))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
