# Orphans: finding them, and asking about them

An orphan is a record or provision that cannot be fully expressed in the construct. Flag it in
the extraction sheet (`"flags": [...]`) and list it in `orphans.json`. Never fill the gap
silently.

| Code | Flag when | Not an orphan when |
|---|---|---|
| `O-SIG` | No trigger and no standing/discretionary reading is possible ("The license shall be renewed.") | The act is a standing prohibition or continuous duty; a deadline is stated against a clear trigger |
| `O-ACT` | Passive voice with no agent, or an ambiguous pronoun | A generic actor is named ("every person") |
| `O-VERB` | The act is not concrete ("ensure compliance", "cooperate") | The act is concrete but broad ("keep and preserve records for three years") |
| `O-CP` | The holder of a right or beneficiary is needed and the text is unclear | The duty runs to the public or to nobody in particular |
| `O-XREF` | A reference names a section that does not exist in the code you were given, or is vague ("applicable law") | The target exists in scope, or is a real section outside the run (an external stub, not an orphan) |
| `O-AMBIG` | Two readings change the map (power *and* duty; "may" with a mandatory deadline) | One reading is clearly intended |
| `O-CONFLICT` | Two provisions impose incompatible rules on the same act | They address different cases |
| `O-CLASS` | You cannot classify the provision | |

Flag at the *record* level where a record exists. A provision you cannot turn into any record
gets a stub record with `signal: unknown`, `actor: null`, or the closest fit, plus the flag.

## What a good orphan entry contains

```json
{"id": "ORP-03", "code": "O-ACT", "records": ["A-5.xx.xxx-1"], "provision": "5.xx.xxx",
 "quote": "<verbatim>", "missing": "<one line: what the text does not say>",
 "best_guess": "<your proposed value>", "basis": "<why: evidence in the text>",
 "options": ["<choice 1>", "<choice 2>", "Other"], "status": "open"}
```

`options` always has at least two entries and ends with an open choice ("Other"); write it yourself, the table script only letters the list. `quote` is verbatim text from one provision; when an orphan spans two provisions (a conflict), quote the first and name both in `provision`.

## Presenting orphans to the user: one table per group

Present all open orphans together, grouped in this order: **missing signals (O-SIG), missing
actors (O-ACT), unclear actions (O-VERB), then everything else**. One markdown table per group,
columns exactly:

| # | Provision | Quote | What the text doesn't say | My best guess (basis) | Options |
|---|---|---|---|---|---|

- `#` is the orphan id, so the user can reply "ORP-04: b".
- Quote: shortest verbatim span that shows the gap (about 25 words, ellipsis allowed).
- Options are lettered a, b, c in the order listed in `orphans.json`.
- Before the tables, state the counts per group and offer bulk rules ("treat every
  agentless 'a license shall be obtained' as the applicant").
- After the tables, tell the user how to answer: by number and letter, with free text for
  "Other", or a bulk rule.

Do not interleave questions with commentary. Do not ask about anything that is not an orphan.
If the table exceeds about 25 rows, split the response by group and continue on request.

## Recording answers

Each answer becomes a `resolution` on the orphan:
`{"type": "answer|duplicate|superseded|external|accept_gap|bulk_rule", "answer": "<user's words>",
"patch": {"<record id>": {<fields replaced>}}}`. Patches are applied in orphan-id order and must be
self-contained (set `status` and the remaining `orphan_flags`). Set the orphan `status` to
`resolved` or `known_gap`. Never mark an orphan resolved without an answer from the user or an
explicit user rule.

## Judgment calls from the Brisbane Division I run

- **Strict on passive voice.** "A permit must be obtained", "shall be served", "may be appealed":
  each is `O-ACT` with the actor left null and the likely actor in `best_guess`, even when it
  is obvious. The user would rather confirm in bulk than have it assumed. Offer a bulk rule for
  repeated patterns.
- **One orphan, several records.** When several records share one gap and one fix (four
  agentless "may be appealed" provisions), list them in a single orphan so the user answers once.
- **Provision-level orphans** (`records: []`) are allowed when the question is about scope, for
  example whether a penalty clause that says "this chapter" reaches the whole division.
- **A reference to the wrong section** (a penalties cross-reference that lands on an evidence
  rule) is `O-XREF` even though the target exists: the target does not say what the reference
  claims.
- **"Right to" an act** (the tax administrator's "right to inspect") is a `power`, not an
  `entitlement`.
- **Restatements are not orphans.** If a provision repeats a duty stated elsewhere, cover it
  through `provision_refs` of one record and mention it in the summary; do not create a duplicate.
