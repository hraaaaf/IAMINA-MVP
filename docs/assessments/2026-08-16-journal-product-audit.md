# Journal product audit — 2026-08-16

Status: runtime correction in progress; current product arbitrations resolved, certification pending.

## Product contract

Journal is a factual history of recorded glucose measurements and their captured context. Filters and displayed units must match what the user actually selected. Historical insulin context remains backward-compatible; this page does not become a prescribing surface.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Header + active period | Immediate orientation: tells the user exactly what history scope is shown | 8.0/10 baseline → 9.0/10 | IMPROVE — subtitle follows 7 / 30 / all-history filter |
| 7 / 30 / all filter | Essential temporal navigation; direct visibility reduces discovery cost versus a hidden menu | 9.0/10 baseline → 9.5/10 | **Decision B** — expose three visible ChoiceChips below the header |
| Personal Response | Adds longitudinal interpretation, but competes with Summary if visually dominant | 6.5/10 baseline → 8.5/10 | **Decision B** — KEEP as secondary, collapsed by default, after history |
| Grouping by day | Natural chronological scan of measurements | 9.5/10 | KEEP |
| Glucose value capsule | Core factual content of Journal | 9.0/10 baseline → 9.5/10 | IMPROVE — display respects mg/dL / mmol/L preference |
| Meal / glycemic / Ramadan / life context | Explains recorded circumstances without manufacturing context | 9.0/10 | KEEP |
| Historical insulin badge | Preserves backward-compatible factual history without turning Journal into medication entry | 8.5/10 | **Decision A** — KEEP visible and read-only on legacy rows |
| Synchronization status | Useful only when action or attention is required; routine success adds repeated visual noise | 7.0/10 baseline → 9.0/10 | **Decision B** — hide synced/non-actionable states; show pending/error only |
| Tap → edit | Essential correction path for persisted factual data | 9.5/10 | KEEP |
| Swipe → confirmed delete | Necessary destructive action with explicit confirmation | 9.0/10 | KEEP |
| Glucose color hierarchy | Distinguishes clinically important low glucose from ordinary out-of-target values without overclaiming urgency | 7.0/10 baseline → 9.0/10 | **Decision B** — red only below 70 mg/dL; out-of-target highs follow patient target range in amber |

## Verified findings

- Default filter is 30 days while the header previously said `Historique complet`.
- Stored glucose is mg/dL, but the row previously rendered `bloodSugar.toStringAsFixed(0)` regardless of `unitPreference`; mmol/L users therefore saw the wrong numerical display.
- Personal Response previously appeared before the factual history and therefore competed with the Journal's primary purpose.
- Synchronization previously rendered an icon even for routine `synced` state, repeating low-value status on every row.
- The range selector was previously hidden behind a tune icon, adding avoidable interaction cost for a primary Journal control.
- Deletion already requires explicit confirmation.
- Historical `insulinUnits` remains display-only compatibility data in Journal.
- Previous row coloring made both `<70 mg/dL` and `>250 mg/dL` red. ADA Standards of Care 2026 explicitly treats `<70 mg/dL` as clinically important hypoglycemia, while `>250 mg/dL` is defined in CGM reporting as a time-above-range level-2 hyperglycemia metric. That does not by itself establish a universal red-alert rule for one isolated Journal row.

## Product decision — Personal Response

User arbitration: **B**.

- KEEP Personal Response.
- MOVE it after the chronological history.
- SIMPLIFY its prominence by collapsing the whole section by default.
- Load/render the full `PersonalResponseSection` only after explicit expansion.
- Do not move its interpretation into the factual history rows.

## Product decision — synchronization status

User arbitration: **B**.

- Hide routine `synced` state from Journal rows.
- Keep `pending` visible because synchronization is not complete.
- Keep `error` visible because user attention may be required.
- Hide non-actionable fallback/unknown icon instead of presenting ambiguous cloud state.

## Product decision — glucose color hierarchy

User arbitration: **B**.

- Red is reserved for glucose `<70 mg/dL`.
- Values above the patient's configured target remain amber through the existing `val > high` branch.
- The former hard-coded `>250 mg/dL` red rule is removed from Journal.
- No treatment advice, dose logic, target value, schema, persisted data or historical value is changed.

## Product decision — historical insulin badge

User arbitration: **A**.

- Keep the legacy insulin badge visible when historical `insulinUnits` exists.
- Keep it strictly read-only in Journal.
- Medication entry remains canonical in Medications; Journal does not become an insulin-entry surface.
- No runtime change was required because the current implementation already satisfies this decision.

## Product decision — temporal filter

User arbitration: **B**.

- Expose 7-day, 30-day and all-history choices directly below the page header.
- Keep 30 days as the existing default.
- Preserve the dynamic subtitle so the active scope is stated in text as well as selection state.
- Remove the hidden popup-menu interaction for this primary control.

## Runtime correction

Branch: `agent/journal-product-audit`

- Header subtitle follows the selected 7-day, 30-day or all-history filter.
- 7 / 30 / all-history selection is exposed as visible ChoiceChips below the header.
- mmol/L display converts stored mg/dL using `/ 18.0` and one decimal place.
- Personal Response is a post-history secondary disclosure, collapsed by default.
- Journal row sync chrome is silent for `synced`/non-actionable states and visible only for `pending`/`error`.
- Red is reserved for `<70 mg/dL`; other out-of-target readings use the patient's target-range amber branch.
- Target ranges, treatment logic, schema and history remain unchanged.
- Anti-regression contracts: `frontend/test/features/journal_truthfulness_contract_test.dart` and the canonical mobile-header contract.

## Certification gate

No final page score or CLOSED status before exact-head CI/relevant gates, real Chrome 390×844 inspection, post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
