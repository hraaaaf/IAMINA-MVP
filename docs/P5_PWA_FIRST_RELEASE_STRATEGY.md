# P5 — PWA-first release strategy

> **Status:** CANONICAL PRODUCT DIRECTION
> **Effective:** 2026-09-11
> **Baseline:** `main@2a6408cc953ec46b0e7632e4fb113432198bddef`
> **Pilot Readiness arithmetic:** unchanged at 3/9 = 33.3%
> **MENA arithmetic:** unchanged at 32/38 = 84.2%
> **Deployment:** this strategy does not authorize a Vercel deployment.

## Goal

Use the PWA as the immediate pilot delivery surface. Align native Android and iOS later, after the PWA pilot path is stable and the real-patient release gates are satisfied.

## Product decision

The current critical path is **PWA-first**.

- PWA packaging, installability, offline/update behavior and release traceability are the immediate pilot-delivery concerns.
- Android APK/AAB signing, permanent JKS identity, Apple Developer provisioning, TestFlight/App Store distribution and native real-device upgrade evidence are **deferred native alignment work**.
- Deferred native work remains mandatory before claiming native Android/iOS release readiness, but it must not block the PWA pilot solely because native signing is incomplete.
- P5-6 real-patient legal/CNDP/processor/residency/clinical-human gates remain mandatory regardless of delivery surface.

## P5-4 split

### P5-4A — PWA pilot packaging — CURRENT CRITICAL PATH

Success requires evidence that the PWA candidate:

1. is buildable reproducibly from one exact Git SHA;
2. has a stable production identity/version;
3. can be installed as a PWA on supported mobile browsers without repository or developer access;
4. preserves local/offline data across normal PWA updates within the supported compatibility window;
5. has deterministic recovery/forward-fix guidance if an update fails;
6. exposes no development secrets or repository access to pilot users;
7. has retained exact-SHA build/install/update evidence on the target PWA environments.

This lane may close independently of native signing.

### P5-4B — Native Android/iOS alignment — DEFERRED / NON-BLOCKING FOR PWA PILOT

Retained future gates include:

- founder-controlled permanent Android signing identity;
- signed Android artifact and retained hash/signature evidence;
- Apple Developer registration/signing/provisioning;
- signed iOS/TestFlight-equivalent artifact;
- real-device clean install and N-1 -> N update evidence on Android/iOS;
- native recovery/rollback evidence;
- release instructions without repository/developer tooling.

These gates become critical before any native Android/iOS pilot or public native distribution claim.

## P5-6 interaction

PWA-first does **not** bypass P5-6.

Before real patient data is enabled on the PWA candidate, the exact release must still satisfy:

- #318 qualified clinical-human review;
- #320 CNDP/processor/residency/foreign-transfer requirements;
- all three `--require-approved` fail-closed audits;
- explicit human release authorization.

Until then the release posture remains `NOT_RELEASE_AUTHORIZED`.

## Non-claims

This strategy does not claim that the current PWA is already pilot-ready, does not close P5-4A, does not close P5-6, does not waive Android/iOS future gates, and does not authorize Vercel or real-patient deployment.

## Next exact action

Audit the current PWA against the P5-4A success criteria, retain exact-SHA evidence, and fix only observed gaps. Native signing work remains deferred until the native lane is intentionally activated.
