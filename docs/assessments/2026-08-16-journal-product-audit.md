# Journal product audit — 2026-08-16

Status: runtime correction in progress; SMART product review complete; certification pending.

## Product contract

Journal is a factual history of recorded glucose measurements and their captured context. Filters and displayed units must match what the user actually selected. Historical insulin context remains backward-compatible; this page does not become a prescribing surface.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Header + active period | Immediate orientation: tells the user exactly what history scope is shown | 8.0/10 baseline → 9.0/10 | IMPROVE — subtitle follows 7 / 30 / all-history filter |
| 7 / 30 / all filter | Essential temporal navigation; direct visibility reduces discovery cost versus a hidden menu | 9.0/10 baseline → 9.5/10 | **Decision B** — expose three visible ChoiceChips below the header |
| History query truthfulness | Determines whether the visible period actually contains every eligible stored row | 6.5/10 baseline → 9.7/10 | IMPROVE — remove arbitrary year-2000 floor and include legacy `loggedAt == null` rows via `createdAt` fallback without rewriting data |
| Empty state | First-use orientation and fastest route to making Journal useful | 8.5/10 baseline → 9.5/10 | **Decision B / autonomous recommendation** — Add reading primary + Import secondary |
| Loading skeleton | Preserves layout stability while local Drift stream resolves | 9.0/10 | KEEP — useful, low-noise, no fabricated clinical data |
| Personal Response | Adds longitudinal interpretation, but competes with Summary if visually dominant | 6.5/10 baseline → 8.5/10 | **Decision B** — KEEP as secondary, collapsed by default, after history |
| Grouping by day | Natural chronological scan of measurements | 9.5/10 | KEEP |
| Glucose value capsule | Core factual content of Journal; numerical value without its unit is incomplete | 9.0/10 baseline → 9.7/10 | IMPROVE — convert mmol/L correctly and print the active unit beside every value |
| Meal / glycemic / Ramadan context | Explains recorded circumstances but full chips + description made rows unnecessarily dense | 9.0/10 baseline → 9.5/10 | **Decision B** — keep primary context + compact one-line meal summary; full details on tap |
| Life-context indicators | Fast scan for illness, stress, fatigue, activity and sleep context | 8.0/10 baseline → 9.2/10 | IMPROVE — preserve compact emoji but add localized screen-reader semantics |
| Historical insulin badge | Preserves backward-compatible factual history without turning Journal into medication entry | 8.5/10 | **Decision A** — KEEP visible and read-only on legacy rows |
| Synchronization status | Useful only when action or attention is required; routine success adds repeated visual noise | 7.0/10 baseline → 9.0/10 | **Decision B** — hide synced/non-actionable states; show pending/error only |
| Tap → edit | Essential correction/detail path for persisted factual data; affordance should be visible | 9.5/10 baseline → 9.8/10 | **Decision B** — keep whole-row tap and add a discreet chevron |
| Delete access | Destructive action must be discoverable but guarded | 9.0/10 baseline → 9.5/10 | **Decision B** — keep swipe + confirmation and add confirmed delete in detail/edit |
| Glucose color hierarchy | Distinguishes clinically important low glucose from ordinary out-of-target values without overclaiming urgency | 7.0/10 baseline → 9.0/10 | **Decision B** — red only below 70 mg/dL; out-of-target highs follow patient target range in amber |

## Verified findings

