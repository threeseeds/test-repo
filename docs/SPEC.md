# Municipal Code Obligation Mapper — Specification

Status: v1.0 (open questions resolved; ready for Phase 1)
Skill name (proposed): `municipal-code-mapper`

## 1. Purpose

Take a chapter or article of a municipal code and decompose **every provision** into a
single analytic construct:

> **Signal → Actor → Action (→ Counterparty)**
> *What event or condition triggers an action, who is responsible for taking it, what
> exactly must/may/must not be done, and to whom is it owed?*

Anything that cannot be fully expressed in that construct is surfaced as an **orphan** and
resolved with the user. Once the first-order map is complete and frozen, build a
**second-order map**: the logical dependencies between actions (which actions are
antecedents of which others).

Two products result:

1. **First-order map** — a register of every agent action and who owes what to whom.
2. **Second-order map** — a directed graph of dependencies among those actions.

## 2. Non-goals

- Not legal advice or legal interpretation. The skill reports what the text says and flags
  ambiguity; it does not resolve ambiguity on its own authority.
- Not a compliance engine or workflow executor (the output could feed one later).
- Not amendment tracking or version diffing of code over time.
- Not a general contract/statute analyzer, although the construct may transfer.

## 3. Inputs

| Mode | Detail |
|---|---|
| Local file | PDF, DOCX, HTML, TXT, Markdown. Reliable path; preferred. |
| Pasted text | Chapter/article text pasted into the conversation. |
| URL | Municode, American Legal, eCode360, city sites. Best effort: these sites are often JavaScript-rendered and may block automated fetches. On failure the skill asks for a file or paste instead of guessing. |

**Scope per run:** one chapter/article by default; a multi-chapter title when requested.
References to sections outside the run scope are recorded as **external references**
(see §9) rather than silently dropped or invented.

The skill records the input's provenance (source, retrieval date, code supplement/
ordinance currency if stated) in every output.

## 4. Core construct: the Action Record

One record per atomic obligation/permission/etc. A single provision may yield several
records (e.g. a sentence with two "shall" clauses, or two actors). A record is the unit
that both maps are built from.

| Field | Meaning | Notes |
|---|---|---|
| `id` | Stable ID, `A-<section>-<n>` | e.g. `A-8.12.040-2` |
| `provision_refs[]` | Section/subsection/paragraph IDs it derives from | Required; ≥1 |
| `source_quote` | Verbatim text span supporting the record | Required; never paraphrased |
| `signal` | What triggers the action (see §4.1) | May be unresolved → orphan |
| `actor` | Who must/may act (see §4.2) | May be unresolved → orphan |
| `modality` | `duty`, `prohibition`, `permission`, `power`, `entitlement` | Full set (see §4.3) |
| `action` | Normalized verb phrase + object | May be unclear → orphan |
| `counterparty` | To whom owed / who is affected or benefits | Optional; see §4.4 |
| `timing` | Deadline, period, frequency, duration | e.g. "within 10 days of signal" |
| `conditions[]` | Further qualifiers beyond the triggering signal | e.g. "if the lot exceeds 1 acre" |
| `exceptions[]` | Carve-outs that suspend the action | Linked exception records |
| `consequence` | Penalty/sanction/default if not performed | Linked penalty provisions |
| `outputs[]` | Artifacts/states the action produces | Feeds second-order map |
| `status` | `complete`, `orphan`, `resolved`, `external` | |
| `orphan_flags[]` | Which gaps remain (see §6) | |
| `confidence` | `explicit` or `inferred` per field | Inferred values are visible, never hidden |
| `resolution_note` | User's answer and date, if an orphan was resolved | Provenance |

### 4.1 Signal

The trigger that makes the action due. Typed:

