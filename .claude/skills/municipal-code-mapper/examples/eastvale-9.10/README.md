# Fixture: Eastvale Municipal Code, Chapter 9.10 Sidewalk Vending

A **fictional** chapter (40 provisions) written in the same layout as the Brisbane, CA text
exported from Municode (page headers, table of contents, repeated headings, `(Ord. …)` lines).
It exists to test the mapper against known answers, including deliberately planted defects.

`source.md` is the input. `golden/` holds the hand-authored expected outputs.

## Golden files

| File | Meaning |
|---|---|
| `provisions.json` | Expected segmentation and classification of all 40 provisions, with attachments (`segment.py` must reproduce everything except `class`, `attaches_to` and `record_ids`) |
| `actors.json` | Expected actor registry (roles as written, aliases reconciled) |
| `glossary.json` | Definitions from 9.10.020 |
| `actions.pre-resolution.json` | Expected extraction output: 29 Action Records, orphans still flagged |
| `orphans.json` | Expected orphans with best guess, plus the simulated user answer and the patch it applies |
| `actions.frozen.json` | Expected first-order map after applying the answers in `orphans.json` |
| `dependencies.json` | Expected second-order graph on the frozen map |
| `expected-analysis.json` | Roots, leaves and cycles, in explicit-only and with-inferred views |
| `coverage.json` | Expected coverage ledger |

## Planted cases

| Case | Where | Expected |
|---|---|---|
| Passive voice, no agent, and no trigger | 9.10.050.D | `O-ACT` and `O-SIG` |
| "Renew annually" with no trigger | 9.10.070.B | `O-SIG`; resolved as a duplicate of 9.10.070.C |
| "Ensure compliance" | 9.10.080.C | `O-VERB`; accepted as a known gap |
| Four-foot vs five-foot cart width | 9.10.080.E / 9.10.100 | `O-CONFLICT` (both records) |
| Reference to nonexistent Section 9.10.135 | 9.10.110 | `O-XREF`; resolved to external Chapter 9.30 |
| "May hold a hearing within 30 days" | 9.10.130.B | `O-AMBIG`; resolved to a duty |
| Standing prohibitions, permission, discretionary power | 9.10.040, 080.B, 080.D, 090.A | **No orphan** (valid signals) |
| Definitions, purpose, severability, reserved | 9.10.020, 010, 160, 150 | **No orphan** (classify and attach) |
| Fee and term provisions | 9.10.050.B, 9.10.070.A | Attached to records, not mapped |
| Alternative actors | 9.10.060.C | Two linked records (`alternative`) |
| Renewal loop and revocation loop | 9.10.070, 9.10.140 | Cycles in the explicit-only view |
| Unpaid fine blocks a permit | 9.10.060.B | Inferred edge; merges cycles in the with-inferred view |
| Chapter reference outside scope | 9.10.030 → Chapter 9.20 | External stub, not an orphan |

Not covered by this fixture: `O-CP`, `O-CLASS`, and joint (as opposed to alternative) actors.
Add synthetic unit cases for those in Phase 2/3.

## How to test

`scripts/validate.py` checks the golden files themselves (`--stage deps --actions actions.frozen.json`);
the unit tests in `tests/` run every script against them. To check a skill run against this
fixture, compare it with the golden files as below.

Explicit edges (`basis: explicit`) must match exactly. Inferred edges (`basis: inferred`) are
scored as recall: the skill should propose each of them, and may propose extras.
Free-text fields (`summary`, `evidence`, `answer`) are illustrative and not compared.

## Maintenance

The golden files are committed data, edited by hand. If you change `source.md`, update the
golden files and run the tests. Orphan patches are applied in id order and must be
self-contained (see SPEC section 6.0).
