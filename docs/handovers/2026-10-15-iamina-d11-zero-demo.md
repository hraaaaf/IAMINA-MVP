# IAMINA V1 — D11: real patient accounts never receive synthetic demo readings

**Date:** 2026-10-15  
**Status:** DRAFT, candidate code NOT MERGED. Security/privacy and real-device gates OPEN.  
**GitHub:** [PR #1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021), branch `fix/v1-d11-real-account-zero-demo-20261015`.  
**Canonical 29-decision order:** #5 → #6 → #7 → #9 → #10 → **#11** → #18 → #19 → ... → #1 → #25. D10-B remains gated on independent security/privacy; D11 is a separable anti-contamination fix.  
**P5 historical:** 6/12 = 50%, unchanged.

## Goal / observable success / evidence

- **Goal:** fresh *real* patient accounts have no fabricated glucose logs, meals or medical profile; existing real patient data cannot be overwritten/augmented by demo generation; test demo remains usable only in a separately labelled synthetic space.
- **Success:** authenticated A/B POST /api/v1/demo/seed returns HTTP 403 with no clinical mutation; anonymous returns 401; device and native patient Drift vaults reject demo seeding even with audit flags; the explicitly audit-only vault still seeds synthetic fixtures; public GET demo scenarios still returns eight fixtures.
- **Evidence:** CI/P5-5 and backend/Flutter synthetic tests must be green on PR exact HEAD. Real PWA/browser and physical A→logout→B→A proof remains separate **NOT RUN**.

## BEFORE — audited source on main (2026-10-15)

1. `backend/diabetes/api/v1/demo.py:seed_demo_data` previously accepted a patient bearer and wrote around 30 days of fabricated `LogEntry` records **under `request.user`**, plus an invented diabetes medical profile if absent. It was described as dev-only **without** enforced development/synthetic-only authorization.
2. `frontend/lib/services/offline_demo_audit_seed.dart` checked two visual-audit booleans but did **not** inspect `AppDatabase.patientVaultScope`. A later caller could thus accidentally write demo readings into a real patient vault while audit flags were enabled.
3. `AppDatabase.seedDemoData()` begins by **deleting all existing local log entries**, then inserts fabricated measurements; the method lacked a patient-vault boundary check.
4. `PatientVaultAppHost` and `PatientVaultSessionController` currently use distinct physical Drift DB names for native, device-local and audit sessions. Old generic `amina` data are quarantined in app startup and are not served to patient providers. That pre-existing design does not by itself certify this new D11 seed behavior.

## AFTER — PR #1021 candidate

- Authenticated `POST /api/v1/demo/seed` now returns **403** without any clinical writes. Demo data may still be created via an explicit **local management command** `setup_demo`; demo scenarios and synthetic `/demo/chat` remain separate; account authentication does not confer right to seed.
- Audit seed helper requires two flags **and** `patientVaultScope.databaseName == PatientVaultScope.auditOnly().databaseName`. Unscoped legacy DB, device-local vault and native Django account vault are refused.
- Direct `AppDatabase.seedDemoData()` rejects any **patient-scoped** non-audit vault before beginning a transaction or deleting entries. Pre-existing unscoped test fixtures remain compatible, but cannot be injected as patient providers.
- Django regression tests: native **registration over HTTP** yields an empty clinical journal and baseline identity profile; new identity receives zero fake logs and no synthetic medical defaults; existing measurements for A and B survive retries untouched; named fixture account `patient1` denied; anonymous 401; public scenarios retained.
- Flutter regression tests: authorization matrix, patient-vault zero log/profile test, direct bypass denial, preservation of an existing clinical reading, audit-only positive fixture.
- **No UI/UX code change**; no BEFORE/AFTER pixel comparison needed for this backend/data-access-only lot.

## Remaining hazards and human gates

- The `setup_demo` management command has development-oriented hard-coded sample credentials. D11 now refuses it **unless `settings.DEBUG=True` AND an administrator explicitly passes `--confirm-synthetic-only`**; refusal happens before any User/LogEntry write. Regression tests cover refusal with DEBUG=False, refusal without flag, and explicit fixture operation in local DEBUG. This is not permission to use clinical real-patient data with DEBUG or fixture command. Deployment/runbook confinement and a security review remain required.
- This candidate prevents **new** fixture injection, but cannot prove that historical data already present in an old database were not synthetic. No automatic purge, migration, user reconciliation or deletion was authorized: destructive cleanup is an explicit human/security/legal gate.
- Audit mode only accepts compile-time-enabled loopback visual previews. A native account opened in audit mode resolves the audit namespace rather than a clinical vault.
- D30 identity, sync consent, PWA egress, D31 physical A/B and data recovery remain distinct certification gates. Do not infer patient isolation merely from this PR's code.
- **No merge / no clinical pilot / no Vercel** without exact-head CI + independent privacy/security approval and required real-device evidence.

## Verified exact-code-HEAD CI and PWA evidence — 2026-10-15

**Reviewed code/test HEAD before this documentation-only closeout commit:** `550a76eb7ff99242dea000018ea6ca5a89a1dfde` on [PR #1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021), **DRAFT, NOT MERGED**.

- [Main CI #38697582946](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582946): **COMPLETED/SUCCESS**, including Ruff, OpenAPI schema check, Django/Pytest (**2,822 passed; 5 skipped; 3 xfailed; 121 subtests**), PostgreSQL (**2,826 passed; 1 skipped; 3 xfailed; 121 subtests**), Flutter analyze/tests (**787 passed; 1 skipped**, explicitly including four D11 vault tests), and self-contained PWA release build.
- [Django migration drift #38697582950](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582950): **SUCCESS**.
- [P5-5 synthetic pilot #38697582952](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582952): **SUCCESS**.
- [PWA offline shell #38697582948](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582948): **SUCCESS**.
- [PWA update/recovery #38697582945](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582945): **SUCCESS**.
- [PWA Chrome persistent storage #38697582982](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582982): initial attempt **FAILURE** because Chrome's DevTools port 9223 never opened; synthetic persistence tests did not execute then (not evidence of a storage fault). **Single-job rerun, attempt 2: COMPLETED/SUCCESS**, same exact SHA, with [browser proof artifact #11960588503](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38697582982/artifacts/11960588503). The proof artifact is present; its contents have **not** been independently re-parsed here.
- Thus **6/6 exact-code-SHA workflows green after Chrome re-run**. All tests used synthetic patients / runtime; no new clinical real-patient certification is claimed.
- Recent unrelated `main` commits advanced beyond the PR base. Recheck PR mergeability and rebase if required **only after independent review**; do not conflate this green code SHA with future integration or deployment.
- The **documentation-only update that adds this section produces a NEW HEAD**. Run its new exact-HEAD CI independently before declaring a final documentation/git closeout. Historical `550a76eb` green must not be silently transferred to a newer SHA.

**Status:** D11 code and synthetic CI proof green on `550a76eb`; **D11 real-patient certification / merge OPEN** pending independent security/privacy, existing-data audit and physical A→logout→B→A. No Vercel/real-patient release or destructive cleaning.

## Execution evidence register

- PR #1021: base main at PR creation `0b33abbbbfb9093314cf45e6fe2f98c9f32ba9d5`; code/test HEAD before this documentation update `0702b947902963769536fec0a38e37225477d40a`. Final documentation commit requires fresh exact-head CI; no previous green transfers.
- CI `#38695946163` on previous SHA `a37d9e5` found stale OpenAPI description; schema updated to match `/demo/seed` fail-closed description in commit `b530a2a`. Intermediate runs on newer commits were cancelled by subsequent pushes and do NOT count green. Exact verdict for final HEAD **PENDING** until observed. Previous P5-5 and PWA successes on older SHAs do not certify final code.
- **Next exact:** check exact-HEAD CI, diagnose and repair any red job. If full green, verify PR scope/diff and update GitHub/Notion closeout with final SHA and evidence. Independent privacy/security + physical multi-patient gate still blocks release/merge.

## D11 test-lab white-screen regression / verified recovery (2026-10-15)

**Goal:** prevent transient blank screens from mixed versions of PWA app-shell files without purging patient IndexedDB.

**BEFORE:** user reported white screen on Vercel test frontend. In source, `frontend/web/flutter_bootstrap.js` invoked `_flutter.loader.load()` before asynchronous hosted-review SW unregistration/app-shell cache cleanup. This ordering can permit an old controlling SW to serve stale Flutter assets after new deployment. A desktop Opera browser screenshot of the old build at `https://iamina-review.vercel.app/#/login` nevertheless showed the French login screen; user's affected device/cache state was not reproduced. This is a verified code race, not a proven single root cause on user's device.

**AFTER — code SHA `60de80ec070157f912cb62c80a7ded1e9bde75a6`:**
- Hosted Vercel build awaits cleanup of only `iamina-app-shell-*` caches + SW registrations before Flutter boot. A still-controlled document is reloaded **at most once** per tab via sessionStorage; second attempt proceeds to render. No IndexedDB delete, no storage clear, no unrelated cache deletion.
- New `frontend/test/services/d11_web_review_bootstrap_contract_test.dart` enforces ordering/bounded reload. Separate JS execution with synthetic browser mocks was performed for (1) clean, (2) controlled first load and (3) controlled repeat — all produced the expected sequence with no unrelated cache deletion.
- **Exact SHA CI:** [CI #38718391963](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718391963), [migration #38718391842](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718391842), [P5-5 #38718391837](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718391837), [PWA browser persistence #38718391813](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718391813), [PWA offline #38718391925](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718391925), [PWA update/recovery #38718392095](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38718392095): **6/6 COMPLETED SUCCESS**.
- **Vercel preview:** `dpl_66U7ffeqnM7tdmDxDqaqMycvxvTF` READY on this SHA, desktop screenshot opened login screen with logo, e-mail/password, demo CTA.
- **Vercel production-of-TEST:** `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K` READY on same SHA, alias `https://iamina-review.vercel.app` verified by new browser load and screenshot showing the same login layout. Backend test alias remains `https://iamina-certified.vercel.app`, previously READY and health/db OK.
- **UI review:** no intended layout/styling changes; desktop BEFORE/AFTER screenshots visually equivalent at full-screen browser dimensions. No quantitative pixel-diff score or affected-user device replay, so no `10/10` claim.
- **Human/device gate OPEN:** user should check previously white-screen browser without wiping private site data; interactive account onboarding A→B→A and real persistence remain unverified on their device. No old patient data purged.
- **Git state:** D11 PR #1021 is DRAFT/unmerged; this markdown closeout introduces a documentation-only SHA, so its exact-HEAD CI must be checked separately. Vercel test production already serves the green code SHA above; no new deployment required for prose-only changes.
- **Next:** exact docs-HEAD CI, then user/device white-screen reproduction outcome, closeout security gates; D18 independent work may proceed.

