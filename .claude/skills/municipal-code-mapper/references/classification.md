# Provision classification

Classify every provision before extracting. Unlisted provisions default to `operative`, and
`Reserved`/`Repealed` headings default to `reserved`. `expand.py` reads `classification.json`:

```json
{"classes": {"5.04.040": "definition", "5.12.040": "exemption", "5.24.080": "penalty"},
 "attach":  {"5.12.040": {"to": ["5.12.010"], "summary": "charitable organizations are exempt"}}}
```

| Class | Use for | Handling |
|---|---|---|
| `operative` | A duty, prohibition, permission, power or entitlement for a named or generic actor | One or more records |
| `definition` | "X means…", designations like "The finance director is designated the license collector" | Glossary; attaches automatically to records whose actor/counterparty is registered with `defined_in`; otherwise `attach` it to the records that use the term, or let it fall to `glossary` |
| `purpose` | Statements of intent, findings, "enacted solely to raise revenue" | Attach to `chapter` |
| `penalty` | Criminal/civil sanction, delinquency penalty *amount*, interest rate | Becomes `consequence` on the records it sanctions; also extract any distinct enforcement acts it assigns (see below) |
| `exemption` | "shall not apply to…", "is exempt" | Its id goes into `exceptions` on the records it exempts |
| `fee` | A rate, amount, schedule or due date for a fee or tax | Attached to the record of the act that incurs it (decided with the user): for a business license, the license issuance record |
| `applicability` | Scope, term, effective-date and similar limits; relationships to other law | Attach to the records or `chapter` it limits |
| `legal_effect` | Self-executing rules with no actor or act: "shall be deemed a debt", "conclusive evidence", "final and conclusive", "remedies are cumulative", "shall not constitute a waiver", "deemed served when mailed" | Attach to the records they bear on, or `chapter` |
| `cross_reference` | Pure incorporation: "see Section X" | Attach where relevant; becomes an edge in the second-order map |
| `reserved` | Reserved / repealed | Listed in the coverage ledger |
| `unclassifiable` | You cannot tell | Orphan `O-CLASS` |

## Decision rules

1. If it tells someone to do, not do, or be allowed to do something: **operative**, even when
   it also contains an amount ("shall pay a fee of $5 for each duplicate").
2. If the *only* content is an amount, rate, schedule or due date: **fee**.
3. If a provision mixes: classify it `operative`, extract the act(s), and add an `attach` rule
   with `"kind": "fee"` (or `penalty`, etc.) from that same provision to the target record for
   the non-act content.
4. Penalty sections that assign acts ("the license collector shall add a penalty of 10% and
   collect it") are **operative** (an enforcement act with a signal); the rate is part of the
   record's `action.object` and does not need a separate attachment.
5. A section that both defines a term and imposes a duty is `operative`; add the definition as
   a note in `action.object` or attach a separate `definition` if it has its own lettered
   paragraph.
6. Definitions inside operative sections (5.20.050.B "solicitor" is defined…) are separate
   provisions when lettered: classify the lettered paragraph `definition`.
7. Numbered sub-items (`1.`, `2.` …) are inside their lettered parent and are not classified
   separately.
8. Chapter-wide boilerplate (severability, short title) is `applicability` attached to
   `chapter`.

## Fee schedules and tax rates

"Attach to the action that incurs them" means: a provision like 5.20.140.A (a $50 semiannual
fee for catering trucks) is class `fee`, attached to the record of the act that incurs it.
For Brisbane Division I that is the issuance record in 5.16.070 (the license collector issues a
license "upon payment of the prescribed fee"). Do not create "pay the fee" records.

Keep the full text of each fee provision untouched; the report lists them as attachments
with the summary you supply (keep it short: business type, amount, frequency).

Distinct *procedures* in the fee chapters are still operative: returns, record keeping,
hearings, liens, refunds, background checks, permits. Extract those as records.

## Enforcement chains

Violation → notice or citation → penalty → appeal are separate records (decided with the user),
each with its own actor and an `upstream_action` signal where the text links them.
