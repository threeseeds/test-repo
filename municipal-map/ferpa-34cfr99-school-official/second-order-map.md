# Second-order map: 34 CFR Part 99 (FERPA) - school official exception

## Edges by type

| Type | Explicit | Inferred |
|---|---|---|
| exception-of | 2 | 1 |
| produces-input | 0 | 2 |
| reference | 10 | 0 |
| triggers | 4 | 0 |

## Analysis: explicit only

33 nodes, 16 edges.

- **Roots (entry points):** 99.4-1, 99.5.a.2-1, 99.5.b-1, 99.7.a.1-1, 99.7.b-1, 99.7.b.1-1, 99.7.b.2-1, 99.30.c.2-1, 99.31.a-1, 99.31.a.1.i.A-1, 99.31.a.1.ii-1, 99.31.a.1.ii-2, 99.32.a.4-1, 99.32.a.5-1, 99.32.b.2.i-1, 99.32.b.2.iii-1, 99.32.c.1-1, 99.32.c.2-1, 99.32.c.3-1, 99.33.a.1-1, 99.33.b.1-1, 99.33.b.2-1
- **Leaves (terminal actions):** 99.4-1, 99.5.a.2-1, 99.5.b-1, 99.7.a.1-1, 99.7.a.3.iii-1, 99.7.b-1, 99.7.b.1-1, 99.7.b.2-1, 99.30.c.1-1, 99.30.c.2-1, 99.31.a.1.ii-1, 99.31.a.1.ii-2, 99.32.a.2-1, 99.32.a.4-1, 99.32.a.5-1, 99.32.b.1-1, 99.32.b.2.ii-1, 99.32.b.2.iii-1, 99.32.c.1-1, 99.32.c.2-1, 99.32.c.3-1, 99.33.b.2-1, 99.33.d-1
- **Longest chain (4 actions):** 99.33.a.1-1 → 99.33.a.1-2 → 99.31.a.1.i.B-1 → 99.7.a.3.iii-1
- **Outputs nothing consumes:** 99.7.a.1-1, 99.7.a.3.iii-1, 99.30.a-1

No cycles.

## Analysis: with inferred

33 nodes, 19 edges.

- **Roots (entry points):** 99.4-1, 99.5.a.2-1, 99.5.b-1, 99.7.a.1-1, 99.7.b-1, 99.7.b.1-1, 99.7.b.2-1, 99.30.c.2-1, 99.31.a-1, 99.31.a.1.i.A-1, 99.31.a.1.ii-2, 99.32.a.4-1, 99.32.a.5-1, 99.32.b.2.i-1, 99.32.b.2.iii-1, 99.32.c.1-1, 99.32.c.2-1, 99.32.c.3-1, 99.33.a.1-1, 99.33.b.1-1, 99.33.b.2-1
- **Leaves (terminal actions):** 99.4-1, 99.5.a.2-1, 99.5.b-1, 99.7.a.1-1, 99.7.a.3.iii-1, 99.7.b-1, 99.7.b.1-1, 99.7.b.2-1, 99.30.c.1-1, 99.30.c.2-1, 99.31.a.1.ii-1, 99.31.a.1.ii-2, 99.32.a.2-1, 99.32.a.4-1, 99.32.a.5-1, 99.32.b.1-1, 99.32.b.2.ii-1, 99.32.b.2.iii-1, 99.32.c.1-1, 99.32.c.2-1, 99.32.c.3-1, 99.33.b.2-1, 99.33.d-1
- **Longest chain (5 actions):** 99.33.a.1-1 → 99.33.a.1-2 → 99.31.a.1.i.B-1 → 99.32.a.1-1 → 99.32.a.2-1
- **Outputs nothing consumes:** 99.7.a.1-1, 99.7.a.3.iii-1, 99.30.a-1

No cycles.

## Edges awaiting review

None.

## All edges

| Edge | From | To | Type | Basis | Status |
|---|---|---|---|---|---|
| E-001 | 99.32.a.1-1 | 99.32.a.2-1 | triggers | explicit | accepted |
| E-002 | 99.32.b.2.i-1 | 99.32.b.2.ii-1 | triggers | explicit | accepted |
| E-003 | 99.33.a.1-1 | 99.33.a.1-2 | triggers | explicit | accepted |
| E-004 | 99.33.a.1-1 | 99.33.a.2-1 | triggers | explicit | accepted |
| E-005 | 99.33.a.1-1 | 99.31.a.1.i.B-1 | reference | explicit | accepted |
| E-006 | 99.33.a.1-2 | 99.31.a.1.i.B-1 | reference | explicit | accepted |
| E-007 | 99.33.a.2-1 | 99.31.a.1.i.B-1 | reference | explicit | accepted |
| E-008 | 99.31.a.1.i.A-1 | 99.31.a.1.i.B-1 | reference | explicit | accepted |
| E-009 | 99.31.a-1 | 99.30.a-1 | exception-of | explicit | accepted |
| E-010 | 99.31.a.1.i.A-1 | 99.7.a.3.iii-1 | reference | explicit | accepted |
| E-011 | 99.31.a.1.i.B-1 | 99.7.a.3.iii-1 | reference | explicit | accepted |
| E-012 | 99.31.a.1.i.A-1 | 99.32.a.1-1 | exception-of | explicit | accepted |
| E-013 | 99.31.a.1.i.B-1 | 99.32.a.1-1 | exception-of | inferred | accepted |
| E-014 | 99.33.b.1-1 | 99.32.b.1-1 | reference | explicit | accepted |
| E-015 | 99.32.a.1-1 | 99.32.b.1-1 | reference | explicit | accepted |
| E-016 | 99.33.a.1-1 | 99.33.d-1 | reference | explicit | accepted |
| E-017 | 99.31.a.1.i.A-1 | 99.31.a.1.ii-1 | produces-input | inferred | accepted |
| E-018 | 99.31.a.1.i.B-1 | 99.31.a.1.ii-1 | produces-input | inferred | accepted |
| E-019 | 99.30.a-1 | 99.30.c.1-1 | reference | explicit | accepted |
