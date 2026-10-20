# Second-order map: Brisbane Title 5, Division I (chapters 5.04-5.24)

## Edges by type

| Type | Explicit | Inferred |
|---|---|---|
| condition-precedent | 4 | 13 |
| enforcement | 94 | 5 |
| exception-of | 3 | 9 |
| produces-input | 32 | 13 |
| reference | 6 | 7 |
| triggers | 48 | 0 |

## Analysis: explicit only

128 nodes, 187 edges.

- **Roots (entry points):** 5.08.020-1, 5.08.030-1, 5.08.030-2, 5.08.030-3, 5.08.040.B-1, 5.08.040.B-2, 5.08.040.C-1, 5.08.040.C-2, 5.08.050.A-1, 5.08.050.B-1, 5.08.050.B-3, 5.12.020-1, 5.12.060-1, 5.16.010-1, 5.16.020.A-1, 5.16.020.B-1, 5.16.040.A-1, 5.16.090-2, 5.16.090-3, 5.16.100-2, 5.16.110-1, 5.16.150-1, 5.16.150-2, 5.16.150-3, 5.20.015.C-1, 5.20.015.C-2, 5.20.015.D-1, 5.20.015.D-2, 5.20.015.H-1, 5.20.020-1, 5.20.060.A-1, 5.20.060.B-1, 5.20.080-1, 5.20.037-1, 5.20.040-4, 5.20.041-1, 5.20.042.B-1, 5.20.042.C-1, 5.20.043.D-1, 5.20.110.C-1, 5.20.180.B-1, 5.20.140.B-1, 5.20.140.C-1, 5.20.140.C-2, 5.20.240.B-1, 5.24.030-1, 5.24.040-1, 5.24.050-1
- **Leaves (terminal actions):** 5.08.020-1, 5.08.030-1, 5.08.030-2, 5.08.030-3, 5.08.030-4, 5.08.040.A-1, 5.08.040.A-2, 5.08.040.B-1, 5.08.040.B-2, 5.08.040.C-1, 5.08.040.C-2, 5.08.050.A-1, 5.08.050.B-2, 5.08.050.B-3, 5.12.020-2, 5.16.020.B-2, 5.16.020.C-1, 5.16.040.A-1, 5.16.040.C-1, 5.16.050-5, 5.16.050-7, 5.16.060-5, 5.16.100-1, 5.16.110-1, 5.16.120-3, 5.16.130-3, 5.16.130-5, 5.16.130-7, 5.16.140.B-3, 5.16.150-1, 5.16.150-2, 5.16.150-3, 5.20.015.C-1, 5.20.015.C-2, 5.20.015.D-2, 5.20.015.D-3, 5.20.015.H-2, 5.20.020-1, 5.20.060.A-1, 5.20.060.B-1, 5.20.080-1, 5.20.037-3, 5.20.038.C-1, 5.20.039.A-3, 5.20.039.B-4, 5.20.040-3, 5.20.040-4, 5.20.041-2, 5.20.042.A-1, 5.20.043.A-1, 5.20.043.B-4, 5.20.043.C-1, 5.20.110.D-1, 5.20.180.C-1, 5.20.110.D-2, 5.20.180.C-2, 5.20.140.B-3, 5.20.140.C-1, 5.20.140.C-3, 5.20.240.B-1, 5.24.060-1
- **Longest chain (13 actions):** 5.20.037-1 → 5.20.037-2 → 5.20.039.A-1 → 5.20.039.A-2 → 5.20.039.B-1 → 5.20.039.B-2 → 5.20.039.B-3 → 5.20.039.B-5 → 5.20.039.B-6 → 5.20.040-1 → 5.20.040-2 → 5.20.040-5 → 5.20.043.C-1
- **Outputs nothing consumes:** 5.08.020-1, 5.08.050.B-2, 5.12.080-1, 5.16.050-5, 5.16.050-7, 5.16.090-3, 5.16.130-3, 5.16.130-5, 5.16.130-7, 5.20.015.D-3, 5.20.015.H-2, 5.20.037-2, 5.20.038.C-1, 5.20.039.B-7, 5.20.040-3, 5.20.042.A-1, 5.20.043.C-1, 5.20.110.C-1, 5.20.180.B-1, 5.20.110.D-1, 5.20.180.C-1, 5.20.140.C-1, 5.20.240.B-1

