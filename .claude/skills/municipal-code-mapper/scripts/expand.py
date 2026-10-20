#!/usr/bin/env python3
"""Expand a compact extraction sheet into full Action Records.

The model writes terse inputs; this script fills defaults, assigns ids, resolves
cross-references, applies classification attachments, and updates provisions.json. It checks
only what it needs to expand correctly; run validate.py afterwards for the full checks.

Inputs (all in RUN_DIR unless overridden):
  provisions.json      from segment.py
  actors.json          actor registry
  classification.json  provision classes and attachments (format below)
  extraction.jsonl     one JSON object per line, one Action Record per line
Outputs:
  actions.json         full records;  provisions.json is rewritten with class, record_ids, attaches_to

classification.json
  {"classes": {"<provision id>": "<class>", ...},         # anything not listed is "operative";
                                                          # 'Reserved'/'Repealed' headings default to "reserved"
   "attach":  {"<provision id>": {"to": ["<provision id>", "<record id>", "chapter", "glossary", ...],
                                  "summary": "short text"}}}
  The class of an attaching provision decides the attachment kind: fee, applicability,
  legal_effect, definition (each becomes an entry in the target records' `attachments`);
  penalty (becomes the target records' `consequence`); exemption (its id is added to the
  target records' `exceptions`). Add "kind" to a rule to override the class, e.g. a rate
  sentence inside an operative provision: {"to": [...], "kind": "fee"}. Definitions also attach
  automatically to records whose actor or counterparty is registered with `defined_in`.

extraction.jsonl line (only p, q, mod, verb/obj via "act", and sig are always needed)
  {"p": "9.10.050.C",                      provision id (a list is allowed for multi-provision records)
   "q": "verbatim quote",                  must be a substring of the provision text
   "sig": {"type": "upstream_action", "text": "after it is filed", "ref": "9.10.050.A"},
                                           ref: "<provision id>" (= its first record) or "<provision id>#<n>"
                                           type "unknown" for a missing signal (also flag O-SIG)
                                           signal confidence: add "c": "inferred" (default explicit)
   "actor": "ACT-director|The director"    "ACT-id|text" explicit; "ACT-id?|text" inferred; null = unknown (flag O-ACT)
   "mod": "duty",
   "act": ["review", "each application for completeness"]   or [verb, object, "inferred"]
   "cp": "ACT-applicant?",                 same shorthand as actor; omit or null for none
   "time": {"kind": "deadline", "amount": 5, "unit": "days", "from": "signal", "direction": "after",
            "business_days": true, "text": "within five business days"},
   "cond": ["..."], "out": ["artifact:completeness-determination"],
   "flags": ["O-SIG"], "link": {"id": "L-9.10.060.C", "rel": "alternative"},
   "conflict": ["9.10.100"], "ext": ["external:Chapter 9.30"]}
Records get ids A-<provision id>-<n>, numbered per provision in file order.

Usage:  expand.py RUN_DIR [--sheet extraction.jsonl] [--classification classification.json]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_json, read_text, write_json

KIND_OF = {"fee": "fee", "applicability": "applicability", "exemption": "exemption", "penalty": "penalty",
           "definition": "definition", "legal_effect": "legal_effect"}
TIMING_DEFAULT = {"kind": None, "amount": None, "unit": None, "from": None, "direction": None, "business_days": False, "text": None}


def actor_ref(v, errs, where):
    if v is None:
        return None
    if isinstance(v, dict):
        return {"id": v["id"], "text": v.get("text"), "confidence": v.get("confidence", "explicit")}
    m = re.match(r"^(ACT-[a-z0-9-]+)(\?)?(?:\|(.*))?$", v)
    if not m:
        errs.append(f"{where}: bad actor shorthand {v!r}")
        return None
    return {"id": m.group(1), "text": m.group(3), "confidence": "inferred" if m.group(2) else "explicit"}


def rid(ref, counts, errs, where, pids):
    """'9.10.050.A' | '9.10.060.C#2' | 'A-9.10.060.C-2' -> record id (checked after all records are numbered)."""
    if ref.startswith("A-"):
        return ref
    p, _, n = ref.partition("#")
    if p not in pids:
        errs.append(f"{where}: unknown provision {p!r} in reference {ref!r}")
    return f"A-{p}-{n or 1}"


def expand(prov, actors, classification, sheet):
    errs = []
    pd = {p["id"]: p for p in prov}
    pids = set(pd)
    actor_ids = {a["id"]: a for a in actors}
    classes = dict(classification.get("classes", {}))
    for p in prov:
        if p["id"] not in classes and re.match(r"^(Reserved|Repealed)\b", p["heading"]) and p["text"] in ("Reserved.", "Repealed."):
            classes[p["id"]] = "reserved"
    for pid in classes:
        if pid not in pd:
            errs.append(f"classification: unknown provision {pid}")
    for p in prov:
        p["class"] = classes.get(p["id"], "operative")
        p["attaches_to"] = []
        p["record_ids"] = []
    counts, records = {}, []
    for i, row in enumerate(sheet, 1):
        where = f"sheet line {i}"
        ps = row["p"] if isinstance(row["p"], list) else [row["p"]]
        for p in ps:
            if p not in pd:
                errs.append(f"{where}: unknown provision {p!r}")
        if any(p not in pd for p in ps):
            continue
        if not any(row["q"] in pd[p]["text"] for p in ps):
            errs.append(f"{where}: quote is not a verbatim substring of provision {ps[0]}")
        counts[ps[0]] = counts.get(ps[0], 0) + 1
        s = row["sig"]
        sig = {"type": s["type"], "text": s.get("text"), "confidence": None if s["type"] == "unknown" else s.get("c", "explicit")}
        if s.get("ref"):
            sig["ref"] = rid(s["ref"], counts, errs, where, pids)
        act = row["act"]
        timing = None
        if row.get("time"):
            timing = dict(TIMING_DEFAULT); timing.update(row["time"])
        link = {"link_id": row["link"]["id"], "relation": row["link"]["rel"]} if row.get("link") else None
        flags = row.get("flags", [])
        r = {"id": f"A-{ps[0]}-{counts[ps[0]]}", "provision_refs": ps, "source_quote": row["q"], "signal": sig,
             "actor": actor_ref(row.get("actor"), errs, where), "modality": row["mod"],
             "action": {"verb": act[0], "object": act[1], "confidence": act[2] if len(act) > 2 and act[2] != "explicit" else "explicit"},
             "counterparty": actor_ref(row.get("cp"), errs, where), "timing": timing, "conditions": row.get("cond", []),
             "exceptions": row.get("exceptions", []), "consequence": None, "attachments": [], "outputs": row.get("out", []),
             "status": "orphan" if flags else "complete", "orphan_flags": flags, "link": link,
             "conflict_with": [rid(c, counts, errs, where, pids) for c in row.get("conflict", [])], "resolution_note": None}
        if row.get("ext"):
            r["external_refs"] = row["ext"]
        for k in ("actor", "counterparty"):
            if r[k] and r[k]["id"] not in actor_ids:
                errs.append(f"{where}: {k} {r[k]['id']} is not in actors.json")
        records.append(r)
    ids = {r["id"] for r in records}
    for r in records:
        for ref in [r["signal"].get("ref")] + r["conflict_with"]:
            if ref and ref not in ids:
                errs.append(f"{r['id']}: reference {ref} does not exist")
    by_prov = {}
    for r in records:
        for p in r["provision_refs"]:
            by_prov.setdefault(p, []).append(r)
            pd[p]["record_ids"].append(r["id"])
    # attachments from classification
    for src, spec in classification.get("attach", {}).items():
        if src not in pd:
            errs.append(f"attach: unknown provision {src}"); continue
        kind = spec.get("kind") or KIND_OF.get(pd[src]["class"])
        if not kind and any(t not in ("chapter", "glossary") for t in spec["to"]):
            errs.append(f"attach: provision {src} has class {pd[src]['class']}, which can attach to the chapter but not to records"); continue
        summary = spec.get("summary") or pd[src]["text"][:80]
        for t in spec["to"]:
            if t in ("chapter", "glossary"):
                pd[src]["attaches_to"].append(t)
            elif t.startswith("A-") and t not in ids:
                errs.append(f"attach: {src} targets unknown record {t}")
            elif not t.startswith("A-") and t not in pd:
                errs.append(f"attach: {src} targets unknown provision {t}")
            elif not t.startswith("A-") and not by_prov.get(t):
                errs.append(f"attach: {src} targets {t}, which has no records")
            else:
                for r in ([x for x in records if x["id"] == t] if t.startswith("A-") else by_prov[t]):
                    if kind == "penalty":
                        r["consequence"] = r["consequence"] or {"provision_refs": [], "summary": summary}
                        r["consequence"]["provision_refs"].append(src)
                    elif kind == "exemption":
                        r["exceptions"].append(src)
                    else:
                        r["attachments"].append({"kind": kind, "provision": src, "summary": summary})
                    pd[src]["attaches_to"].append(r["id"])
    # automatic definition attachments via the actor registry
    for r in records:
        seen = set()
        for k in ("actor", "counterparty"):
            a = r[k]
            d = actor_ids.get(a["id"], {}).get("defined_in") if a else None
            if d and d in pd and d not in seen:
                seen.add(d)
                r["attachments"].append({"kind": "definition", "provision": d, "summary": "definition of " + a["id"][4:].replace("-", " ")})
                pd[d]["attaches_to"].append(r["id"])
    for p in prov:
        p["attaches_to"] = sorted(set(p["attaches_to"]))
        if p["class"] == "definition" and not p["attaches_to"]:
            p["attaches_to"] = ["glossary"]
    return records, prov, errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--sheet", default="extraction.jsonl")
    ap.add_argument("--classification", default="classification.json")
    ap.add_argument("--provisions", default="provisions.json")
    ap.add_argument("--actors", default="actors.json")
    ap.add_argument("--out-actions", default="actions.json")
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    sheet = []
    for no, line in enumerate(read_text(P(a.sheet)).splitlines(), 1):
        if line.strip() and not line.lstrip().startswith("#"):
            try:
                sheet.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"{a.sheet} line {no}: invalid JSON: {e}")
    records, prov, errs = expand(read_json(P(a.provisions)), read_json(P(a.actors)),
                                 read_json(P(a.classification)) if os.path.exists(P(a.classification)) else {}, sheet)
    for e in errs:
        print("ERROR", e)
    if errs:
        print(f"{len(errs)} problem(s); nothing written")
        return 1
    write_json(P(a.out_actions), records)
    write_json(P(a.provisions), prov)
    print(f"wrote {len(records)} records to {a.out_actions}; classified {len(prov)} provisions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
