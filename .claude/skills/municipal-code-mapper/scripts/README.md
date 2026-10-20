# Scripts

Deterministic tooling for the municipal code mapper. Anything checkable lives here; the model
does classification, extraction, best-guess proposals and inferred edges. All scripts use only
the Python standard library, except `validate.py`, which needs `jsonschema`
(`pip install jsonschema`). Run them in isolated mode: `python3 -I scripts/<name>.py`.

## Pipeline and run directory

```
ingest.py   INPUT --out RUN          -> source.txt, provenance.json
segment.py  RUN/source.txt --out RUN -> provisions.json, notes.json, footnotes.json, segment-report.json
            (model: write actors.json, glossary.json, classification.json, extraction.jsonl)
expand.py   RUN                      -> actions.json (+ provisions.json classified and linked)
            (model: write orphans.json)
validate.py RUN --stage extract      -> checks the model's output
orphan_table.py RUN                  -> the tables shown to the user
            (user: resolve orphans; patches applied; records frozen)
validate.py RUN --stage frozen
            (model: propose dependencies.json)
validate.py RUN --stage deps
graph.py    RUN --analysis-out analysis.json --mermaid dependency-graph.mmd
report.py   RUN --title "Brisbane Title 5" -> first-order-map.md, second-order-map.md, coverage.md/json
```

| Script | What it does |
|---|---|
| `ingest.py` | Normalizes .txt/.md, .html, .docx, .pdf (needs `pdftotext`), stdin or a URL into `source.txt`, and records origin, hash, time and the code supplement/date the text states. A failed or JavaScript-only URL exits 2 with instructions to supply a file. |
| `segment.py` | Splits text into provisions (a section, or a top-level lettered paragraph) with stable ids like `5.16.020.A`. Strips page furniture using a profile (`profiles/municode.json`), tracks division/chapter/article, attaches history lines, moves editor's notes to `notes.json`, handles reserved sections and table-of-contents repeats, and reports any line it could not place. `--chapters 5.04:5.24,5.70` limits scope; `--strict` fails on empty provisions or unplaced lines. |
| `expand.py` | Expands the model's terse extraction sheet (`extraction.jsonl`) and `classification.json` into full records, assigns ids, resolves cross-references, applies fee/penalty/exemption/legal-effect attachments, and updates `provisions.json`. Writes nothing if any quote is not verbatim or any reference is dangling. Format in the script header. |
| `validate.py` | Schema validation and the spec's integrity checks: verbatim quotes, the coverage invariant, actor and reference integrity, orphan/flag consistency, no open orphans at freeze, graph endpoints, and triggers-edge consistency. `--json` for machine output. Exit 1 on any problem. |
| `graph.py` | Roots, leaves, cycles, longest chain, dangling outputs and external dependencies, in two views (explicit edges only, and with inferred edges). Renders Mermaid, splitting large graphs into components. `--group chapter\|actor`, `--hide-types enforcement`. |
| `orphan_table.py` | Renders open orphans as the grouped tables the user answers from (missing signals, missing actors, unclear actions, everything else), with lettered options. |
| `score.py` | Scores a run against golden files: classification accuracy, record precision/recall, field accuracy, orphan precision/recall, explicit-edge precision/recall. |
| `report.py` | Renders the first-order register and views, the second-order report with labeled cycles and edges awaiting review, and the coverage ledger. |

## Adding a code publisher

Page furniture differs by publisher. Copy `profiles/municode.json`, change the `noise` and
heading patterns, and pass it with `segment.py --profile`. Test it against a real sample plus
the fixture before relying on it.

## Tests

```
python3 -I -m unittest discover -s tests -t tests
TITLE5_TEXT=/path/to/title5.txt python3 -I -m unittest discover -s tests -t tests   # also runs the real-text test
```

Tests cover each script against the Eastvale fixture's golden files, injected faults the
validator must reject, and synthetic edge cases (run-on paragraph labels, editor's notes,
chapter filters, 6000-node chains).