No cycles.

## Analysis: with inferred

128 nodes, 234 edges.

- **Roots (entry points):** 5.08.020-1, 5.08.030-1, 5.08.030-2, 5.08.050.A-1, 5.08.050.B-1, 5.08.050.B-3, 5.12.020-1, 5.12.060-1, 5.16.010-1, 5.16.020.A-1, 5.16.020.B-1, 5.16.090-2, 5.16.090-3, 5.16.100-2, 5.16.110-1, 5.16.150-3, 5.20.015.C-1, 5.20.015.C-2, 5.20.015.D-1, 5.20.015.H-1, 5.20.020-1, 5.20.060.A-1, 5.20.060.B-1, 5.20.080-1, 5.20.037-1, 5.20.040-4, 5.20.041-1, 5.20.110.C-1, 5.20.180.B-1, 5.20.140.C-2, 5.20.240.B-1
- **Leaves (terminal actions):** 5.08.020-1, 5.08.030-1, 5.08.030-2, 5.08.030-3, 5.08.030-4, 5.08.040.A-1, 5.08.040.A-2, 5.08.040.B-1, 5.08.040.B-2, 5.08.040.C-1, 5.08.040.C-2, 5.08.050.B-3, 5.12.020-2, 5.16.020.B-2, 5.16.040.A-1, 5.16.040.C-1, 5.16.050-5, 5.16.050-7, 5.16.060-5, 5.16.100-1, 5.16.120-3, 5.16.130-3, 5.16.130-5, 5.16.130-7, 5.16.140.B-3, 5.16.150-1, 5.16.150-2, 5.16.150-3, 5.20.015.C-1, 5.20.015.D-2, 5.20.015.D-3, 5.20.015.H-2, 5.20.020-1, 5.20.060.A-1, 5.20.060.B-1, 5.20.080-1, 5.20.037-3, 5.20.039.A-3, 5.20.039.B-4, 5.20.040-3, 5.20.040-4, 5.20.041-2, 5.20.042.A-1, 5.20.043.A-1, 5.20.043.B-4, 5.20.043.C-1, 5.20.110.D-1, 5.20.180.C-1, 5.20.110.D-2, 5.20.180.C-2, 5.20.140.B-3, 5.20.140.C-1, 5.20.140.C-3, 5.20.240.B-1, 5.24.060-1
- **Longest chain (15 actions):** 5.20.037-1 → 5.20.037-2 → 5.20.038.C-1 → 5.20.039.A-2 → 5.20.039.B-1 → 5.20.039.B-2 → 5.20.039.B-3 → 5.20.039.B-5 → 5.20.039.B-6 → 5.20.040-1 → 5.20.039.B-7 → 5.20.043.B-1 → 5.20.043.B-2 → 5.20.043.B-3 → 5.20.043.B-4
- **Outputs nothing consumes:** 5.08.020-1, 5.16.050-5, 5.16.050-7, 5.16.090-3, 5.16.130-3, 5.16.130-5, 5.16.130-7, 5.20.015.D-3, 5.20.015.H-2, 5.20.039.B-7, 5.20.040-3, 5.20.042.A-1, 5.20.043.C-1, 5.20.110.C-1, 5.20.180.B-1, 5.20.110.D-1, 5.20.180.C-1, 5.20.140.C-1, 5.20.240.B-1

**Cycles**

| Cycle | Members | Exit |
|---|---|---|
| License renewal loop | 5.16.020.B-3, 5.16.020.C-1, 5.16.060-3 | the licensee furnishes the statement and pays the tax (or does not seek another license) |

