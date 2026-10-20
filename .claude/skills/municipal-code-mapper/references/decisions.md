# Decisions already made with the user

Follow these and do not re-ask. (Source: SPEC section 17 in the repository's docs/SPEC.md.)

| Topic | Decision |
|---|---|
| Actors | The role as written in the code, with aliases reconciled in `actors.json`. No separate department or named-individual fields. |
| Joint or alternative actors | Separate linked records (`link.rel` is `joint` or `alternative`; both records share one `link.id`). |
| Enforcement | Violation, notice or citation, penalty and appeal are full records, joined by `enforcement` edges in the dependency map. |
| Shall and may | Classify by the literal operative word. Flag oddities `O-AMBIG` and let the user decide. |
| Fees and rates | Attach to the act that incurs them (for a business license, the issuance record). Do not create "pay the fee" records, except where payment is the provision's only act. |
| Passive voice | A duty or prohibition with no stated agent is `O-ACT`, with the actor left null and your guess in the orphan. |
| Scale | Work chapter by chapter with one shared actor registry and glossary, built first. |
| Orphan Q&A | Grouped tables (missing signals, missing actors, unclear actions, everything else), best guess and options, one pass. Accepting "all best guesses" is a valid answer (a `bulk_rule`). |
| Dependency edges | All kinds. Include inferred edges, labeled, and put them to the user for confirmation. |
