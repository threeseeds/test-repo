#!/usr/bin/env python3
"""Render open orphans as the grouped markdown tables the user answers from.

Groups, in order: missing signals (O-SIG), missing actors (O-ACT), unclear actions (O-VERB),
then everything else. Columns: # | Provision | Quote | What the text doesn't say |
My best guess (basis) | Options. Options are lettered a, b, c in orphans.json order.

Usage:  orphan_table.py RUN_DIR [--orphans orphans.json] [--status open] [--max-words 25] [--out FILE]
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_json, write_text

GROUPS = [("Missing signals (O-SIG)", ("O-SIG",)), ("Missing actors (O-ACT)", ("O-ACT",)),
          ("Unclear actions (O-VERB)", ("O-VERB",)),
          ("Everything else", ("O-XREF", "O-AMBIG", "O-CP", "O-CONFLICT", "O-CLASS"))]


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def shorten(q, n):
    w = q.split()
    return q if len(w) <= n else " ".join(w[:n]) + " …"


def render(orphans, max_words=25):
    out = []
    counts = ", ".join(f"{t.split(' (')[0].lower()} {sum(1 for o in orphans if o['code'] in codes)}" for t, codes in GROUPS)
    out.append(f"**{len(orphans)} open orphans:** {counts}.\n")
    for title, codes in GROUPS:
        rows = [o for o in orphans if o["code"] in codes]
        if not rows:
            continue
        out.append(f"### {title}: {len(rows)}\n")
        out.append("| # | Provision | Quote | What the text doesn't say | My best guess (basis) | Options |")
        out.append("|---|---|---|---|---|---|")
        for o in rows:
            opts = "<br>".join(f"{chr(97 + i)}) {cell(t)}" for i, t in enumerate(o["options"]))
            out.append("| " + " | ".join([o["id"], cell(o["provision"]), "“" + cell(shorten(o["quote"], max_words)) + "”",
                                          cell(o["missing"]), f"{cell(o['best_guess'])} ({cell(o['basis'])})", opts]) + " |")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--orphans", default="orphans.json")
    ap.add_argument("--status", default="open")
    ap.add_argument("--max-words", type=int, default=25)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    path = a.orphans if os.path.isabs(a.orphans) else os.path.join(a.run_dir, a.orphans)
    rows = [o for o in read_json(path) if o["status"] == a.status]
    text = render(rows, a.max_words) if rows else f"No {a.status} orphans.\n"
    if a.out:
        write_text(a.out, text)
        print(f"wrote {len(rows)} {a.status} orphan(s) as tables to {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
