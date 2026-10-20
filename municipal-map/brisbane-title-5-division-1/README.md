# Brisbane, CA Municipal Code: Title 5, Division I (Chapters 5.04 to 5.24)

Obligation and dependency map produced with the `municipal-code-mapper` skill
(`.claude/skills/municipal-code-mapper`). Source: Municode export of Title 5, Supplement No. 42
(created 2026-07-01); see `provenance.json` for its hash. The normalized source text of the whole
title is not committed.

**Open the map:** `dependency-graph.html` (self-contained; open it in a browser).

## Status

| | |
|---|---|
| Provisions | 176 in 92 sections, 6 chapters (all accounted for; see `coverage.md`) |
| Action records | 128 (69 duties, 31 powers, 18 permissions, 9 prohibitions, 1 entitlement) |
| Orphans | 21, all resolved by the user's instruction "accept all best guesses" (`orphans.json` holds each answer) |
| First-order map | Frozen (`actions.frozen.json`) |
| Dependencies | 234 edges: 48 derived triggers, 186 judgment edges. All reviewed: 39 inferred edges accepted (none rejected), so none await review |

## Files

| File | What it is |
|---|---|
| `first-order-map.md` | Register of every action by section, actor, counterparty and signal type; actor-by-counterparty matrix; orphan log |
| `second-order-map.md` | Dependency report: edge counts, roots, longest chains, cycles, edges awaiting review, all edges |
| `dependency-graph.html` | Interactive graph |
| `dependency-graph.part*.mmd` | Mermaid sources, one per connected component (enforcement edges hidden) |
| `coverage.md`, `coverage.json` | Every provision, with the records or attachments that account for it |
| `provisions.json`, `provisions.frozen.json` | Segmented provisions with classes (before and after resolution attachments) |
| `actions.json`, `actions.frozen.json` | Action records before and after orphan resolution |
| `orphans.json` | The 21 orphans, best guesses, options and the recorded answers |
| `dependencies.jsonl` | Edge sheet: judgment edges with evidence and statuses, plus cycle labels |
| `dependencies.json` | The built graph (derived triggers plus the sheet) |
| `analysis.json` | Roots, leaves, cycles, longest chain, in explicit-only and with-inferred views |
| `actors.json`, `glossary.json`, `classification.json`, `extraction.jsonl` | The model's inputs to `expand.py` |
| `provenance.json`, `segment-report.json`, `chapters.json`, `notes.json`, `footnotes.json` | Intake and segmentation records |

## Judgment calls recorded in this run

- Fee and rate provisions (52) attach to the license-issuance records (5.16.060-3 and 5.16.070-1) rather than being records.
- `5.24.080` (misdemeanor) is read as covering all of Chapters 5.04 to 5.24 and attaches to the 27 private-party duties and prohibitions.
- 5.08.040.B and C (police entry and signature powers) are discretionary powers, not mandatory duties.
- `legal_effect` is a provision class added for rules with no actor or act ("deemed a debt", "final and conclusive").
- The two issuance provisions (5.16.060, 5.16.070) are not linked to each other in the text and are not linked in the map.

## Reproducing or updating

Save the Title 5 text (for example the Municode export), then follow `SKILL.md`. To re-check these files
against the source, run
`python3 -I scripts/validate.py municipal-map/brisbane-title-5-division-1 --stage deps --actions actions.frozen.json --provisions provisions.frozen.json --source <normalized source>.txt`
from the skill directory. To record decisions on inferred edges, use `scripts/edge_review.py`, then
`build_deps.py`, `graph.py`, `report.py` and `graph_html.py`.
