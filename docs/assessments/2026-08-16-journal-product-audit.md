# Journal product audit — 2026-08-16

Status: **CLOSED — 9.5/10 PASS**.

## Product contract

Journal is a factual history of recorded glucose measurements and their captured context. Filters and displayed units must match what the user actually selected. Historical insulin context remains backward-compatible; this page does not become a prescribing surface.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Header + active period | Immediate orientation: tells the user exactly what history scope is shown | 8.0/10 baseline → 9.0/10 | IMPROVED — subtitle follows 7 / 30 / all-history filter |
| 7 / 30 / all filter | Essential temporal navigation; direct visibility reduces discovery cost versus a hidden menu | 9.0/10 baseline → 9.5/10 | Decision B — three visible ChoiceChips below the header |
| History query truthfulness | Determines whether the visible period actually contains every eligible stored row | 6.5/10 baseline → 9.7/10 | IMPROVED — no arbitrary lower floor; legacy `loggedAt == null` rows use `createdAt` fallback without data rewrite |
| Empty state | First-use orientation and fastest route to making Journal useful | 8.5/10 baseline → 9.5/10 | Decision B — Add reading primary + Import secondary |
| Loading skeleton | Preserves layout stability while local Drift stream resolves | 9.0/10 | KEEP |
| Personal Response | Adds longitudinal interpretation, but competes with Summary if visually dominant | 6.5/10 baseline → 8.5/10 | Decision B — secondary, collapsed by default, after history |
| Grouping by day | Natural chronological scan of measurements | 9.5/10 | KEEP |
| Glucose value capsule | Core factual content of Journal; numerical value without its unit is incomplete | 9.0/10 baseline → 9.7/10 | IMPROVED — mmol/L conversion correct and active unit printed |
| Meal / glycemic / Ramadan context | Explains recorded circumstances without overloading rows | 9.0/10 baseline → 9.5/10 | Decision B — compact summary, full details on tap |
| Life-context indicators | Fast scan for illness, stress, fatigue, activity and sleep context | 8.0/10 baseline → 9.2/10 | IMPROVED — localized screen-reader semantics |
| Historical insulin badge | Preserves backward-compatible factual history without turning Journal into medication entry | 8.5/10 | Decision A — visible and read-only on legacy rows |
| Synchronization status | Useful only when action or attention is required | 7.0/10 baseline → 9.0/10 | Decision B — routine synced state hidden; pending/error only |
| Tap → edit | Essential correction/detail path for persisted factual data | 9.5/10 baseline → 9.8/10 | Decision B — whole-row tap + discreet chevron |
| Delete access | Destructive action must be discoverable but guarded | 9.0/10 baseline → 9.5/10 | Decision B — swipe + detail delete, both confirmed |
| Glucose color hierarchy | Distinguishes clinically important low glucose from ordinary out-of-target values without overclaiming urgency | 7.0/10 baseline → 9.0/10 | Decision B — red below 70 mg/dL; other out-of-target values amber |

## Verified findings and resolved decisions

- Default 30-day filter now matches the visible `30 derniers jours` subtitle.
- `Tout historique` is unbounded.
- Legacy rows with nullable `loggedAt` remain visible through `createdAt` fallback, with no migration or persisted-data rewrite.
- Stored mg/dL is converted for mmol/L display and each row prints its active unit.
- Personal Response is secondary and collapsed after factual history.
- Routine synchronization chrome is removed from synced rows.
- Primary temporal navigation is visible instead of hidden behind a tune icon.
- Meal/context density is compact while full detail remains reachable by row tap.
- Life-context indicators expose localized accessibility semantics.
- Detail/edit navigation has a visible chevron affordance.
- Delete remains explicitly confirmed.
- Historical `insulinUnits` remains display-only compatibility data.
- Red is reserved for `<70 mg/dL`; high values outside the patient target use amber. No target range or treatment logic was changed.

## Runtime evidence

Runtime PR: **#253** `Journal: sharpen factual history hierarchy`

Exact pre-merge head: `fcd406ec7f0283955658ec7c453fb30bcb0dda7f`

Pre-merge gates:
- CI #2503 — PASS
- Django migration drift #2315 — PASS
- UI screenshot audit #122 — PASS
- real Chrome #82 — PASS after retry of an infrastructure-only Chrome startup failure

Runtime merge SHA: `38f2051dc55b524b3efe65b9bb2e2b48edd3e8eb`

Post-merge gates on the exact merge SHA:
- CI #2506 / run `31922365644` — PASS
- Django migration drift #2318 / run `31922365620` — PASS
- UI screenshot audit #125 / run `31922365550` — PASS
- real Chrome #85 / run `31922365588` — PASS

Real Chrome artifact:
- artifact ID `9256799202`
- digest `sha256:344389b1038dc847fb94feaff30d4b456f88513dc5397d7770c753cb1df87602`
- `journal-390x844.png` manually inspected after post-merge certification: clean header/range truthfulness, visible filters, explicit glucose units, readable chronological cards and no blocking visual defect in the certified viewport.

## Anti-regression

- `frontend/test/features/journal_truthfulness_contract_test.dart`
- `frontend/test/ux_7_first_use_empty_state_contract_test.dart`
- canonical mobile-header contract updated for dynamic range labels

## Final assessment

**9.5/10 PASS.** The primary Journal job is truthful, legible and reversible where destructive actions exist. Remaining lower-scored secondary surfaces do not create a blocking clinical, data-integrity, accessibility or main-flow defect. This score is conditional only on the docs closeout merge and post-doc CI/drift remaining green.

No MENA roadmap numerator change is caused by this page audit.
