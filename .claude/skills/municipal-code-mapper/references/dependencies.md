# Second-order map: dependencies between actions

Edge `A -> B` means **B depends on A**: B cannot happen, or is not due, until A has happened or
been decided. Start only after the first-order map is frozen (`validate.py --stage frozen` passes).

## What is derived and what you write

`build_deps.py` derives every `triggers` edge from the `ref` of `upstream_action` signals; do not
write them. You write all other edges in `dependencies.jsonl` (format in the script's header), one
per line, each with `basis` (explicit or inferred), `conf` and **evidence**: a short quote or the
reasoning. No evidence, no edge.

| Type | Direction | Use when | Typical evidence |
|---|---|---|---|
| `triggers` | derived | A's completion is B's stated signal | the signal text |
| `produces-input` | producer -> consumer | A's output (a license, notice, determination, filing) is what B acts on or requires | "keep such **license** posted" |
| `condition-precedent` | earlier -> later | B may or must occur only once A has occurred or been satisfied | "until such person shall have furnished the statement" |
| `temporal` | earlier -> later | The text orders them in time with no artifact passing between | "before a permit is issued" |
| `reference` | referenced -> invoker | B invokes A's procedure by citation | "as provided in Section 5.16.130" |
| `enforcement` | duty -> response | A is a duty or prohibition and B is the act that answers its breach (citation, penalty, prosecution, lien, action to recover) | "violation of any of the provisions of Chapters 5.04 through 5.24" |
| `exception-of` | overrider -> overridden | A suspends, overrides or gates B | "shall not issue … until approval" |
| `delegation` | delegator -> delegate | B is done by someone empowered through A | "the director or the director's designee" |

## Working order

1. `build_deps.py` once with no sheet, to see the derived triggers and node count.
2. Walk the artifacts. For each `outputs` name, find every record that consumes it: the license is
   consumed by the acts that require, post, carry, transfer, renew, replace or revoke it. When two
   records both produce the same artifact (two issuance provisions), connect consumers to both.
3. Walk the gates: prohibitions and "shall not … until" provisions are `exception-of` or
   `condition-precedent` edges onto the act they gate.
4. Walk enforcement: delinquency penalties, failure-to-file determinations, liens, actions to
   recover, revocation proceedings. Failure to do A leads to B.
5. Walk cross-references ("as provided in", "as set forth in"). Add resolved orphan answers
   (a corrected cross-reference) as `reference` edges with `"status": "accepted"` and the orphan id
   in the evidence.
6. Label every cycle `graph.py` reports with a `{"cycle": ...}` line (what loops, and what ends it).
7. `build_deps.py`, `validate.py --stage deps`, `graph.py --analysis-out`, then put the pending
   edges to the user with `edge_review.py RUN table`.

## Judgment rules

- **Explicit vs inferred.** Explicit only if the text states the relationship (quote it). If you
  connected two sections because they obviously belong together, it is inferred and goes to review.
- **Enforcement fan-out.** When one clause covers every violation ("any of the provisions of
  Chapters 5.04 through 5.24"), add one edge from each private-party duty or prohibition to each
  response record. It is many edges; diagrams hide the type with `--hide-types enforcement`.
- **No satisfaction loops.** Do not link a prohibition ("no business without a license") to the act
  that satisfies it (applying for the license) in the direction that makes the prohibition trigger
  the application. The license is an input to the prohibition, not the other way round.
- **Sibling records.** Two records that do the same thing (two provisions that both issue the
  license) are not linked to each other unless the text links them. Report them to the user as an
  observation.
- **Do not link through attachments.** Fees, definitions and legal effects are attached to records;
  they are not nodes. Edge them through the record they attach to.
- **Loops are information.** A renewal or revocation loop is real; label it and name the exit.
  A loop that exists only because of inferred edges is reported separately and needs review.
- **Never edge a duplicate or superseded record.** `build_deps.py` refuses.

## Review

`edge_review.py RUN table` prints the pending (inferred) edges grouped by type. Record the user's
decisions with `edge_review.py RUN apply --accept ... --reject ...` (or `--accept-all`), which
writes them into the sheet; then rebuild. Rejected edges stay in the file as `rejected` and are
ignored by the analysis and diagrams, so they are not proposed again.
