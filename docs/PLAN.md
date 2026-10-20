# Municipal Code Obligation Mapper — Build Plan

Companion to `SPEC.md`. Status: v1.0.

## Guiding approach

Build the deterministic scaffolding first (so quality is checkable), then the model-driven
extraction against a fixture with planted defects, then the interactive orphan loop, then
the second-order map. Run on a real chapter only after the fixture passes.

## Phases

### Phase 0 — Resolve open questions (DONE)
- SPEC §17 answered. Target: Brisbane, CA Municipal Code Title 5. Whole title per run, team use.
- **Exit:** SPEC v1.0 agreed.

### Phase 1 — Fixture, schemas, and source acquisition (DONE)
- Source: user's Google Drive file `Title_5___BUSINESS_LICENSES__TAXES_AND_REGULATIONS.docx`
  (Brisbane CA, Supp. No. 42; 18 chapters, 227 sections), read via the Drive connector and
  kept out of the repo. Municode itself is blocked from this environment.
- Source quirks for `ingest.py`/`segment.py`: repeated page headers and "Created:" footers,
  a table of contents, repeated division headings, fee tables as Markdown tables, footnotes
  at the end of the title, block references like "Chapters 5.04 through 5.24".
- Write a small fictional municipal chapter (about 25 sections) containing every
  provision class and planted defects: agentless passive, signal-less duty, vague
  "ensure compliance", dangling cross-reference, conflicting duties, a legitimate
  cycle (appeal), standing prohibition, definitions, penalties, exemptions, fees.
- Hand-build the golden outputs: provisions, actions, orphans, dependency edges.
- JSON Schemas for provisions, actions, actors, orphans, dependencies.
- **Exit:** fixture and golden files reviewed by user.

### Phase 2 — Deterministic scripts (DONE)
- `ingest.py`: file, paste and URL intake with fallback messaging.
- `segment.py`: provision inventory with stable IDs; verify no text lost.
- `validate.py`: schema, verbatim grounding, coverage invariant, reference integrity.
- `graph.py`: roots, leaves, cycles, chains, unreachable, dangling outputs, Mermaid.
- `report.py`: JSON to markdown views.
- Unit tests against the fixture.
- **Exit:** scripts pass on golden files; fail correctly on injected faults. Met: 42 tests; the
  segmenter also reproduces all 227 sections / 18 chapters of Brisbane Title 5 and passes `validate.py`.

### Phase 3 — Reference docs and SKILL.md (first-order)
- Write `references/*.md` (construct, classification, orphans, drafting cues).
- SKILL.md stages 0–5: intake, segment, classify, registries, extract, audit.
- `scripts/score.py`: compare a run to the golden files (precision/recall on records, orphan
  codes and explicit edges; inferred-edge recall) so extraction quality is measured, not eyeballed.
- Prototype the shared actor registry and glossary design for whole-title runs here.
- **Exit:** on the fixture, extraction recovers the golden actions and every planted
  orphan is flagged with the right code; no false orphans on standing prohibitions
  or definitions.

### Phase 4 — Orphan resolution loop
- Batched Q&A protocol, grouped by type, with best guess and basis.
- Bulk-rule support; write-back of resolutions; re-validation; second-round handling.
- Freeze gate for the first-order map; known-gaps carry-over.
- `scripts/resolve.py`: apply orphan patches in id order, recompute provision attachments,
  refuse to freeze while orphans are open, and reuse saved resolutions on re-runs.
- **Exit:** simulated user answers on the fixture produce a frozen map matching golden;
  re-run reuses saved resolutions with no re-asking.

### Phase 5 — Second-order map
- `references/dependencies.md` with edge types and inference heuristics.
- SKILL.md stages 7–8: edge extraction (explicit and inferred), inferred-edge review pass,
  graph analytics, reports and Mermaid output.
- **Exit:** explicit edges match the hand-built reference graph; inferred edges are
  labeled; planted cycle is detected and labeled.

### Phase 6 — Real-title pilot
- Pilot on Division I (Ch. 5.04–5.24, about 92 sections: definitions, administration,
  requirements/exemptions, application/issuance, fees, enforcement) with the user in the
  loop, then Division II chapters, then the whole title.
- Capture friction: question quality, over/under-flagging, graph readability.
- Tune prompts, orphan templates and graph splitting.
- **Exit:** user accepts first-order and second-order maps for the chapter.

### Phase 7 — Scale and team readiness
- Section-wise subagent fan-out with shared registries (needed for whole-Title-5 runs;
  prototype the registry-sharing design in Phase 3 so it is not a late surprise).
- Multi-chapter runs and external-stub replacement.
- Team docs: skill README, worked example, contributor note on golden tests.
- Optional extras (decide later): XLSX export, interactive HTML graph, plugin packaging.

## Deliverables by phase

| Phase | Deliverable |
|---|---|
| 0 | SPEC v1.0 |
| 1 | `examples/` fixture, golden files, schemas |
| 2 | `scripts/` + tests |
| 3 | `SKILL.md` (first-order), `references/` |
| 4 | Orphan loop, freeze gate |
| 5 | Second-order stages |
| 6 | Pilot report and tuned skill |
| 7 | Scale features |

## Testing strategy

- **Golden-file tests** for deterministic scripts.
- **Defect-injection tests**: delete a quote, break a reference, drop a provision; the
  validator must fail.
- **Fixture end-to-end** comparing model output to golden at the record level
  (precision and recall on records, orphan codes, edges).
- **Stability test**: re-run twice; IDs and resolutions identical.
- **Pilot review** with the user as the final judge of question usefulness.

## Open risks to watch

- Extraction recall on compound sentences.
- User fatigue in the orphan Q&A on a large chapter; mitigated by bulk rules and good
  best guesses.
- Inferred dependency edges being noisy; mitigated by labeling and a reject-and-remember
  pass.

## Next step

Start Phase 1: user supplies Title 5 text (or one chapter to start); build the fictional
fixture and schemas.
