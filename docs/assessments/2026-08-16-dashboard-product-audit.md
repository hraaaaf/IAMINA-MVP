# Dashboard product audit — 2026-08-16

Status: CLOSED — 9.6/10 PASS.

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
| Trust card | KEEP | factual provenance copy retained |

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
- Manual inspection of `dashboard-390x844.png`: clean layout, no collision/overflow, clear hierarchy and factual latest-reading surface.

## Post-merge certification

Main SHA: `955173a3b3858311cc8b298b3e39b1f8c3e12a23`

- CI #2445: PASS.
- Django migration drift #2257: PASS.
- UI screenshot audit #75: PASS.
- Chrome certification #34: PASS.
- Post-merge Chrome artifact: `9254949309`, digest `sha256:d521b325085dfb9aa422d48f89aeddcb13af97395273266bbd35d3c0c435fd38`.

## Final score

**9.6/10 — PASS.** The identified truthfulness defect is fixed, the runtime diff is minimal, exact-head and post-merge gates are green, and the real 390×844 surface is clean. No clinical or persisted-data semantics changed.

MENA roadmap numerator remains unchanged by this page audit.
