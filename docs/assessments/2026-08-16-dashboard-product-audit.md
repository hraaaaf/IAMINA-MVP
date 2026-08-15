# Dashboard product audit — 2026-08-16

Status: runtime merged; post-merge main recertification pending.

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

Runtime PR: #252
Runtime merge SHA: `955173a3b3858311cc8b298b3e39b1f8c3e12a23`
Exact-head certified SHA: `5f60f540df76df7f8b538753bf0255d569ee7800`

- Dashboard now uses `watchRecentLogs(limit: 1)` for the card labelled `Dernière mesure`.
- The arbitrary 21-day lookup window is removed from this surface.
- No target range, clinical threshold, unit conversion, treatment logic, persisted-data schema or history is changed.
- Anti-regression contract: `frontend/test/features/dashboard_latest_reading_contract_test.dart`.

## Exact-head certification

- CI #2444: PASS.
- Django migration drift #2256: PASS.
- UI screenshot audit #74: PASS.
- Chrome certification #33: PASS.
- Chrome artifact: `9254612669`, digest `sha256:ccdaec4cb2f7c639ead2db3041f1164e5643ab38d8155aa2b235baf9d36b6496`.
- Manual inspection of `dashboard-390x844.png`: clean layout, no collision/overflow, clear hierarchy and visible factual latest-reading surface.

## Remaining closeout gate

No final score or CLOSED status before post-merge `main` recertification is green and canonical consistency is confirmed.

MENA roadmap numerator remains unchanged by this page audit.
