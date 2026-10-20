---
name: municipal-code-mapper
description: Parse a municipal code chapter, article or title into signal → actor → action → counterparty records, surface orphans (missing signal, missing actor, unclear action, bad reference, conflict) as a table for the user to resolve, then map the first-order obligations. Use when the user wants to decompose a municipal code, ordinance or similar regulatory text into who must do what, when, and to whom, or asks for an obligation map, orphan check, or dependency map of a code. Needs the code text as a file or pasted text.
---

# Municipal code mapper

Turns code text into this construct, one record per atomic obligation:

> **Signal** (what triggers it) → **Actor** (who is responsible) → **Action** (what must/may/must not be done) → **Counterparty** (to whom)

Anything that does not fit becomes an **orphan** and is put to the user in a table. Once the
orphans are resolved the first-order map is **frozen**; only then is the second-order
(dependency) map built. Full design: `docs/SPEC.md` at the repository root. Decisions already made
with the user are in SPEC section 17; follow them and do not re-ask.

Status: stages 0 to 6 below work. Stages 7 and 8 (dependency map) come in a later phase.

## Ground rules

- **Never invent.** Quotes are verbatim. A missing signal, actor or action is an orphan, never
  silently filled in. Anything you supply is marked `inferred`.
- **Do not interpret the law.** Report what the text says; ambiguity goes to the user.
- **Roles as written.** Actors are the role names the code uses, with aliases reconciled.
- **Literal modality.** Classify by the operative word; flag oddities `O-AMBIG`.
- **Fees attach; they are not records.** Enforcement steps are full records.
- **Do not spawn subagents** unless the user asks. Work chapter by chapter.
- Work in a run directory, default `municipal-map/<scope-slug>/`. Keep source text out of the repository.

Scripts are in `scripts/` (Python 3, `jsonschema` needed for `validate.py`). Run them as
`python3 -I <skill dir>/scripts/<name>.py`. `scripts/README.md` documents each one. Read the
references when you reach the stage that needs them:
`references/construct.md` (fields, signal types, splitting), `references/classification.md`,
`references/orphans.md` (flags, table format), `references/drafting-cues.md`.

## Workflow

### 0. Intake: confirm scope and source
Ask only what you need: which code text (file or pasted), and which chapters/articles. If the
user gives a URL, try `ingest.py`; if it fails (JavaScript pages, blocked network) ask for a file
or pasted text.
```
ingest.py INPUT --out RUN          # RUN/source.txt, RUN/provenance.json
```
Tell the user the supplement/date the text states.

### 1. Segment
```
segment.py RUN/source.txt --out RUN [--chapters 5.04:5.24] --strict
validate.py RUN --stage segment --source RUN/source.txt
```
Read `segment-report.json`. Resolve every warning before going on: tell the user about run-on
paragraphs or unplaced lines. Nothing is dropped silently. Confirm section/provision counts per
chapter with the user if they look wrong.

### 2. Registries (do this once, before any extraction)
Read the definitions and administration chapters first. Write:
- `RUN/actors.json`: every actor and counterparty role, with `aliases` and `defined_in` (the
  provision that defines or designates the role). Include generic actors ("any person", "the
  public") and external agencies. See `schemas/actor.schema.json`.
- `RUN/glossary.json`: `{term, provision, text}` for each defined term.

Add actors as you meet them in later chapters; never rename an existing id. Show the user the
actor list in one line each and take corrections before continuing.

### 3. Classify
Write `RUN/classification.json` (format and rules in `references/classification.md`). Classify
every provision; list only non-operative ones (plus `attach` rules).

### 4. Extract, chapter by chapter
For each chapter write one line per Action Record into `RUN/extraction.jsonl` (format in the
header of `scripts/expand.py`; field rules in `references/construct.md`). Work one chapter at a
time so references stay accurate, appending lines in provision order. Then:
```
expand.py RUN                      # writes actions.json, updates provisions.json
```
Fix every error `expand.py` reports (it writes nothing until clean). A passive duty or
prohibition with no stated agent is flagged `O-ACT` even when the actor is obvious; leave the
record's `actor` null and put your guess in the orphan.

### 5. Audit
Write `RUN/orphans.json` for every flagged record plus any provision you could not classify
(format in `references/orphans.md`). Then:
```
validate.py RUN --stage extract --source RUN/source.txt
```
Fix every problem. Coverage must be complete: each provision is the source of a record, attached
to one, or reserved.

### 6. Resolve orphans with the user (one table per group)
Render the tables with `orphan_table.py RUN` and paste them as the response, grouped as
`references/orphans.md` specifies (`# | Provision | Quote | What the text doesn't say | My best guess (basis) | Options`).
Group records that share one pattern into a single orphan (for example four agentless "may be
appealed" provisions) and offer a bulk rule.
Wait for answers. Record each as a `resolution` on its orphan (`type`, `answer`, a self-contained
`patch`), set the orphan `status` to `resolved` or `known_gap`, and write the file. Then freeze:
```
resolve.py RUN                     # applies patches in id order -> actions.frozen.json, provisions.frozen.json
validate.py RUN --stage frozen --actions actions.frozen.json --provisions provisions.frozen.json --source RUN/source.txt
report.py RUN --actions actions.frozen.json --provisions provisions.frozen.json --title "<scope>"
```
`resolve.py` refuses to freeze while any orphan is open and never edits its inputs, so changing an
answer and re-running reproduces the map. If answers create new orphans, ask again, smaller.
`accept_gap` keeps the record's flag and sets `status: known_gap`. A bulk rule from the user
("accept all best guesses") is recorded as `type: bulk_rule` on each orphan it covers; compute
any patch that depends on other answers from the frozen state of those answers.
Show the user the frozen map's summary and a sample of 5 records beside their source text so they
can spot-check. The first-order map is frozen when `--stage frozen` passes.

### 7–8. Dependency map (not yet built)
Tell the user the second-order map is the next phase. Do not start it before the first-order
map is frozen.

## What to tell the user at each gate

- After stage 1: provisions and sections per chapter, any warnings.
- After stage 5: records by modality, counts of orphans by code, and any assumption you made that
  the user should know about (e.g. "rate provisions are attached to the license issuance record").
- After stage 6: counts resolved / known gaps, and the path to the reports.

Keep summaries short; findings live in the files and reports.
