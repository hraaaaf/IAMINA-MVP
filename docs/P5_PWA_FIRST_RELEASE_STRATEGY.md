# P5 — PWA-first release strategy

> **Status:** CANONICAL PRODUCT DIRECTION — P5-4A ENGINEERING CLOSED_WITH_BOUNDARIES
> **Effective:** 2026-09-11
> **Certified PWA baseline:** `main@35ab9c5cd70fa1f7e7f41978c8e1e5e1e1388387`
> **Pilot Readiness arithmetic:** unchanged at 3/9 = 33.3%
> **MENA arithmetic:** unchanged at 32/38 = 84.2%
> **Deployment:** this strategy does not authorize a Vercel deployment.

## Goal

Use the PWA as the immediate pilot delivery surface. Align native Android and iOS later, after the PWA pilot engineering path is stable and the real-patient release gates are satisfied.

## Product decision

The delivery strategy remains **PWA-first**.

- PWA packaging, installability, offline/update behavior and release traceability have completed the P5-4A engineering lane with retained exact-SHA browser evidence.
- Android APK/AAB signing, permanent JKS identity, Apple Developer provisioning, TestFlight/App Store distribution and native real-device upgrade evidence remain **deferred native alignment work**.
- Deferred native work remains mandatory before claiming native Android/iOS release readiness, but it must not block the PWA pilot solely because native signing is incomplete.
- P5-6 real-patient legal/CNDP/processor/residency/clinical-human gates remain mandatory regardless of delivery surface.
- A controlled pilot URL and physical target-browser/device installation remain external/human evidence, not implied by engineering closure.

## P5-4 split

### P5-4A — PWA pilot packaging — ENGINEERING CLOSED_WITH_BOUNDARIES

Retained engineering evidence now proves that the PWA candidate:

1. is buildable reproducibly from an exact Git SHA;
2. has a stable production identity/version;
3. has browser installability evidence without repository or developer access;
4. preserves persistent `sharedIndexedDb` Drift data across navigation, offline reopen and supported updates;
5. has a strict offline app-shell proof with normal HTTP cache disabled;
6. discovers canonical releases deterministically through a network-only service-worker probe and release-versioned registration URL;
7. precaches each release with HTTP-cache bypass so new release caches cannot inherit stale old-release bytes;
8. preserves the last-known-good shell when a deliberately broken candidate is rejected;
9. promotes a later healthy candidate only across the safe waiting/close/reopen lifecycle without clearing origin storage;
10. has a merged pilot operating runbook requiring no Git/repository/developer tooling.

Canonical closeout: `docs/assessments/2026-09-11-p5-4a-pwa-pilot-packaging-closeout.md`.
Canonical runbook: `docs/P5_PWA_PILOT_RUNBOOK.md`.

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

P5-4A engineering closure does not claim that a production/pilot URL exists, does not prove physical target-device installation, does not close P5-4B, does not close P5-6, does not waive Android/iOS future gates, and does not authorize Vercel or real-patient deployment.

## Next exact action

Advance the remaining pilot human/external evidence gates that actually block release. P5-6 is the primary release blocker; P5-1/P5-3 evidence remains applicable where the selected pilot scope requires those lanes. Native signing work stays deferred until the native lane is intentionally activated.
