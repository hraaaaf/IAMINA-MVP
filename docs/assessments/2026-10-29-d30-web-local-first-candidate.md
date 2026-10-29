# D30 — Web local-first, isolated validation (2026-10-29)

**Status: EXACT-HEAD CI + FR/AR 1180x860 browser screenshots GREEN; MERGE/POST-MERGE NOT performed.**
Not a Production or hosted patient certification. Live backend/Neon identity is not attested.

## Goal
The Web/PWA device may begin with a local vault and strong app lock, without
mandatory name, email, phone or remote account. Remote clinical AI access stays
opt-in/credential-gated. The patient must not lose a local glucose reading after
reload, logout, or re-enrollment.

## Exact evidence
- Repository: `hraaaaf/IAMINA-MVP`
- Baseline: `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`
- Candidate: `test/d30-local-reenrollment-lock-20261028@f620a159e69eb58c09efd5e6fa52bfa0dcf52138`
- GitHub Actions: [run 40795479155](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40795479155), job `123190910476`, **SUCCESS** on the candidate SHA.
- Flutter widget, app-lock, local vault A/B/A, remote clinical API default-deny,
  browser bootstrap and Cloud CanvasKit packaging checks: PASS.
- Chromium: local device enrollment, actual WebAuthn with a virtual test
  authenticator, minimal onboarding, direct dashboard without mandatory remote
  AI consent, exact `112` textbox value, local save, reload app-lock prompt,
  legitimate unlock, same 112 mg/dL reading visible again: PASS.
- Browser intercepted nonlocal requests: **zero non-font outbound attempts**
  during the clinical test; **86 blocked font fallback attempts**.
- Real installed Service Worker on loopback: offline navigation, local lock
  verifier and packaged CanvasKit available with networking disabled: PASS.
  Cache `iamina-app-shell-0.1.0+1-d30-offline-lock`, 14 items.

## Final visual regression evidence (2026-10-29)
- [GitHub Actions run 40799852678](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40799852678), **SUCCESS** on code SHA `222cf7e002d053b0815d4829fe42c3a013e8cae4`.
- Screenshot artifact `d30-flutter-web-boot`, ID `12864909639`, contains first-use FR and Arabic screenshots and clinical/offline shell.
- Browser **1180x860** comparison: BEFORE missing Arabic glyphs in first-use heading and primary CTA; AFTER both render complete readable Arabic, RTL orientation preserved, same viewport. French remains intact.
- Actual screenshot reviewed (not inferred from accessibility semantics): Arabic title `إعداد IAmina هنا`; button `إعداد هذا الجهاز` present and legible.
- Offline shell cache 20 assets, including all six self-hosted OFL fonts, packaged CanvasKit and local WebAuthn verifier; all outbound font requests blocked.
- Visual score **9/10** for these inspected first-use/dashboard screens. Other viewports and independent Arabic medical-copy review remain separate scope.
- [Visual font issue #1167](https://github.com/hraaaaf/IAMINA-MVP/issues/1167) is fixed within this isolated candidate; not merged to main yet.

## QA / limitations
- Data were **synthetic only**, with no remote patient account, Neon mutation,
  Production deployment, or remotely approved clinical sync.
- PWA offline **app shell** was tested; a complete write+reboot clinical session
  while disconnected was not independently exercised by that particular smoke.
- The headless offline/no-external-font screenshot has missing glyphs (tofu).
  Typography under blocked external fonts needs its own visual remediation and
  identical-viewport BEFORE/AFTER comparison before claiming a polished
  fully readable offline UI. **No visual 10/10 score is asserted.**
- Browser screenshots are retained in the CI artifact
  `d30-flutter-web-boot` (run 40795479155).
- Tests are from a single CI runner and self-review, not independent security
  certification, formal medical validation or Production readiness.

## Changes within candidate
App route guard for locally completed onboarding and optional remote AI
consent; offline CanvasKit release packaging and Service Worker app-lock asset;
safe Service Worker registration update; synthetic Flutter/Chromium/Node
regressions and GitHub-only workflow. No change to glucose alert thresholds.

## Remaining gates
1. Complete independent security/privacy review of isolated local-first diff.
2. **Human gate:** explicit approval before merge because a merge can trigger
   downstream deployments, including Production Vercel. No deployment GO given.
3. If merge approved, merge, verify exact main SHA and post-merge CI; update
   Notion Chantier A and canonical roadmap. D19 audit can proceed independently.

**Do not mark D30 closed until these gates have been satisfied.**
