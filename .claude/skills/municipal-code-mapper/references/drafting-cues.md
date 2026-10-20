# Legal drafting cues

| Pattern | Meaning for the map |
|---|---|
| "shall", "must", "is required to", "it shall be the duty of" | `duty` |
| "shall not", "may not", "no X shall", "it is unlawful for" | `prohibition` |
| "may" (act is optional) | `permission`; if it changes someone's legal position, `power` |
| "shall have the power to" | `power` |
| "notwithstanding…" | the later text overrides; record as an exception in the overridden record's conditions |
| "provided, that…" / "provided, however…" | a proviso: becomes a `condition` or `exception` on the record before it |
| "unless otherwise provided" / "except as provided in Section X" | exception reference; check X exists in scope |
| "in lieu of" | one fee replaces another; attach to the superseded fee |
| "deemed", "conclusive", "final" | `legal_effect` |
| "upon", "after", "within N days of" | `upstream_action` or `event` signal plus timing |
| "working days" / "business days" | `business_days: true`; otherwise days are calendar days unless the code defines "day" |
| "he", "his", "such person" | pronoun/anaphor: resolve to the nearest actor or flag `O-ACT` |
| "or" between actors | `alternative` link |
| "and" between actors with "jointly" | `joint` link |
| "such license", "such notice" | the thing previously mentioned; the `outputs` name should match |
| "Chapters 5.04 through 5.24" | an in-scope range, not an external reference |
| "this code", "Chapter 1.14" | a cross-reference outside the run is an external stub (`external:Chapter 1.14`) |
