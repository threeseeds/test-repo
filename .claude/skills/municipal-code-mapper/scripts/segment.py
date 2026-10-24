#!/usr/bin/env python3
"""Segment normalized municipal code text into a provision inventory.

A provision is a section, or a top-level lettered paragraph (A., B., ...) of a section.
Deeper nesting stays inside the parent provision's text. Ids are the section number plus
".<label>" for lettered paragraphs (e.g. 9.10.050.C).

Every input line is accounted for: noise (page furniture), structure (division/chapter/
article headings), headings, history lines, editor's notes (written to notes.json, not
provision text), body text, footnotes, or "unassigned". Nothing
is silently dropped; the report lists anything unassigned inside the body.

Regulations (profile style "cfr", see segment_cfr.py) are segmented one paragraph per provision,
with ids like 99.31.a.1.i.B; the chapter field then holds the section number.

Also writes source.clean.txt: the source without page furniture, one text line per line. Validate
provision text against this file, since provisions skip the furniture that sits inside them.

Usage:
  segment.py SOURCE.txt --out RUN_DIR [--profile profiles/municode.json | profiles/cfr.json]
                        [--chapters 5.04:5.24,5.70] [--only 99.31:a.1] [--strict]
  --chapters   scope by chapter number (or, for a regulation, by section number such as 99.3,99.30:99.33)
  --only       repeatable SECTION:PATH, keeps only that paragraph subtree (and its ancestors) of a section
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_text, write_text, read_json, write_json


SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_profile(path):
    p = read_json(path)
    for k in ("noise",):
        p[k] = [re.compile(x) for x in p[k]]
    for k in ("footnotes_marker", "history", "section_heading", "chapter_line", "division_line",
              "article_line", "footnote_marker_in_text", "reserved_heading"):
        p[k] = re.compile(p[k])
    return p


def chapter_key(c):
    a, b = c.split(".")
    return (int(a), int(b))


def parse_chapter_filter(spec):
    """'5.04:5.24,5.70' -> predicate on a chapter number."""
    if not spec:
        return lambda c: True
    ranges = []
    for part in spec.split(","):
        part = part.strip()
        if ":" in part:
            lo, hi = part.split(":")
            ranges.append((chapter_key(lo), chapter_key(hi)))
        else:
            ranges.append((chapter_key(part), chapter_key(part)))
    return lambda c: any(lo <= chapter_key(c) <= hi for lo, hi in ranges)


def segment(text, prof):
    lines = text.replace("\r\n", "\n").split("\n")
    stats = {"lines": len(lines), "blank": 0, "noise": 0, "structure": 0, "heading": 0,
             "history": 0, "body": 0, "note": 0, "footnote": 0, "front_matter_text": 0}
    unassigned = []          # (line_no, text, reason)
    sections = []            # in order of appearance
    footnotes = []
    division = chapter = article = None
    chapter_titles = {}
    sec = None               # current section dict
    cur = None               # current provision dict
    last_label = None
    in_footnotes = False
    seen_section = False
    warnings = []

    def close_prov():
        nonlocal cur
        cur = None

    for no, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s:
            stats["blank"] += 1
            continue
        if in_footnotes:
            m = re.match(r"^(\d+)\\?\.\s+(.*)$", s)
            if m:
                footnotes.append({"number": int(m.group(1)), "text": m.group(2)})
                stats["footnote"] += 1
            elif any(n.match(s) for n in prof["noise"]):
                stats["noise"] += 1
            elif footnotes:
                footnotes[-1]["text"] += " " + s
                stats["footnote"] += 1
            else:
                unassigned.append((no, s, "footnote_preamble"))
            continue
        if prof["footnotes_marker"].match(s):
            in_footnotes = True
            stats["structure"] += 1
            continue
        if any(n.match(s) for n in prof["noise"]):
            stats["noise"] += 1
            continue
        m = prof["division_line"].match(s)
        if m:
            division = m.group(1); stats["structure"] += 1; continue
        m = prof["chapter_line"].match(s)
        if m and not re.search(r"[a-z]", m.group(2)):
            if chapter != m.group(1):
                article = None
            chapter = m.group(1); chapter_titles.setdefault(chapter, m.group(2).strip().title()); stats["structure"] += 1; continue
        m = prof["article_line"].match(s)
        if m and not re.search(r"[a-z]", m.group(2)):
            article = m.group(1); stats["structure"] += 1; continue
        m = prof["section_heading"].match(s)
        if m:
            seen_section = True
            sec = {"section": m.group(1), "heading": m.group(2).rstrip("."), "chapter": chapter or ".".join(m.group(1).split(".")[:2]),
                   "division": division, "article": article, "provisions": [], "history": [], "notes": [], "line": no}
            sections.append(sec)
            cur = None; last_label = None
            stats["heading"] += 1
            continue
        if sec is None:
            stats["front_matter_text"] += 1
            unassigned.append((no, s, "front_matter"))
            continue
        if prof["history"].match(s) and not sec["notes"]:
            sec["history"].append(s)
            stats["history"] += 1
            continue
        if sec["history"]:
            # after the history line only editor's notes follow; they are not provision text
            sec["notes"].append(s)
            stats["note"] += 1
            continue
        m = re.match(r"^([A-Z])\. (.+)$", s)
        if m:
            expect = "A" if last_label is None else chr(ord(last_label) + 1)
            if m.group(1) >= expect:
                if m.group(1) > expect:
                    warnings.append((sec["section"], f"line {no}: label '{m.group(1)}.' skips '{expect}.' in {sec['section']}; "
                                    f"check the source for a run-on or missing paragraph"))
                last_label = m.group(1)
                cur = {"label": m.group(1), "text": m.group(2)}
                sec["provisions"].append(cur)
                stats["body"] += 1
                continue
            warnings.append((sec["section"], f"line {no}: '{m.group(1)}.' repeats an earlier label in {sec['section']}; kept as continuation"))
        elif last_label is not None and re.search(r"[;:] " + chr(ord(last_label) + 1) + r"\. [A-Z]", s):
            warnings.append((sec["section"], f"line {no}: possible inline paragraph '{chr(ord(last_label) + 1)}.' inside {sec['section']}.{last_label}; not split"))
        if cur is None:
            cur = {"label": None, "text": s}
            sec["provisions"].append(cur)
        else:
            cur["text"] += "\n" + s
        stats["body"] += 1
    return sections, footnotes, stats, unassigned, warnings, chapter_titles


def keep_only(label, prefixes):
    """True if the provision label is inside, or an ancestor of, one of the kept paths."""
    if label is None:
        return True
    return any(label == q or label.startswith(q + ".") or q.startswith(label + ".") for q in prefixes)


def build(sections, prof, in_scope, only=None):
    fn_re = prof["footnote_marker_in_text"]
    by_id = {}
    dup_notes = []
    for sec in sections:
        has_body = any(p["text"] for p in sec["provisions"])
        if sec["section"] in by_id:
            old = by_id[sec["section"]]
            old_body = any(p["text"] for p in old["provisions"])
            if old_body and has_body:
                dup_notes.append((sec["section"], f"{sec['section']}: two sections with text (lines {old['line']} and {sec['line']}); kept the later one"))
            elif old_body and not has_body:
                continue          # later bodyless repeat (e.g. a table of contents entry)
        by_id[sec["section"]] = sec
    ordered = sorted(by_id.values(), key=lambda x: x["line"])
    out = []
    for sec in ordered:
        if not in_scope(sec["chapter"]):
            continue
        history = " ".join(sec["history"]) or None
        provs = sec["provisions"]
        if not provs:
            provs = [{"label": None, "text": "Reserved." if prof["reserved_heading"].match(sec["heading"]) else ""}]
        if only and sec["section"] in only:
            provs = [p for p in provs if keep_only(p["label"], only[sec["section"]])]
        for p in provs:
            refs = [int(x) for x in fn_re.findall(p["text"])]
            text = fn_re.sub("", p["text"]).strip()
            pid = sec["section"] + ("." + p["label"] if p["label"] else "")
            rec = {"id": pid, "section": sec["section"], "chapter": sec["chapter"], "division": sec["division"],
                   "label": p["label"], "heading": sec["heading"], "article": sec["article"], "text": text,
                   "class": None, "attaches_to": [], "record_ids": [], "history": history}
            if refs:
                rec["footnote_refs"] = refs
            out.append(rec)
    notes = {sec["section"]: sec["notes"] for sec in ordered if sec["notes"] and in_scope(sec["chapter"])}
    return out, dup_notes, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", default=os.path.join(SKILL, "profiles", "municode.json"))
    ap.add_argument("--chapters", help="chapter scope, e.g. 5.04:5.24,5.70 (for a regulation: sections, e.g. 99.3,99.30:99.33)")
    ap.add_argument("--only", action="append", default=[], metavar="SECTION:PATH", help="keep only this paragraph subtree of a section, e.g. 99.31:a.1")
    ap.add_argument("--strict", action="store_true", help="fail if any body line is unassigned or text is empty")
    a = ap.parse_args(argv)
    raw_prof = read_json(a.profile)
    text = read_text(a.source)
    only = {}
    for o in a.only:
        sec_id, _, path = o.partition(":")
        only.setdefault(sec_id, []).append(path)
    if raw_prof.get("style") == "cfr":
        from segment_cfr import segment_cfr
        prof = dict(raw_prof)
        prof["footnote_marker_in_text"] = re.compile(raw_prof["footnote_marker_in_text"])
        prof["reserved_heading"] = re.compile(raw_prof["reserved_heading"])
        sections, footnotes, stats, unassigned, warnings, chapter_titles, clean = segment_cfr(text.replace("\r\n", "\n").split("\n"), raw_prof)
        warnings = [(sc["section"], w) for sc in sections for w in []] + [("*", w) for w in warnings]
    else:
        prof = load_profile(a.profile)
        sections, footnotes, stats, unassigned, warnings, chapter_titles = segment(text, prof)
        clean = "\n".join(l.strip() for l in text.replace("\r\n", "\n").split("\n") if l.strip() and not any(n.match(l.strip()) for n in prof["noise"])) + "\n"
    provs, dup_notes, notes = build(sections, prof, parse_chapter_filter(a.chapters), only)
    in_scope_sections = {p["section"] for p in provs}
    warnings = [m for sec_id, m in warnings + dup_notes if sec_id in in_scope_sections or sec_id == "*"]
    empty = [p["id"] for p in provs if not p["text"]]
    body_unassigned = [u for u in unassigned if u[2] != "front_matter"]
    report = {"source": os.path.abspath(a.source), "profile": prof["name"], "chapters_filter": a.chapters, "only": a.only,
              "line_stats": stats, "sections_found": len({p["section"] for p in provs}), "provisions": len(provs),
              "chapters": sorted({p["chapter"] for p in provs}, key=chapter_key),
              "per_chapter": {c: len({p["section"] for p in provs if p["chapter"] == c}) for c in sorted({p["chapter"] for p in provs}, key=chapter_key)},
              "empty_provisions": empty, "unassigned_body_lines": body_unassigned,
              "front_matter_text_lines": [u for u in unassigned if u[2] == "front_matter"], "warnings": warnings}
    os.makedirs(a.out, exist_ok=True)
    write_json(os.path.join(a.out, "provisions.json"), provs)
    write_text(os.path.join(a.out, "source.clean.txt"), clean)
    write_json(os.path.join(a.out, "chapters.json"), {c: chapter_titles.get(c, "") for c in report["chapters"]})
    if notes:
        write_json(os.path.join(a.out, "notes.json"), notes)
    if footnotes:
        write_json(os.path.join(a.out, "footnotes.json"), footnotes)
    write_json(os.path.join(a.out, "segment-report.json"), report)
    print(f"{len(provs)} provisions in {report['sections_found']} sections across {len(report['chapters'])} chapters; "
          f"{len(empty)} empty, {len(body_unassigned)} unassigned body lines, {len(warnings)} warnings")
    bad = bool(empty or body_unassigned) and a.strict
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
