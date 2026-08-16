# Journal product audit — 2026-08-16

Status: runtime correction in progress; clinical color-threshold authority unresolved.

## Product contract

Journal is a factual history of recorded glucose measurements and their captured context. Filters and displayed units must match what the user actually selected. Historical insulin context remains backward-compatible; this page does not become a prescribing surface.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Header + active period | Immediate orientation: tells the user exactly what history scope is shown | 8.0/10 | IMPROVE — subtitle now follows 7 / 30 / all-history filter |
| 7 / 30 / all filter | Essential temporal navigation without changing source data | 9.0/10 | KEEP |
| Personal Response | Adds longitudinal interpretation, but competes with Summary if visually dominant | 6.5/10 baseline | **Decision B** — KEEP as secondary, collapsed by default, after history |
| Grouping by day | Natural chronological scan of measurements | 9.5/10 | KEEP |
| Glucose value capsule | Core factual content of Journal | 9.0/10 baseline | IMPROVE — display now respects mg/dL / mmol/L preference |
| Meal / glycemic / Ramadan / life context | Explains recorded circumstances without manufacturing context | 9.0/10 | KEEP |
| Historical insulin badge | Preserves backward-compatible factual history without turning Journal into medication entry | 8.5/10 | KEEP |
| Synchronization status | Useful provenance/state signal but visually secondary | 7.0/10 | REVIEW — no change without a new A/B/C decision |
| Tap → edit | Essential correction path for persisted factual data | 9.5/10 | KEEP |
| Swipe → confirmed delete | Necessary destructive action with explicit confirmation | 9.0/10 | KEEP |
| Hard-coded red threshold `>250 mg/dL` | Potentially useful alert hierarchy, but clinical authority/surface semantics must be governed | not scored | HOLD — no change without clinical decision |

## Verified findings

- Default filter is 30 days while the header previously said `Historique complet`.
- Stored glucose is mg/dL, but the row previously rendered `bloodSugar.toStringAsFixed(0)` regardless of `unitPreference`; mmol/L users therefore saw the wrong numerical display.
- Personal Response previously appeared before the factual history and therefore competed with the Journal's primary purpose.
- Deletion already requires explicit confirmation.
- Historical `insulinUnits` remains display-only compatibility data in Journal.
- Row coloring currently uses `val < 70 || val > 250` for red, otherwise profile target-range comparison for amber. Repository search did not establish authority for the hard-coded `250 mg/dL` red threshold. This audit does not modify it.

## Product decision — Personal Response

User arbitration: **B**.

- KEEP Personal Response.
- MOVE it after the chronological history.
- SIMPLIFY its prominence by collapsing the whole section by default.
- Load/render the full `PersonalResponseSection` only after explicit expansion.
- Do not move its interpretation into the factual history rows.

## Runtime correction

Branch: `agent/journal-product-audit`

- Header subtitle follows the selected 7-day, 30-day or all-history filter.
- mmol/L display converts stored mg/dL using `/ 18.0` and one decimal place.
- Personal Response is now a post-history secondary disclosure, collapsed by default.
- Existing clinical coloring thresholds, target ranges, treatment logic, schema and history remain unchanged.
- Anti-regression contracts: `frontend/test/features/journal_truthfulness_contract_test.dart` and the canonical mobile-header contract.

## Certification gate

No final page score or CLOSED status before exact-head CI/relevant gates, real Chrome 390×844 inspection, post-merge recertification, canonical closeout, and resolution of the clinical-threshold HOLD.

MENA roadmap numerator remains unchanged by this page audit.
