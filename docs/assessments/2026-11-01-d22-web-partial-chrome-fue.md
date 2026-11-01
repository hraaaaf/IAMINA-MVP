# D22-B Web real-Chrome FUE — limited negative-path candidate

Date: 2026-11-01; PR #1214. This deliberately does **not** claim F01–F07 complete.

**Goal:** on a *real Flutter release Web build* accessed with disposable real Chromium and local synthetic account, verify that the profile's selected display unit persists mg/dL→mmol/L→mg/dL after saving and physical reload, and no unauthenticated personal target is editable. Preserve no-egress invariant and collect 390×844, 768×1024, 1280×900 full-page PNG evidence.

**Success criterion (bounded):** `scripts/d22_web_fail_closed_fue.py` writes `proof.json` with `PASS_PARTIAL` and 3 checksummed screenshots; pinned CI workflow `d22-web-fail-closed-chrome.yml` ends SUCCESS on exact HEAD. No patient information or production SSO connected.

**Coverage mapping:** F01 partial (display unit preference/reload, EN only); F03 partial (unverified-target message, no editable target on synthetic profile); F07 partial (real Chrome EN viewports). F02 patient-specific approved target, F04 persisted raw measurement edits, F05 reports/CGM/exports, F06 two accounts and remote privacy, F07 FR/AR/RTL/keyboard+zoom all **NOT_RUN**, as well as BEFORE screenshot reference and independent clinical approvals. A generic widget-test success cannot replace the FUE.

**Clinical gate:** `AppDatabase.schemaVersion==12`, legacy numerical defaults 70/180 still exist with unknown source unit; UI is fail-closed. Synthetic G7 migration rehearsal passing does not equal authorized migration. Do not enable clinical metrics or real DB migration from this workflow. No Vercel deployment; PR remains Draft.

**Next exact:** check exact HEAD CI and browser snapshots, fix any failure without bypassing accessible state. Then complete G1/G4/G7 clinical/privacy design, FR/AR+RTL/browser keyboard FUE and real backup/rollback proof before certification.
