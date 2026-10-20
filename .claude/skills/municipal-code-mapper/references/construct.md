# The construct: signal, actor, action, counterparty

One Action Record per atomic obligation. Split a sentence into several records when it has
several actors, several independent acts, or several signals. Keep one record when the pieces
cannot be separated without losing meaning.

## Atomic splitting

| Text | Records |
|---|---|
| "The license collector shall give notice… The person may apply for a hearing within 15 days… The collector shall set the hearing within 5 working days…" (5.16.050) | One per act: determine, give notice, apply for hearing, set hearing, give hearing notice, council decides, serve findings |
| "A or B shall do X" | Two records, `link: {rel: alternative}` |
| "A and B shall jointly do X" | Two records, `link: {rel: joint}` |
| "Every person… shall keep such license posted" / "Every person not having a fixed place… shall carry such license" (5.16.080) | Two records, one per paragraph: different conditions |
| "shall pay X in advance prior to issuance" | One fee attachment, not a record (see classification.md) |

If a provision lists items that are the *content* of an act (5.16.070.A–F: what the license
contains), the act is one record whose `provision_refs` lists the intro and every item; the items
need no records of their own.

## Signal: what makes the action due

Pick the type by asking "what has to be true or happen before this is due?"

| Type | Use when | Examples |
|---|---|---|
| `event` | Something occurs | "Upon observing a violation", "whenever a petition is filed" |
| `state` | A standing fact holds | "while vending", "if the amount is measured by gross receipts", "having a fixed place of business" |
| `time` | A date, period or recurrence | "on or before the last day of April, July, October and January", "annually" **with** a date; "on Monday of each week" |
| `request` | Another party asks | "within five days after demand", "upon request" |
| `upstream_action` | Another record's completion triggers it | "after the application is approved", "upon service of the notice". **Set `ref`.** |
| `discretionary` | The actor decides; valid only with `permission` or `power` | "The license collector may make administrative rules" |
| `standing` | Applies to everyone in the class at all times | "No person shall…", "It is unlawful for any person to…" |
| `unknown` | The text does not say. **Also flag `O-SIG`.** | "The permit shall be renewed." |

Rules:
- A prohibition or standing duty ("shall keep such license posted while in force") is **not**
  missing a signal. Use `standing` or `state`.
- A deadline is `timing`, not a signal. "Within 15 days after the notice" has signal
  `upstream_action` (the notice) and timing 15 days after signal. A bare "within 15 days" with no
  anchor is an `O-SIG`.
- **Do not supply a trigger the text does not state.** A duty that has only a deadline ("before
  a permit is issued", "annually") and no triggering event is signal `unknown` with `O-SIG`, even
  when one trigger is obvious (an application). Put the guess in the orphan's `best_guess`. Use
  `upstream_action` or `event` only when the text names the event ("after the application is
  filed"). Recurrence with a stated date ("on or before March 1 of each year") is `time`.
- If a signal depends on a *condition* ("if the amount is measured by gross receipts") put the
  trigger in `signal` and any extra qualifier in `conditions`.
- Prefer `upstream_action` over `event` whenever the triggering event is another mapped act. That
  link feeds the second-order map.

## Actor: who must act

Use the role as written in the code, reconciled across aliases in `actors.json` ("license
collector", "he", "the finance director" when the code defines the collector as the finance
director are one actor if the code says so). The actor is whoever the grammar makes responsible:

- "The license collector shall issue…" → license collector.
- "Any person who fails to file… shall pay…" → the generic class (`any-person` or a defined
  term). Generic actors are valid.
- Passive with no agent ("A separate license must be obtained") → **`O-ACT`**, with your best
  guess.
- Pronouns ("he", "his") refer to the nearest antecedent actor; if two are plausible, flag
  `O-ACT`.
- "Council" vs "city council" vs "the council" are one actor if the code uses them
  interchangeably; otherwise ask.
- Do not merge distinct roles because they sound alike (tax administrator vs license collector
  vs director of finance) unless the text makes them the same.
- Hierarchy ("his deputies, agents or employees") is one record on the named officer with the
  delegates noted in `action.object` or a `delegation` edge later; do not invent separate
  actors unless they have their own distinct duties.

Actor kinds: `official`, `body`, `department`, `private_party`, `tribunal`, `external_agency`,
`public_body`, `public`.

## Modality

Classify by the operative word, literally (decided with the user). Flag oddities as `O-AMBIG`
and do not decide them yourself.

| Modality | Cues |
|---|---|
| `duty` | shall, must, is required to, "it shall be the duty of", "are required to" |
| `prohibition` | shall not, may not, no X shall, unlawful to, "is prohibited" |
| `permission` | may (an act the actor is free to do, e.g. "may elect to pay under 5.20.010"), is authorized to |
| `power` | may determine, shall have the power to, may revoke, "shall have power to hear the matter" (changes someone else's legal position) |
| `entitlement` | has the right to, shall be entitled to (the counterparty-side view) |

Typical `O-AMBIG` situations: "shall have the power and it shall be their duty" (both), a
"may" with a deadline attached, "shall" for something that is obviously permissive, or "may"
where context suggests an obligation.

## Counterparty

To whom the obligation runs. Use `inferred` confidence when you supply it from context. Leave it
null when the duty runs to nobody in particular. It is rarely an orphan.

## Timing

`timing` carries the deadline/window/recurrence: `{kind, amount, unit, from, direction,
business_days, text}`. Count "working days" and "business days" as `business_days: true`. Keep
the original words in `text`. If the code defines "day" (Brisbane 5.04.070: calendar day), the
definition attaches; do not convert.

## Outputs

`outputs` names what an act produces that other acts consume: `artifact:license`,
`artifact:notice-of-assessment`, `artifact:determination`. Use short stable kebab-case names and
reuse them exactly, because dependency analysis matches them. Only list outputs the text
implies an act produces (a notice, license, determination, filing, payment); skip trivia.

## Quotes

`source_quote` must be a **verbatim** substring of the provision (or of one of its
`provision_refs`). Do not repair typos or spacing. If the act is expressed by two separated
phrases, quote the shorter span that contains the actor and the operative verb, not both.

## Confidence

Every filled field is `explicit` (the text says it) or `inferred` (you supplied it). Never mark
something explicit that you added. Inferred fields are not orphans, but a *missing* signal or
actor is an orphan even when you can guess it.
