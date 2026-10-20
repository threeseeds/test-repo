#!/usr/bin/env python3
"""Score a run against golden files (precision / recall / field accuracy).

Records are matched by (primary provision, actor id, modality), disambiguated by action
verb and then by order, so differing record numbering does not matter. Reports:
  classification   share of provisions given the golden class
  records          precision, recall, F1
  fields           accuracy over matched records: signal type, actor, modality, counterparty,
                   timing amount+unit (counterparty and timing only where golden has them)
  orphans          precision/recall on (code, primary provision) pairs
  edges            explicit-edge precision/recall (exact type+endpoints); inferred-edge recall

Usage:
  score.py RUN_DIR GOLDEN_DIR [--actions actions.json] [--golden-actions actions.pre-resolution.json]
           [--orphans orphans.json] [--deps dependencies.json] [--min-record-f1 0.9] [--json]
  Use --golden-actions actions.frozen.json with a frozen run.  Exit 1 if --min-record-f1 is not met.
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_json


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
            "tp": tp, "fp": fp, "fn": fn}


def key(r):
    return (r["provision_refs"][0], (r["actor"] or {"id": None})["id"], r["modality"])


def match_records(run, gold):
    """Returns {run_id: gold_id}."""
    groups = collections.defaultdict(list)
    for g in gold:
        groups[key(g)].append(g)
    used, out = set(), {}
    for r in run:
        cands = [g for g in groups.get(key(r), []) if g["id"] not in used]
        if not cands:
            continue
        same = [g for g in cands if g["action"]["verb"] == r["action"]["verb"]]
        g = (same or cands)[0]
        used.add(g["id"]); out[r["id"]] = g["id"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir"); ap.add_argument("golden_dir")
    ap.add_argument("--actions", default="actions.json")
    ap.add_argument("--golden-actions", default="actions.pre-resolution.json")
    ap.add_argument("--provisions", default="provisions.json")
    ap.add_argument("--orphans", default="orphans.json")
    ap.add_argument("--deps", default="dependencies.json")
    ap.add_argument("--min-record-f1", type=float)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    R = lambda n: os.path.join(a.run_dir, n)
    G = lambda n: os.path.join(a.golden_dir, n)
    out = {}
    rp, gp = {p["id"]: p for p in read_json(R(a.provisions))}, {p["id"]: p for p in read_json(G(a.provisions))}
    ok = sum(1 for i in gp if i in rp and rp[i]["class"] == gp[i]["class"])
    out["classification"] = {"correct": ok, "total": len(gp), "accuracy": round(ok / len(gp), 3),
                             "wrong": {i: [rp.get(i, {}).get("class"), gp[i]["class"]] for i in gp if rp.get(i, {}).get("class") != gp[i]["class"]}}
    run, gold = read_json(R(a.actions)), read_json(G(a.golden_actions))
    m = match_records(run, gold)
    out["records"] = prf(len(m), len(run) - len(m), len(gold) - len(m))
    out["records"]["missed"] = sorted(g["id"] for g in gold if g["id"] not in set(m.values()))
    out["records"]["extra"] = sorted(r["id"] for r in run if r["id"] not in m)
    gd, rd = {g["id"]: g for g in gold}, {r["id"]: r for r in run}
    fields = {"signal_type": [0, 0], "actor": [0, 0], "modality": [0, 0], "counterparty": [0, 0], "timing": [0, 0]}
    for rid_, gid in m.items():
        r, g = rd[rid_], gd[gid]
        fields["signal_type"][1] += 1; fields["signal_type"][0] += r["signal"]["type"] == g["signal"]["type"]
        fields["actor"][1] += 1; fields["actor"][0] += (r["actor"] or {}).get("id") == (g["actor"] or {}).get("id")
        fields["modality"][1] += 1; fields["modality"][0] += r["modality"] == g["modality"]
        if g["counterparty"]:
            fields["counterparty"][1] += 1; fields["counterparty"][0] += (r["counterparty"] or {}).get("id") == g["counterparty"]["id"]
        if g["timing"] and g["timing"].get("amount") is not None:
            fields["timing"][1] += 1
            fields["timing"][0] += bool(r["timing"]) and (r["timing"].get("amount"), r["timing"].get("unit")) == (g["timing"]["amount"], g["timing"]["unit"])
    out["fields"] = {k: {"correct": c, "total": t, "accuracy": round(c / t, 3) if t else None} for k, (c, t) in fields.items()}
    # orphans, keyed by (code, primary provision of the first record)
    def pairs(path, acts):
        by = {x["id"]: x for x in acts}
        return {(o["code"], by[rid_]["provision_refs"][0]) for o in read_json(path) for rid_ in o["records"] if rid_ in by}
    if os.path.exists(R(a.orphans)):
        rr, gg = pairs(R(a.orphans), run), pairs(G(a.orphans), gold)
        out["orphans"] = prf(len(rr & gg), len(rr - gg), len(gg - rr))
        out["orphans"]["false"] = sorted(rr - gg); out["orphans"]["missed"] = sorted(gg - rr)
    # edges, translated into golden record ids
    if os.path.exists(R(a.deps)) and os.path.exists(G(a.deps)):
        def tr(x):
            return m.get(x, x) if not x.startswith("external:") else x
        re_ = [e for e in read_json(R(a.deps))["edges"]]
        ge = [e for e in read_json(G(a.deps))["edges"]]
        sig = lambda e: (e["type"], tr(e["from"]), tr(e["to"]))
        gsig = lambda e: (e["type"], e["from"], e["to"])
        rex, gex = {sig(e) for e in re_ if e["basis"] == "explicit"}, {gsig(e) for e in ge if e["basis"] == "explicit"}
        out["edges_explicit"] = prf(len(rex & gex), len(rex - gex), len(gex - rex))
        out["edges_explicit"]["missed"] = sorted(gex - rex)
        rall = {sig(e) for e in re_}; gin = {gsig(e) for e in ge if e["basis"] == "inferred"}
        out["edges_inferred_recall"] = {"found": len(rall & gin), "total": len(gin), "missed": sorted(gin - rall)}
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        c = out["classification"]; print(f"classification  {c['correct']}/{c['total']}  wrong: {c['wrong'] or 'none'}")
        r = out["records"]; print(f"records         P {r['precision']} R {r['recall']} F1 {r['f1']}  missed {r['missed'] or 'none'}  extra {r['extra'] or 'none'}")
        print("fields          " + "  ".join(f"{k} {v['correct']}/{v['total']}" for k, v in out["fields"].items()))
        if "orphans" in out:
            o = out["orphans"]; print(f"orphans         P {o['precision']} R {o['recall']}  false {o['false'] or 'none'}  missed {o['missed'] or 'none'}")
        if "edges_explicit" in out:
            e = out["edges_explicit"]; print(f"explicit edges  P {e['precision']} R {e['recall']}  missed {len(e['missed'])}")
            i = out["edges_inferred_recall"]; print(f"inferred edges  recall {i['found']}/{i['total']}")
    if a.min_record_f1 is not None and out["records"]["f1"] < a.min_record_f1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
