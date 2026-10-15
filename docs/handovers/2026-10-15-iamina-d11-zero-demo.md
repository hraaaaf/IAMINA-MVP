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
- Django regression tests: new identity receives zero fake log and no synthetic medical defaults; existing measurements for A and B survive retries untouched; named fixture account `patient1` denied; anonymous 401; public scenarios retained.
- Flutter regression tests: authorization matrix, patient-vault zero log/profile test, direct bypass denial, audit-only positive fixture.
- **No UI/UX code change**; no BEFORE/AFTER pixel comparison needed for this backend/data-access-only lot.

## Remaining hazards and human gates

- `setup_demo` management command has development-oriented hard-coded sample credentials and must never run against a clinical production database. Its deployment policy needs a separate security review.
- This candidate prevents **new** fixture injection, but cannot prove that historical data already present in an old database were not synthetic. No automatic purge, migration, user reconciliation or deletion was authorized: destructive cleanup is an explicit human/security/legal gate.
- Audit mode only accepts compile-time-enabled loopback visual previews. A native account opened in audit mode resolves the audit namespace rather than a clinical vault.
- D30 identity, sync consent, PWA egress, D31 physical A/B and data recovery remain distinct certification gates. Do not infer patient isolation merely from this PR's code.
- **No merge / no clinical pilot / no Vercel** without exact-head CI + independent privacy/security approval and required real-device evidence.

## Execution evidence register

- PR #1021 HEAD code `09db7d97599ef36041fe3ea0c3385c2bb8ea7ffe` at first CI dispatch; base main at PR creation `0b33abbbbfb9093314cf45e6fe2f98c9f32ba9d5`.
- Six GitHub workflow runs started automatically; exact verdict **PENDING** at document authoring. No prior run is transferable to this HEAD.
- **Next exact:** check exact-HEAD CI, diagnose and repair any red job, then update this canonical document with final SHA and evidence. Human gates remain explicit.