- **Event** — something occurs ("upon receipt of an application", "when a complaint is filed").
- **State/condition** — a standing fact ("where a building is vacant for 90 days").
- **Time** — fixed date, elapsed period, or recurrence ("annually by March 1").
- **Request** — another party asks ("upon written request").
- **Upstream action** — completion/outcome of another action ("after the director issues a
  determination"). *This type is the bridge to the second-order map (§8).*
- **Standing/continuous** — applies at all times to everyone in a class ("No person shall…").
  Recorded explicitly as `standing` so it is not mistaken for a *missing* signal.

### 4.2 Actor

The party responsible for the action. Resolved against an **actor registry** built per run so
"the director", "the Director of Public Works", and "the department head" are reconciled to
one entity or flagged as possibly distinct. Actor kinds: official/officer, body (council,
commission, board), department, private party (owner, applicant, operator, occupant, any
person), court/tribunal, external agency. Generic actors ("any person") are valid and not
orphans; *passive voice with no agent* ("a permit shall be obtained") is an orphan.

### 4.3 Modality (full set)

| Modality | Cue | Meaning |
|---|---|---|
| `duty` | shall, must, is required to | Actor is obliged to act |
| `prohibition` | shall not, may not, unlawful to | Actor is barred from acting |
| `permission` | may, is authorized to, is permitted | Actor is allowed, not obliged |
| `power` | may determine, in its discretion, has authority to | Actor can change others' legal position (grant, deny, revoke, adjudicate) |
| `entitlement` | has the right to, shall be entitled to | Counterparty holds a claim against the actor; stored as the counterparty-side view of a duty or power |

Correlatives are cross-linked: a duty of A to B has a matching entitlement of B.

### 4.4 Counterparty

"To whom" the obligation runs (the public, applicant, city, adjacent owner, a named
agency). Counterparty is *not* an orphan condition by default, because many duties run to
the public at large. It is flagged only as a **question** when the text makes it ambiguous
and it matters for the entitlement view.

## 5. Provision classification ("classify and attach")

Every provision is first classified so nothing is dropped and non-operative text is not
wrongly reported as an orphan.

| Class | Handling |
|---|---|
| **Operative** (duty/prohibition/permission/power) | Yields ≥1 Action Record |
| **Definition** | Stored in a glossary; attached to every record whose fields use the term |
| **Purpose/intent/findings** | Attached as interpretive context to the chapter; not mapped |
| **Penalty/enforcement** | Attached as `consequence` to the records it sanctions; also mapped as enforcement actions when it assigns duties (e.g. "the city attorney may prosecute") |
| **Exemption/exception** | Attached as `exceptions[]` to affected records |
| **Fee/rate schedule** | Attached to the record whose action incurs the fee |
| **Applicability/scope** | Attached to the chapter or sections it limits |
| **Cross-reference/incorporation** | Becomes an external or internal reference edge |
| **Reserved/repealed** | Logged in the coverage ledger, not mapped |
| **Unclassifiable** | Surfaced as an orphan |

**Coverage invariant:** every provision ID must appear in the coverage ledger either as
the source of ≥1 Action Record or as an attachment to ≥1 record/chapter context, or be
marked reserved/repealed. A provision that satisfies none of these is an orphan. This is
checked mechanically (§11).

## 6. Orphans

An orphan is any record or provision that cannot be fully expressed in the construct.

| Code | Orphan type | Example |
|---|---|---|
| `O-SIG` | Signal unknown | "The permit shall be renewed." (When? triggered by what?) |
| `O-ACT` | Actor unknown | "A permit shall be obtained." (By whom?) |
| `O-VERB` | Action unclear | "Owners shall ensure compliance." (What concrete act?) |
| `O-CP` | Counterparty unclear where it matters | Right asserted but holder unspecified |
| `O-XREF` | Reference unresolved | "…pursuant to Section 12.04" outside scope or nonexistent |
| `O-AMBIG` | Multiple plausible readings | "may" as permission vs. discretion |
| `O-CONFLICT` | Two provisions assign incompatible duties | |
| `O-CLASS` | Provision cannot be classified | |

Rules:

- **Standing prohibitions are not `O-SIG`.** A signal of type `standing` is valid.
- The skill proposes a **best guess** for every orphan with the evidence for it, but a
  guess is only recorded as `inferred` until the user confirms.
- Orphans are never silently resolved. Nothing becomes `resolved` without a user answer
  or an explicit user rule ("treat all unspecified actors as the City Manager").

### 6.1 Resolution Q&A (batched, grouped by type)

After extraction and before the second-order pass, the skill presents one batched
session, grouped: **missing signals → missing actors → unclear actions → everything
else**. Each item shows: provision ID, verbatim quote, what is missing, the skill's best
guess with its basis, and a short list of options plus "other". The user can answer
item-by-item or set a bulk rule that the skill applies and reports back.

Answers are written back to records (`resolution_note`), and the skill re-runs
validation. If answers surface new orphans (e.g. a resolved signal is an upstream action
that is itself unclear), a second, smaller round runs. The first-order map is **frozen**
only when there are zero open orphans or the user explicitly accepts the remainder as
"known gaps", which are then carried into the outputs.

## 7. First-order map (output)

A register of all Action Records plus views:

- **By section** — traceability to the code text.
- **By actor** — "everything the Director must/may do", the obligation load per actor.
- **By counterparty** — "who owes what to the applicant / the public" (entitlement view).
- **By signal type** — surfaces which actions are event-driven vs. clock-driven vs. standing.
- **Actor × counterparty obligation matrix.**
- **Glossary**, **coverage ledger**, **external references**, **known gaps**.

## 8. Second-order map: logical dependencies

Directed graph. Nodes = Action Records. Edge `A → B` means "B depends on A".

| Edge type | Definition | Evidence |
|---|---|---|
| `triggers` | A's completion is B's signal (signal type = upstream action) | Explicit in signal |
| `produces-input` | A produces an artifact/state (permit, determination, notice, record) that B requires | `outputs[]` ↔ B's conditions |
| `condition-precedent` | B may/must occur only if A has occurred or been satisfied | Conditions |
| `temporal` | Text orders them in time without a causal artifact ("before… after… within N days of…") | Timing |
| `reference` | B explicitly invokes or incorporates A by citation | Cross-references |
| `enforcement` | A is a duty; B is the response to its breach (violation → notice → penalty → appeal) | Consequence links |
| `exception-of` | A suspends or overrides B | Exceptions |
| `delegation` | A empowers an actor to perform B | Powers |

**Explicit and inferred edges are both included**, per the "all kinds" scope, but every
edge carries `basis: explicit | inferred` and a `confidence`, plus the supporting quote
or reasoning. Inferred edges are reviewable in a short confirm/reject pass, and rejected
edges are retained as `rejected` so they are not re-proposed on re-runs.

**Graph analyses** (deterministic, scripted):

- **Roots** — actions with no antecedent (spontaneous, standing, or externally triggered).
  These are the system's entry points.
- **Leaves/terminals** — actions with no dependants.
- **Critical chains** — longest dependency chains (e.g. application → completeness review
  → hearing → decision → appeal → ...).
- **Cycles** — flagged, not fatal (appeals and renewals legitimately loop); each cycle is
  labeled and checked for a stated exit.
- **Unreachable actions** — actions whose antecedent is never produced by any mapped
  action (candidate gaps or external dependencies).
- **Dangling outputs** — artifacts produced but never consumed.
- **Cross-boundary edges** — to/from sections outside the run scope.

## 9. External references

References to code outside the run scope are stored as stub nodes (`external:<cite>`) so
edges remain intact. In a multi-chapter run, stubs are replaced by real nodes. The skill
never invents the content of an unseen section.

## 10. Output artifacts

All written to an output directory (default `municipal-map/<chapter-slug>/`):

| File | Content |
|---|---|
| `provisions.json` | Segmented provision inventory with stable IDs and classes |
| `actions.json` | All Action Records (schema in §12) |
| `actors.json` | Actor registry with aliases |
| `glossary.json` | Definitions |
| `orphans.json` | Orphan list with status, guesses, resolutions |
| `dependencies.json` | Edge list with type, basis, confidence |
| `coverage.md` | Coverage ledger: each provision → records/attachments |
| `first-order-map.md` | Human-readable register and views (§7) |
| `second-order-map.md` | Human-readable dependency report and analyses (§8) |
| `dependency-graph.mmd` | Mermaid source, large graphs split per actor or subsystem |
| `run-log.md` | Inputs, decisions, user rules, open known gaps |

## 11. Quality controls

1. **Verbatim grounding** — every record has `source_quote` that must be a literal
   substring of the source text (scripted check).
2. **Coverage invariant** (§5) checked mechanically; run fails loudly on any unaccounted
   provision.
3. **Schema validation** of all JSON.
4. **No silent inference** — inferred fields are marked; the user's confirmations are
   recorded.
5. **Actor consistency** — all actor references resolve into the registry.
6. **Reference integrity** — every edge endpoint exists (internal node or external stub).
7. **Determinism where possible** — segmentation, IDs, coverage, schema, graph analytics
   and Mermaid generation are scripts; only classification and extraction are model work.
8. **Spot-check sample** — at freeze time, the skill shows N random records alongside
   their source text for the user to eyeball.

## 12. Data schema (sketch)

```json
{
  "id": "A-8.12.040-2",
  "provision_refs": ["8.12.040(B)"],
  "source_quote": "Within ten days after receipt of a complete application, the director shall issue or deny the permit.",
  "signal": { "type": "upstream_action", "ref": "A-8.12.030-1", "text": "receipt of a complete application", "confidence": "explicit" },
  "actor": { "id": "ACT-director", "text": "the director", "confidence": "explicit" },
  "modality": "duty",
  "action": { "verb": "issue or deny", "object": "permit", "confidence": "explicit" },
  "counterparty": { "id": "ACT-applicant", "confidence": "inferred" },
  "timing": { "kind": "deadline", "amount": 10, "unit": "days", "from": "signal" },
  "conditions": [],
  "exceptions": [],
  "consequence": null,
  "outputs": ["artifact:permit-decision"],
  "status": "complete",
  "orphan_flags": []
}
```

## 13. Skill packaging

```
.claude/skills/municipal-code-mapper/
  SKILL.md                 # workflow, when to trigger, stage gating, Q&A protocol
  references/
    construct.md           # signal/actor/action/modality definitions with examples
    classification.md      # provision classes and edge cases
    orphans.md             # orphan taxonomy and question templates
    dependencies.md        # edge types and inference heuristics
    legal-drafting-cues.md # shall/may/must, passive voice, "provided that", etc.
  scripts/
    ingest.py              # file/URL/paste → normalized text with structure
    segment.py             # text → provision inventory with stable IDs
    validate.py            # schema, grounding, coverage, reference integrity
    graph.py               # roots, leaves, cycles, chains, mermaid output
    report.py              # JSON → markdown views
  schemas/*.schema.json
  examples/                # small fictional chapter with golden outputs
```

**Division of labor:** scripts do everything checkable; the model does classification,
extraction, normalization of actors, best-guess proposals and inferred edges. For long
chapters the skill fans out extraction by section to subagents, with the actor registry
and glossary built first and shared so naming stays consistent.

## 14. Workflow and gates

| Stage | Output | Gate |
|---|---|---|
| 0 Intake | Normalized text, provenance | Confirm scope and source |
| 1 Segment | Provision inventory | Script check: no text lost |
| 2 Classify | Class per provision | — |
| 3 Build glossary and actor registry | Registries | User glance at actor list |
| 4 Extract | Action Records | Grounding + schema validation |
| 5 Audit | Coverage ledger, orphan list | Coverage invariant passes |
| 6 **Resolve orphans** | Batched Q&A | Zero open orphans or accepted known gaps → **freeze first-order map** |
| 7 Dependencies | Edges + analyses | Inferred-edge review |
| 8 Report | All outputs | Spot-check sample |

The second-order stage does **not** begin until the first-order map is frozen.

## 15. Acceptance criteria

- On a fixture chapter, 100% of provisions appear in the coverage ledger.
- 100% of records have a verbatim, locatable `source_quote`.
- Planted defects in the fixture (an agentless passive, a signal-less duty, a vague
  "ensure compliance", a dangling cross-reference, a cycle) are all surfaced as the
  correct orphan types.
- Standing prohibitions and definitions are *not* falsely reported as orphans.
- Dependency graph for the fixture matches a hand-built reference graph on explicit edges.
- Re-running with saved resolutions produces identical IDs and no re-asked questions.

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Model over-confidently fills in missing actors/signals | Inferred marking; orphans never auto-resolve; guesses shown but unconfirmed |
| Long chapters exceed context | Section-wise extraction with shared registries; scripts hold state on disk |
| URL sources unreliable | File/paste fallback; clear failure message |
| Inconsistent actor naming across sections | Registry first, aliases reconciled, flagged merges |
| Huge unreadable graphs | Split by actor/subsystem; summary-level graph plus detail graphs |
| One sentence → many obligations | Atomic splitting rule; records link to shared provision |
| Interpretive disputes ("may" vs "shall" in context) | `O-AMBIG`, not silently decided |

## 17. Decisions (resolved)

| # | Question | Decision |
|---|---|---|
| 1 | First real target | **Brisbane, California Municipal Code, Title 5 (Business Licenses, Taxation and Regulations)**, https://library.municode.com/ca/brisbane/codes/municipal_code?nodeId=TIT5BULITARE |
| 2 | Actor granularity | **Role as written**, with aliases reconciled in the actor registry. No separate department or named-individual fields. |
| 3 | Joint/alternative actors | **Separate linked records**, tagged `joint` or `alternative` with a shared link ID. |
| 4 | Enforcement | **Full actions in the graph** (violation, notice/citation, penalty, appeal), connected by `enforcement` edges. |
| 5 | Shall vs. may | **Literal word, flag oddities** as `O-AMBIG` for the user to decide. |
| 6 | Fees and rates | **Attach to the action that incurs them.** No separate payment records. |
| 7 | Scale | **Whole Title 5 in one run** (many chapters). Section-wise extraction with shared registries is a core requirement, not an extra. |
| 8 | Audience | **Team.** Skill lives in the repo (`.claude/skills/`) so teammates get it on checkout; needs usage docs and a worked example. |

### 17.1 Consequences of the decisions

- **Municode access.** From the cloud environment, `library.municode.com` is blocked by the
  network policy (proxy returns 403), so URL intake cannot be relied on here. The skill
  keeps URL mode for environments that allow it, but the supported path for Title 5 is
  files or pasted text per chapter. User supplies the text (e.g. Municode's per-chapter
  or full-title download, or copy/paste).
- **Multi-chapter run.** Cross-chapter references inside Title 5 resolve to real nodes
  rather than external stubs; only references outside Title 5 (other titles, state law
  such as the California Business and Professions Code) remain external stubs.
- **Processing order.** Pass 1 builds title-wide glossary and actor registry (definitions
  chapters first); pass 2 extracts per chapter, in parallel where possible; orphan
  Q&A is batched per chapter, with bulk rules carried across chapters; the dependency
  pass runs once on the frozen title-wide map.
- **Team use.** Add `README` usage notes under the skill, the worked fixture example, and
  a short contributor note on how the golden tests work.
