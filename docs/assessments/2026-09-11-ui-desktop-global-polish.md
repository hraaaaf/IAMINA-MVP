# UI-DESKTOP-GLOBAL-POLISH — Global desktop density and action polish

**Date:** 2026-09-11  
**Status:** READY_TO_MERGE

## Goal

Polish the entire IAMINA patient-facing application for desktop so every real patient route uses the available canvas intentionally, avoids under-filled wide layouts and unnecessarily full-width primary actions, while preserving mobile/tablet behavior and clinical/data/security boundaries.

## Success criteria

1. All 17 real patient-facing routes have retained browser evidence at 390x844, 768x1024 and 1280x900.
2. Desktop composition is intentional: bounded rails, useful two-column layouts where truthful, compact actions, bounded empty/error states.
3. Dashboard, Journal and Trend are not regressed.
4. Mobile/tablet information architecture and interaction order are preserved.
5. FR/EN/AR, RTL, accessibility, clinical boundaries, persistence, authentication, CGM and route behavior are unchanged.
6. Analyze/tests and real Chrome evidence are green on the exact implementation head.
7. Same-viewport BEFORE/AFTER review plus explicit user acceptance supports the strict visual target: all 17 real routes accepted at >= 9.5/10 before merge.

## Route scope — 17 real routes

Global browser routes:

- Dashboard;
- Companion;
- Reports / Summary;
- Profile;
- Journal;
- New Reading;
- Importer;
- Document Import / Pulper;
- Medications;
- Reminders.

Dedicated missing-route certification:

- Login;
- Reset password;
- Consent;
- Onboarding;
- Companion Chat;
- CGM;
- Edit Reading.

The four extra global captures — Trend, KPI, Insight and Next Action — are Dashboard regression surfaces, not extra patient routes.

## BEFORE evidence

### Global routes

- workflow: `UI browser screenshot certification`;
- run: `34629126600` / #392 — **SUCCESS**;
- exact head: `aa753f06a9b06a3ebe369169f17f0bf0f9c8083c`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10276350839`;
- digest: `sha256:8d0d47000db5e16e4afcceeebdcc1d57e2e9ab49088f41ce59a9bf607f369335`;
- 42 PNGs: 14 surfaces x 390/768/1280.

### Missing-route baseline

- workflow: `UI global missing routes certification`;
- run: `34634831910` / #1 — **SUCCESS**;
- exact head: `2e6be93a2a320c89460c3d007f56f0b58ef58d33`;
- artifact: `iamina-ui-global-missing-routes-cert`;
- artifact id: `10278080077`;
- digest: `sha256:a14654abe9b76ffb0a24c196281dee2946a1d6b72e2136f2e9aa687d6382e7ee`;
- 21 PNGs: 7 routes x 390/768/1280.

## Verified implementation

The polish was applied only to responsive/presentation behavior. Main changes include:

- bounded desktop content rails and shared header/body alignment;
- compact desktop CTA widths instead of stretched mobile actions;
- two-column desktop layouts for Importer, Medications, Reminders and appropriate forms;
- focal desktop states for Pulper, Companion and Companion Chat;
- improved Onboarding desktop composition;
- compact New Reading and Edit Reading actions;
- final premium desktop framing for Edit Reading;
- compact Consent action;
- shared first-use desktop action sizing;
- no fabricated statistics, patient data, recommendations or decorative filler.

Temporary one-shot patch/applicator machinery was removed. No Vercel deployment is part of this lot.

## AFTER evidence — exact implementation head

**Implementation head:** `88a0c54fd0eec8c0a14e657638167448cead4a63`

All required checks on this exact head are **SUCCESS**:

- CI `34655949381` / #4013 ✅
- UI browser screenshot certification `34655949515` / #435 ✅
- UI global missing routes certification `34655949471` / #38 ✅
- UI geometry golden audit `34655949761` / #432 ✅
- P7 responsive Dashboard certification `34655949419` / #89 ✅
- CGM onboarding browser certification `34655949398` / #46 ✅
- Companion real chat E2E screenshots `34655949375` / #87 ✅
- Offline demo UI certification `34655949820` / #35 ✅

### Global AFTER artifact

- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10285787143`;
- digest: `sha256:32870b50f8670769ec3b1b2e067cffdb1f2f5d8a1ff263bf0a063f29fb593e0f`;
- exact head: `88a0c54fd0eec8c0a14e657638167448cead4a63`.

### Missing-route AFTER artifact

- artifact: `iamina-ui-global-missing-routes-cert`;
- artifact id: `10285456459`;
- digest: `sha256:81114914c8391a7aeadcf8113deae863e57d007ba543bf2978c07cf2d5e9bf54`;
- exact head: `88a0c54fd0eec8c0a14e657638167448cead4a63`.

## Visual validation

Same-viewpoint BEFORE/AFTER review was performed at 390x844, 768x1024 and 1280x900 across all 17 real patient routes.

Observed result:

- desktop layouts no longer present the systemic stretched-mobile pattern that initiated the lot;
- primary desktop actions are compact or column-owned;
- mobile/tablet captures remain coherent;
- no route required fabricated content to fill space;
- Edit Reading received a final desktop-only framing pass before certification;
- all 17 AFTER routes were shown to the user from the exact implementation-head artifacts and explicitly validated by the user on 2026-09-12.

**Strict visual acceptance gate: PASS — 17/17 routes accepted at the >=9.5 target.**

## Roadmap and deployment boundary

This is a presentation/responsive UX lane. It does not change Pilot Readiness or MENA arithmetic and therefore does not require a roadmap percentage change. No Vercel deployment is authorized or included.

## Merge gate

All implementation gates are green, exact-head browser evidence is retained, the visual target is accepted, and PR #571 is mergeable.

Closeout documentation commits after the implementation head are docs-only. No product code changed after `88a0c54fd0eec8c0a14e657638167448cead4a63`.

The lot is READY_TO_MERGE.
