# Dashboard product audit — 2026-08-16

Status: runtime correction in progress; exact-head certification pending.

## Product contract

Dashboard is the factual entry surface for the user's latest recorded glucose value and primary navigation. It must not imply that no reading exists merely because the most recent reading falls outside an arbitrary analytics window.

## Verified finding

The card labelled `Dernière mesure` previously consumed `watchLogsInRange(now - 21 days, now)`. A reading older than 21 days therefore produced `Aucune mesure`, despite a real historical reading existing.

## Verdicts

| Surface | Verdict | Reason |
|---|---|---|
| Latest reading card | IMPROVE | label must correspond to the actual latest recorded reading |
| Add measurement CTA | KEEP | clear factual primary action |
| Companion / Importer / Journal shortcuts | KEEP | useful primary navigation |
| Reminder action | KEEP | direct navigation |
| Target-range status | KEEP | existing profile-governed thresholds unchanged in this audit |
| Trust card | KEEP / monitor | no runtime change in this lot |

## Runtime correction

Branch: `agent/dashboard-product-audit`

- Dashboard now uses `watchRecentLogs(limit: 1)` for the card labelled `Dernière mesure`.
- The arbitrary 21-day lookup window is removed from this surface.
- No target range, clinical threshold, unit conversion, treatment logic, persisted-data schema or history is changed.
- Anti-regression contract added in `frontend/test/features/dashboard_latest_reading_contract_test.dart`.

## Certification gate

No final page score or CLOSED status before exact-head CI/relevant gates, real Chrome 390×844 inspection, merge with expected head, post-merge main recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