- Default filter is 30 days while the header previously said `Historique complet`.
- `Tout` previously used an arbitrary `DateTime(2000)` lower bound.
- `LogEntries.loggedAt` is nullable because it was introduced after the original schema; the generic range watcher filters on `loggedAt`, so legacy rows with `loggedAt == null` could disappear despite the Journal itself already using `loggedAt ?? createdAt` for presentation.
- Stored glucose is mg/dL, but the row previously rendered `bloodSugar.toStringAsFixed(0)` regardless of `unitPreference`; mmol/L users therefore saw the wrong numerical display.
- Even after numerical conversion, rows previously omitted the unit label, leaving the displayed number context-dependent.
- Personal Response previously appeared before the factual history and therefore competed with the Journal's primary purpose.
- Synchronization previously rendered an icon even for routine `synced` state, repeating low-value status on every row.
- The range selector was previously hidden behind a tune icon, adding avoidable interaction cost for a primary Journal control.
- Meal rows could render every food chip plus a two-line free-text description in addition to the primary context, increasing scan density.
- Life-context emoji were visually compact but lacked explicit accessibility semantics.
- The full row was tappable for detail/edit, but no visible affordance signaled that interaction.
- Swipe delete already required explicit confirmation, but deletion was not discoverable from the detail/edit screen.
- Historical `insulinUnits` remains display-only compatibility data in Journal.
- Previous row coloring made both `<70 mg/dL` and `>250 mg/dL` red. ADA Standards of Care 2026 explicitly treats `<70 mg/dL` as clinically important hypoglycemia, while `>250 mg/dL` is defined in CGM reporting as a time-above-range level-2 hyperglycemia metric. That does not by itself establish a universal red-alert rule for one isolated Journal row.

## Product decisions

- **Personal Response — B:** keep it, move it after history, collapse it by default and load its full section only after expansion.
- **Synchronization status — B:** hide routine `synced` and ambiguous non-actionable states; keep `pending` and `error` visible.
- **Glucose color hierarchy — B:** reserve red for `<70 mg/dL`; other out-of-target values use the existing patient-target amber branch.
- **Historical insulin badge — A:** keep legacy insulin visible and strictly read-only; no runtime change was required because the implementation already satisfies this.
- **Temporal filter — B:** expose 7-day, 30-day and all-history choices as visible ChoiceChips below the header; keep 30 days as default and preserve the dynamic subtitle.
- **Meal/context density — B:** keep the primary context, summarize at most two localized food labels plus `+N` on one line, fall back to one-line free text when no catalog foods exist, and leave complete detail accessible through row tap.
- **Tap affordance — B:** keep the whole row tappable and add a discreet chevron to signal detail/edit navigation.
- **Deletion access — B:** keep swipe-to-delete with confirmation and add a secondary destructive button in detail/edit using the same irreversible-action confirmation before `deleteLog`.
- **Empty state — B / autonomous recommendation:** keep Add reading primary and expose the already-real `/importer` route as the secondary Import action.
- **Unit visibility — autonomous recommendation:** print the active mg/dL or mmol/L unit directly below each converted glucose value.
- **Life-context accessibility — autonomous recommendation:** retain compact emoji while supplying localized semantic labels.
- **History query — autonomous recommendation:** use a Journal-specific query that returns every row for `Tout` and falls back to `createdAt` when legacy `loggedAt` is null; no migration or data rewrite.

## Runtime correction

Branch: `agent/journal-product-audit`

- Header subtitle follows the selected 7-day, 30-day or all-history filter.
- 7 / 30 / all-history selection is exposed as visible ChoiceChips below the header.
- `Tout` uses an unbounded Journal query; 7/30-day queries include legacy rows through `createdAt` fallback when `loggedAt` is null.
- Empty Journal offers Add reading first and Import second.
- mmol/L display converts stored mg/dL using `/ 18.0` and one decimal place, and rows now print the active unit.
- Meal context is reduced to one compact summary line while preserving primary context and detail-on-tap.
- Life-context emoji expose localized screen-reader semantics.
- A discreet chevron makes row detail/edit navigation discoverable without adding another CTA.
- Detail/edit exposes a secondary delete action with explicit irreversible-action confirmation; swipe delete remains available.
- Personal Response is a post-history secondary disclosure, collapsed by default.
- Journal row sync chrome is silent for `synced`/non-actionable states and visible only for `pending`/`error`.
- Red is reserved for `<70 mg/dL`; other out-of-target readings use the patient's target-range amber branch.
- Target ranges, treatment logic, schema and persisted history remain unchanged.
- Anti-regression contracts: `frontend/test/features/journal_truthfulness_contract_test.dart` and the canonical mobile-header contract.
- Full PR diff reviewed after the autonomous pass: changes remain scoped to Journal runtime/query/edit flow, contracts and this assessment.

## Certification gate

No final page score or CLOSED status before exact-head CI/relevant gates, real Chrome 390×844 inspection, post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
