# IAMINA Web — W02/D11 — Vercel Preview test candidate (2026-10-19)

**Base:** W01 experimental PR head `8c072a3ebcb838fd575d3febd66f1179f3a5c724` (not merged); W01 remains NO-GO.
**Branch:** `test/w02-d11-vercel-preview-20261019`; **Preview only**; both existing Vercel projects must keep SSO and isolated Preview Neon.
**Goal:** no synthetic glucose values injected into patient-owned vault and no deletion of existing clinical readings.
**Code:** guard in Flutter seed service, guard in Drift `AppDatabase.seedDemoData()`, retire Django patient-owned POST /api/v1/demo/seed with authenticated 404.
**Tests:** `flutter test test/services/d11_vercel_preview_guards_test.dart`; `python manage.py test diabetes.tests.test_w02_d11_demo_seed_disabled`; existing auth/local-first regression.
**Deployment:** explicit user authorization for Vercel Preview only, manual Vercel API calls (git.deploymentEnabled false), no Production, no real patient accounts.
**Proof gate:** READY build is not clinical acceptance. Need browser Preview SSO proof, synthetic clinical authorization, A→B→A, data isolation, no demo contamination, and independent security review.
**No real user data:** no DB changes or manual patient account creation in this patch; only in-memory test fixtures.
**No merge / no promotion** until W01 GO and full D11 independent validation.