## Edges awaiting review

None.

## All edges

| Edge | From | To | Type | Basis | Status |
|---|---|---|---|---|---|
| E-001 | 5.08.050.B-1 | 5.08.050.B-2 | triggers | explicit | accepted |
| E-002 | 5.12.060-1 | 5.12.060-2 | triggers | explicit | accepted |
| E-003 | 5.16.020.B-1 | 5.16.020.B-2 | triggers | explicit | accepted |
| E-004 | 5.16.040.A-2 | 5.16.040.B-1 | triggers | explicit | accepted |
| E-005 | 5.16.050-1 | 5.16.050-2 | triggers | explicit | accepted |
| E-006 | 5.16.050-2 | 5.16.050-3 | triggers | explicit | accepted |
| E-007 | 5.16.050-3 | 5.16.050-4 | triggers | explicit | accepted |
| E-008 | 5.16.050-4 | 5.16.050-5 | triggers | explicit | accepted |
| E-009 | 5.16.050-4 | 5.16.050-6 | triggers | explicit | accepted |
| E-010 | 5.16.050-6 | 5.16.050-7 | triggers | explicit | accepted |
| E-011 | 5.16.010-1 | 5.16.060-1 | triggers | explicit | accepted |
| E-012 | 5.16.010-1 | 5.16.060-2 | triggers | explicit | accepted |
| E-013 | 5.16.060-2 | 5.16.060-3 | triggers | explicit | accepted |
| E-014 | 5.16.060-4 | 5.16.060-5 | triggers | explicit | accepted |
| E-015 | 5.16.010-1 | 5.16.070-1 | triggers | explicit | accepted |
| E-016 | 5.16.120-1 | 5.16.120-2 | triggers | explicit | accepted |
| E-017 | 5.16.120-2 | 5.16.120-3 | triggers | explicit | accepted |
| E-018 | 5.16.060-4 | 5.16.130-1 | triggers | explicit | accepted |
| E-019 | 5.16.130-1 | 5.16.130-2 | triggers | explicit | accepted |
| E-020 | 5.16.130-2 | 5.16.130-3 | triggers | explicit | accepted |
| E-021 | 5.16.130-2 | 5.16.130-4 | triggers | explicit | accepted |
| E-022 | 5.16.130-2 | 5.16.130-5 | triggers | explicit | accepted |
| E-023 | 5.16.130-2 | 5.16.130-6 | triggers | explicit | accepted |
| E-024 | 5.16.130-6 | 5.16.130-7 | triggers | explicit | accepted |
| E-025 | 5.16.140.B-1 | 5.16.140.B-2 | triggers | explicit | accepted |
| E-026 | 5.16.140.B-2 | 5.16.140.B-3 | triggers | explicit | accepted |
| E-027 | 5.20.015.H-1 | 5.20.015.H-2 | triggers | explicit | accepted |
| E-028 | 5.20.037-1 | 5.20.037-2 | triggers | explicit | accepted |
| E-029 | 5.20.039.A-1 | 5.20.039.A-2 | triggers | explicit | accepted |
| E-030 | 5.20.039.A-2 | 5.20.039.A-3 | triggers | explicit | accepted |
| E-031 | 5.20.039.A-2 | 5.20.039.B-1 | triggers | explicit | accepted |
| E-032 | 5.20.039.B-1 | 5.20.039.B-2 | triggers | explicit | accepted |
| E-033 | 5.20.039.B-2 | 5.20.039.B-3 | triggers | explicit | accepted |
| E-034 | 5.20.039.B-3 | 5.20.039.B-4 | triggers | explicit | accepted |
| E-035 | 5.20.039.B-3 | 5.20.039.B-5 | triggers | explicit | accepted |
| E-036 | 5.20.039.B-5 | 5.20.039.B-6 | triggers | explicit | accepted |
| E-037 | 5.20.039.B-6 | 5.20.039.B-7 | triggers | explicit | accepted |
| E-038 | 5.20.039.B-6 | 5.20.040-1 | triggers | explicit | accepted |
| E-039 | 5.20.040-1 | 5.20.040-2 | triggers | explicit | accepted |
| E-040 | 5.20.040-2 | 5.20.040-3 | triggers | explicit | accepted |
| E-041 | 5.20.040-2 | 5.20.040-5 | triggers | explicit | accepted |
| E-042 | 5.20.042.B-1 | 5.20.042.A-1 | triggers | explicit | accepted |
| E-043 | 5.20.043.B-1 | 5.20.043.B-2 | triggers | explicit | accepted |
| E-044 | 5.20.043.B-2 | 5.20.043.B-3 | triggers | explicit | accepted |
| E-045 | 5.20.043.B-3 | 5.20.043.B-4 | triggers | explicit | accepted |
| E-046 | 5.20.043.B-3 | 5.20.043.C-1 | triggers | explicit | accepted |
| E-047 | 5.20.140.B-2 | 5.20.140.B-3 | triggers | explicit | accepted |
| E-048 | 5.20.140.C-2 | 5.20.140.C-3 | triggers | explicit | accepted |
| E-049 | 5.16.060-3 | 5.12.010-1 | produces-input | explicit | accepted |
| E-050 | 5.16.070-1 | 5.12.010-1 | produces-input | explicit | accepted |
| E-051 | 5.16.060-3 | 5.12.020-2 | produces-input | explicit | accepted |
| E-052 | 5.16.070-1 | 5.12.020-2 | produces-input | explicit | accepted |
| E-053 | 5.16.060-3 | 5.16.030-1 | produces-input | explicit | accepted |
| E-054 | 5.16.070-1 | 5.16.030-1 | produces-input | explicit | accepted |
| E-055 | 5.16.060-3 | 5.16.080.A-1 | produces-input | explicit | accepted |
| E-056 | 5.16.070-1 | 5.16.080.A-1 | produces-input | explicit | accepted |
| E-057 | 5.16.060-3 | 5.16.080.B-1 | produces-input | explicit | accepted |
| E-058 | 5.16.070-1 | 5.16.080.B-1 | produces-input | explicit | accepted |
| E-059 | 5.16.060-3 | 5.16.090-1 | produces-input | explicit | accepted |
| E-060 | 5.16.070-1 | 5.16.090-1 | produces-input | explicit | accepted |
| E-061 | 5.16.060-3 | 5.16.100-1 | produces-input | explicit | accepted |
| E-062 | 5.16.070-1 | 5.16.100-1 | produces-input | explicit | accepted |
| E-063 | 5.16.060-3 | 5.16.120-1 | produces-input | explicit | accepted |
| E-064 | 5.16.070-1 | 5.16.120-1 | produces-input | explicit | accepted |
| E-065 | 5.16.060-3 | 5.08.040.B-1 | produces-input | inferred | accepted |
| E-066 | 5.16.060-3 | 5.08.040.B-2 | produces-input | inferred | accepted |
| E-067 | 5.16.060-3 | 5.08.040.C-1 | produces-input | inferred | accepted |
| E-068 | 5.16.060-3 | 5.08.040.C-2 | produces-input | inferred | accepted |
| E-069 | 5.16.080.A-1 | 5.08.040.B-1 | produces-input | inferred | accepted |
| E-070 | 5.16.080.B-1 | 5.08.040.B-1 | produces-input | inferred | accepted |
| E-071 | 5.16.080.A-1 | 5.08.040.B-2 | produces-input | inferred | accepted |
| E-072 | 5.16.080.B-1 | 5.08.040.B-2 | produces-input | inferred | accepted |
| E-073 | 5.08.050.B-2 | 5.16.060-3 | condition-precedent | inferred | accepted |
| E-074 | 5.08.050.A-1 | 5.16.060-3 | exception-of | inferred | accepted |
| E-075 | 5.16.020.C-1 | 5.16.060-3 | exception-of | inferred | accepted |
| E-076 | 5.16.110-1 | 5.16.060-3 | exception-of | inferred | accepted |
| E-077 | 5.08.050.B-2 | 5.16.070-1 | condition-precedent | inferred | accepted |
| E-078 | 5.08.050.A-1 | 5.16.070-1 | exception-of | inferred | accepted |
| E-079 | 5.16.020.C-1 | 5.16.070-1 | exception-of | inferred | accepted |
| E-080 | 5.16.110-1 | 5.16.070-1 | exception-of | inferred | accepted |
| E-081 | 5.16.020.A-1 | 5.16.020.C-1 | condition-precedent | explicit | accepted |
| E-082 | 5.16.020.B-3 | 5.16.020.C-1 | condition-precedent | explicit | accepted |
| E-083 | 5.16.060-3 | 5.16.020.B-3 | produces-input | explicit | accepted |
| E-084 | 5.16.060-2 | 5.16.060-4 | condition-precedent | explicit | accepted |
| E-085 | 5.16.070-1 | 5.08.030-3 | condition-precedent | inferred | accepted |
| E-086 | 5.16.020.A-1 | 5.16.050-1 | enforcement | explicit | accepted |
| E-087 | 5.16.020.A-1 | 5.16.040.A-2 | produces-input | explicit | accepted |
| E-088 | 5.16.020.A-1 | 5.16.040.C-1 | produces-input | explicit | accepted |
| E-089 | 5.16.020.B-3 | 5.16.050-1 | enforcement | explicit | accepted |
| E-090 | 5.16.020.B-3 | 5.16.040.A-2 | produces-input | explicit | accepted |
| E-091 | 5.16.020.B-3 | 5.16.040.C-1 | produces-input | explicit | accepted |
| E-092 | 5.16.030-1 | 5.16.050-1 | enforcement | explicit | accepted |
| E-093 | 5.16.030-1 | 5.16.040.A-2 | produces-input | explicit | accepted |
| E-094 | 5.16.030-1 | 5.16.040.C-1 | produces-input | explicit | accepted |
| E-095 | 5.16.040.A-2 | 5.16.040.C-1 | produces-input | explicit | accepted |
| E-096 | 5.16.040.A-2 | 5.16.040.A-1 | condition-precedent | inferred | accepted |
| E-097 | 5.16.050-4 | 5.16.150-1 | condition-precedent | inferred | accepted |
| E-098 | 5.16.050-4 | 5.16.150-2 | condition-precedent | inferred | accepted |
| E-099 | 5.16.120-2 | 5.16.150-1 | condition-precedent | inferred | accepted |
| E-100 | 5.16.120-2 | 5.16.150-2 | condition-precedent | inferred | accepted |
| E-101 | 5.16.130-2 | 5.16.150-1 | condition-precedent | inferred | accepted |
| E-102 | 5.16.130-2 | 5.16.150-2 | condition-precedent | inferred | accepted |
| E-103 | 5.16.130-1 | 5.16.060-5 | reference | explicit | accepted |
| E-104 | 5.16.130-1 | 5.20.140.C-3 | reference | explicit | accepted |
| E-105 | 5.20.040-1 | 5.20.043.B-4 | reference | explicit | accepted |
| E-106 | 5.16.120-1 | 5.20.110.D-2 | reference | explicit | accepted |
| E-107 | 5.16.120-1 | 5.20.180.C-2 | reference | explicit | accepted |
| E-108 | 5.16.010-1 | 5.12.080-1 | reference | explicit | accepted |
| E-109 | 5.12.060-1 | 5.12.010-1 | exception-of | inferred | accepted |
| E-110 | 5.12.080-1 | 5.12.010-1 | exception-of | inferred | accepted |
| E-111 | 5.16.120-2 | 5.16.140.B-1 | condition-precedent | explicit | accepted |
| E-112 | 5.16.090-2 | 5.16.090-1 | exception-of | explicit | accepted |
| E-113 | 5.16.100-2 | 5.16.100-1 | condition-precedent | inferred | accepted |
| E-114 | 5.16.070-1 | 5.24.030-1 | enforcement | inferred | accepted |
| E-115 | 5.24.030-1 | 5.24.060-1 | produces-input | explicit | accepted |
| E-116 | 5.24.030-1 | 5.20.110.D-1 | reference | inferred | accepted |
| E-117 | 5.24.030-1 | 5.20.180.C-1 | reference | inferred | accepted |
| E-118 | 5.16.070-1 | 5.24.040-1 | enforcement | inferred | accepted |
| E-119 | 5.24.040-1 | 5.24.060-1 | produces-input | explicit | accepted |
| E-120 | 5.24.040-1 | 5.20.110.D-1 | reference | inferred | accepted |
| E-121 | 5.24.040-1 | 5.20.180.C-1 | reference | inferred | accepted |
| E-122 | 5.16.070-1 | 5.24.050-1 | enforcement | inferred | accepted |
| E-123 | 5.24.050-1 | 5.24.060-1 | produces-input | explicit | accepted |
| E-124 | 5.24.050-1 | 5.20.110.D-1 | reference | inferred | accepted |
| E-125 | 5.24.050-1 | 5.20.180.C-1 | reference | inferred | accepted |
| E-126 | 5.12.010-1 | 5.24.060-1 | enforcement | explicit | accepted |
| E-127 | 5.20.110.C-1 | 5.20.110.D-1 | enforcement | explicit | accepted |
| E-128 | 5.20.110.C-1 | 5.20.110.D-2 | enforcement | explicit | accepted |
| E-129 | 5.20.180.B-1 | 5.20.180.C-1 | enforcement | explicit | accepted |
| E-130 | 5.20.180.B-1 | 5.20.180.C-2 | enforcement | explicit | accepted |
| E-131 | 5.20.037-1 | 5.20.037-3 | produces-input | explicit | accepted |
| E-132 | 5.20.037-1 | 5.20.039.A-1 | enforcement | explicit | accepted |
| E-133 | 5.20.037-2 | 5.20.039.A-1 | enforcement | explicit | accepted |
| E-134 | 5.20.037-1 | 5.20.039.A-1 | reference | inferred | accepted |
| E-135 | 5.20.037-2 | 5.20.038.C-1 | enforcement | explicit | accepted |
| E-136 | 5.20.038.C-1 | 5.20.039.A-2 | produces-input | inferred | accepted |
| E-137 | 5.20.037-2 | 5.20.043.A-1 | enforcement | explicit | accepted |
| E-138 | 5.20.039.B-7 | 5.20.043.A-1 | enforcement | inferred | accepted |
| E-139 | 5.20.037-2 | 5.20.043.B-1 | enforcement | explicit | accepted |
| E-140 | 5.20.039.B-7 | 5.20.043.B-1 | enforcement | inferred | accepted |
| E-141 | 5.20.040-1 | 5.20.039.B-7 | exception-of | explicit | accepted |
| E-142 | 5.20.040-5 | 5.20.043.C-1 | produces-input | explicit | accepted |
| E-143 | 5.20.037-2 | 5.20.042.B-1 | produces-input | inferred | accepted |
| E-144 | 5.20.041-1 | 5.20.041-2 | produces-input | explicit | accepted |
| E-145 | 5.20.041-1 | 5.20.042.C-1 | produces-input | inferred | accepted |
| E-146 | 5.20.042.C-1 | 5.20.042.A-1 | exception-of | explicit | accepted |
| E-147 | 5.20.037-2 | 5.20.043.D-1 | condition-precedent | inferred | accepted |
| E-148 | 5.20.015.D-1 | 5.20.015.D-3 | produces-input | explicit | accepted |
| E-149 | 5.20.015.C-2 | 5.20.015.D-3 | produces-input | inferred | accepted |
| E-150 | 5.20.015.C-2 | 5.20.015.D-2 | produces-input | inferred | accepted |
| E-151 | 5.20.140.B-1 | 5.20.140.B-2 | produces-input | explicit | accepted |
| E-152 | 5.20.140.B-1 | 5.20.140.C-1 | condition-precedent | inferred | accepted |
| E-153 | 5.20.140.C-2 | 5.20.140.B-1 | exception-of | inferred | accepted |
| E-154 | 5.08.050.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-155 | 5.08.050.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-156 | 5.08.050.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-157 | 5.12.010-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-158 | 5.12.010-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-159 | 5.12.010-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-160 | 5.12.020-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-161 | 5.12.020-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-162 | 5.12.020-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-163 | 5.12.060-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-164 | 5.12.060-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-165 | 5.12.060-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-166 | 5.12.060-2 | 5.08.030-4 | enforcement | explicit | accepted |
| E-167 | 5.12.060-2 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-168 | 5.12.060-2 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-169 | 5.12.080-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-170 | 5.12.080-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-171 | 5.12.080-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-172 | 5.16.010-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-173 | 5.16.010-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-174 | 5.16.010-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-175 | 5.16.020.A-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-176 | 5.16.020.A-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-177 | 5.16.020.A-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-178 | 5.16.020.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-179 | 5.16.020.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-180 | 5.16.020.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-181 | 5.16.020.B-3 | 5.08.030-4 | enforcement | explicit | accepted |
| E-182 | 5.16.020.B-3 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-183 | 5.16.020.B-3 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-184 | 5.16.030-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-185 | 5.16.030-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-186 | 5.16.030-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-187 | 5.16.040.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-188 | 5.16.040.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-189 | 5.16.040.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-190 | 5.16.060-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-191 | 5.16.060-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-192 | 5.16.060-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-193 | 5.16.080.A-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-194 | 5.16.080.A-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-195 | 5.16.080.A-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-196 | 5.16.080.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-197 | 5.16.080.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-198 | 5.16.080.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-199 | 5.16.090-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-200 | 5.16.090-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-201 | 5.16.090-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-202 | 5.16.090-3 | 5.08.030-4 | enforcement | explicit | accepted |
| E-203 | 5.16.090-3 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-204 | 5.16.090-3 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-205 | 5.16.100-2 | 5.08.030-4 | enforcement | explicit | accepted |
| E-206 | 5.16.100-2 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-207 | 5.16.100-2 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-208 | 5.16.130-4 | 5.08.030-4 | enforcement | explicit | accepted |
| E-209 | 5.16.130-4 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-210 | 5.16.130-4 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-211 | 5.20.037-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-212 | 5.20.037-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-213 | 5.20.037-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-214 | 5.20.037-2 | 5.08.030-4 | enforcement | explicit | accepted |
| E-215 | 5.20.037-2 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-216 | 5.20.037-2 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-217 | 5.20.039.B-7 | 5.08.030-4 | enforcement | explicit | accepted |
| E-218 | 5.20.039.B-7 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-219 | 5.20.039.B-7 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-220 | 5.20.041-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-221 | 5.20.041-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-222 | 5.20.041-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-223 | 5.20.043.D-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-224 | 5.20.043.D-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-225 | 5.20.043.D-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-226 | 5.20.110.C-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-227 | 5.20.110.C-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-228 | 5.20.110.C-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-229 | 5.20.180.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-230 | 5.20.180.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-231 | 5.20.180.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
| E-232 | 5.20.140.B-1 | 5.08.030-4 | enforcement | explicit | accepted |
| E-233 | 5.20.140.B-1 | 5.08.040.A-1 | enforcement | explicit | accepted |
| E-234 | 5.20.140.B-1 | 5.08.040.A-2 | enforcement | explicit | accepted |
