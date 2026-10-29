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

## 2026-10-29 — Exact candidate recheck and real Chrome BEFORE/AFTER

The earlier notes about unreadable offline glyphs describe an older run, **not the corrected candidate**. The FR/AR 1180×860 readability correction is supported by screenshot artifact 12864909639 on code SHA 222cf7e0. This does not establish every locale or every offline clinical UI view.

- PR [#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169), candidate code HEAD before this documentation update: `bf1917c5f543d2ec896be99f571027453d823a2d`.
- GitHub Actions at that exact code SHA: 18/18 workflows SUCCESS, including [CI #40841416752](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40841416752), [PWA update/recovery #40841416694](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40841416694), [offline shell #40841416673](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40841416673), and [auth visual #40841416802](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40841416802).
- Auth visual artifact `iamina-auth-local-first-before-after` ID `12882997602`: Chromium BEFORE and AFTER PNGs at identical 390×844, 768×1024, 1280×900 viewports. The captured first-use local-enrolment screen has no horizontal overflow in either state. Both states are legible; the visible delta is modest and primarily typography. Screenshots were directly inspected, not inferred merely from a green status.
- Local-first, WebAuthn, synthetic 112 mg/dL retention and offline app-shell behavior have separate earlier browser evidence, including [#40795479155](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40795479155) and [#40799852678](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40799852678). Do not claim that the visual artifact itself proves these clinical workflow assertions.
- Repository `vercel.json` on main has `git.deploymentEnabled=false`. Vercel projects `iamina-review` and `iamina-certified` are both GitHub-linked. No deployment or release promotion was authorized or performed by this audit.
- **Release-scope gap:** `frontend/vercel_build.sh` still builds Vercel Production with `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` while the D30 isolated workflow exercises `false`. Thus merging the current candidate alone would **not** prove the public Production Web path allows local enrollment without a remote account. Existing remote-account flows must remain safe; resolve deliberately rather than silently flipping the production flag.
- **Independent-review gap:** GitHub returned no submitted reviews for #1169. An automated green CI and a single-agent static review do not constitute independent security/privacy review.
- Code branch is diverged from main (69 ahead / 5 behind at inspection); any merge result requires its own exact-SHA/post-merge evidence.

**Status remains OPEN / NO-GO for a certified D30 closure** until independent security/privacy review, the Web Production scope decision, authorized merge without Vercel deployment, and post-merge checks are recorded. This appendix is evidence documentation only and does not alter clinical behavior, credentials, storage, consent, or deployment configuration.

## 2026-10-29 — Owner-directed two-choice Web entry and optional app lock (candidate)

User decision: always offer two entry journeys when remote account service is
available: (1) set up a device-local vault without name/email/remote credential,
(2) sign in or create an authenticated remote account. A separate, explicit
first-use choice offers secure device lock or continue without app lock.
No-lock is not a bypass for an already-configured credential, recovery-required
vault, unidentified patient scope or known preexisting protected data.

- Scope: Web/PWA source and synthetic QA on PR #1169, not deployed or merged.
- Code implemented via commits c51158e2, 5c1c5ce3 and associated tests.
- No-lock acknowledgement is scoped to the active typed patient-vault namespace
  and revoked on sign-out / identity change; the remote account password is
  still required for login and does not become a local vault credential.
- Privacy warning explicitly states browser-profile exposure, possible loss of
  unsynced local records on browser clearing, and the existing limitation that
  clinical network sync requires an unlocked app-lock (do not bypass egress gates).
- Local and remote flows remain separated by remote bearer and owner binding.
- Earlier 18/18 GREEN on bf1917c5 does not apply to this feature change.
  The updated product/UI/CI HEAD needs exact-SHA tests and 390×844, 768×1024,
  1280×900 Chromium BEFORE/AFTER with remote accounts enabled.
- Historic TD-014 static test incorrectly barred even the word "skip" in UI;
  replaced with checks that only a fresh owner-scoped vault can choose no-lock,
  and existing protection/recovery can never be bypassed.
- Operational note: the opt-out is an *explicitly less secure* product mode.
  Independent privacy/security review, shared-browser A→B→A, storage deletion,
  offline clinical save/reopen, accessibility, and clinical sync limitations
  remain must-prove. Do not certify without new evidence.

No merge to main and no Vercel deploy is authorized by this commit. D30 OPEN.

## 2026-10-29 — D30 user-choice refinement and profile security toggle

**Owner instruction:** Both authentication and device-local app lock must be explicit choices, including users who have a remote account. These decisions are distinct: account password remains required for account login; skipping app-lock does not imply a fictitious remote account, remote clinical consent, or an unlocked clinical sync transport.

### Shipped only to draft branch, not production

- Web /login first-use presents **Continue without account** and, where remote enrollment is available, **Sign in or create an account**. Vercel production still compiles remote account enrollment available while local enrollment is also presented.
- After enrollment, offer **Enable app lock** or **Continue without app lock** with FR/EN/AR risk disclosure and affirmative confirmation.
- Inside **Profile → Account & privacy**, offer a reversible action to enable/disable app lock. Disabling an existing WebAuthn-protected vault requires a **fresh hardware/platform credential verification** even if the current session was previously unlocked. Cancelling verification preserves the existing protection.
- Opt-out is keyed to the selected typed patient-vault owner. Do **not** delete a globally shared WebAuthn credential when disabling a single owner's app lock. Switching or signing out revokes an active opt-out synchronously; A's decision cannot unlock B's vault.
- A user who disables app-lock is warned about browser-shared local health-data access and **clinical sync remaining paused** by existing transport policy. A remote-account password is not disabled.
- Protected/ambiguous/recovery vaults cannot use an unverified first-use opt-out; the legacy untrusted opt-out flag remains rejected.

### Exact evidence and status

- Behavioral code SHA `e1fc7a304c633d33ad53eb2023ab4afbc2007eb0`; integration/widget/fixture SHA `50b27805877655de931867589bd3adb46f7295be` **before this documentation update**.
- Tests added/updated: local/account CTA distinction; initial skip confirmation; persistent per-owner selection; fresh verification rejection on cancel; enable again; A→B auth change; explicit previous-lock protection; hosted login is optional (remote API bearer is not).
- [UI geometry run #40849761165](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40849761165) **SUCCESS** on SHA `50b27805`, after adding a synthetic `AppLockService` provider to the profile geometry fixture.
- At last observed state on `50b27805`: [CI #40849761037](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40849761037) QUEUED, [TD-014 #40849761057](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40849761057) IN_PROGRESS, [browser screenshots #40849761148](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40849761148) QUEUED. The full HEAD was **not certified**.
- Prior real auth BEFORE/AFTER Chrome artefact `12885171884` compared 390×844, 768×1024, 1280×900 with remote accounts compiled ON and no horizontal overflow. Those screenshots predate the new Profile settings toggle: **do not present them as visual proof of that later profile change**.
- Current profile screenshots are generated by `ui-browser-screenshot.yml` and geometry captures by `ui-screenshot-audit.yml`; actual expanded-settings visual inspection and identical-viewport before/after remain an open QA item.

### Limits and remaining gates

- On a **shared browser with multiple patient accounts**, legacy global WebAuthn credentials still impose a lock until a safe account-specific transition is established. The owner-scoped opt-out prevents A from unlocking B, but does **not** certify independent lock setup or opt-out for every second profile with an old global credential. No bypass may be introduced simply to satisfy a button.
- Remote clinical sync is deliberately not loosened when a patient declines app-lock. Its existing `isUnlocked` egress guard stays enforced; changing it requires independent security/privacy review.
- Complete exact-HEAD CI, browser/profile BEFORE/AFTER, independent security/privacy review, scoped shared-device assessment, and controlled merge + post-merge verification. No Vercel deployment authorized; no Neon/patient mutation.

**Status: D30 OPEN, DRAFT PR #1169, not merged, not a production claim.**
