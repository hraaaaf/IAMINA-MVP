# D22-B Web real-Chrome FUE — limited negative-path candidate

Date: 2026-11-01; PR #1214. This deliberately does **not** claim F01–F07 complete.

**Goal:** on a *real Flutter release Web build* accessed with disposable real Chromium and local synthetic account, verify that the profile's selected display unit persists mg/dL→mmol/L→mg/dL after saving and physical reload, and no unauthenticated personal target is editable. Preserve no-egress invariant and collect 390×844, 768×1024, 1280×900 full-page PNG evidence.

**Success criterion (bounded):** `scripts/d22_web_fail_closed_fue.py` writes `proof.json` with `PASS_PARTIAL` and 3 checksummed screenshots; pinned CI workflow `d22-web-fail-closed-chrome.yml` ends SUCCESS on exact HEAD. No patient information or production SSO connected.

**Coverage mapping:** F01 partial (display unit preference/reload, EN only); F03 partial (unverified-target message, no editable target on synthetic profile); F07 partial (real Chrome EN viewports). F02 patient-specific approved target, F04 persisted raw measurement edits, F05 reports/CGM/exports, F06 two accounts and remote privacy, F07 FR/AR/RTL/keyboard+zoom all **NOT_RUN**, as well as BEFORE screenshot reference and independent clinical approvals. A generic widget-test success cannot replace the FUE.

**Clinical gate:** `AppDatabase.schemaVersion==12`, legacy numerical defaults 70/180 still exist with unknown source unit; UI is fail-closed. Synthetic G7 migration rehearsal passing does not equal authorized migration. Do not enable clinical metrics or real DB migration from this workflow. No Vercel deployment; PR remains Draft.

**Next exact:** check exact HEAD CI and browser snapshots, fix any failure without bypassing accessible state. Then complete G1/G4/G7 clinical/privacy design, FR/AR+RTL/browser keyboard FUE and real backup/rollback proof before certification.

## 2026-11-01 — Exact-code-HEAD browser FUE evidence (bounded technical closeout)

**Goal:** verify on real local Flutter Web release + Chromium, without connected patients or remote APIs, that a saved display preference is preserved across real reloads and an unverified historical target is not an editable/clinically classified target. Reconcile the previously red shared D7 route without weakening its oracles.

**Code HEAD / PR:** `7cc4c8784c4bf994c734e4f1624ad682fcfcf7cb`, [Draft #1214](https://github.com/hraaaaf/IAMINA-MVP/pull/1214), branch `fix/d22-b-web-unit-authority-staged-20261101`. This branch contains D22-A #1213 (baseline `3e55ff069a4bc9601ea548390f78af48e8e003dd`): GitHub comparison proved **25 ahead, 0 behind, 30 files**; PR base is temporarily `main` for CI. Neither PR is merged.

### Success / independent evidence

- **17/17 commit workflow runs on 7cc4c87 returned `completed/success`**, including [CI #41359377609](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41359377609) Flutter analyze/tests/PWA build (backend jobs intentionally skipped by scope), [D22 real Chrome #41359377528](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41359377528) and [D7 real Web #41359377529](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41359377529). These are observed GitHub verdicts, **not** a clinical certification.
- D22 Chrome run artifact `13104173532`: `proof.json.result=PASS_PARTIAL`; 5 scenario entries (local enrollment/route; mmol/L saved and physically reloaded; mg/dL return saved and reloaded; non-editable unverified-target synthetic profile; three English viewport renders). **3 PNG** with expected dimensions `390×844`, `768×1024`, `1280×900` and individually verified SHA256. At 390×844 the fail-closed warning is **actually on screen above Save and mobile bottom navigation**; not merely present in offscreen ARIA.
- D7 shared Web run artifact `13103984900`: `proof.json.result=PASS`; **8 actual-app phases** (local WebAuthn; Type 2 + treatment; reload; Type 1; diagnosis unknown; explicitly no treatment; treatment reentry; three viewport/egress check). **9 PNG** (3 states × 3 viewports) checked for PNG dimensions and individual SHA256. D7 additionally re-executed the D22 smoke successfully; artifact `13103989918`, `PASS_PARTIAL`.
- Previously red D7 [#41358178945](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41358178945) showed the medical ExpansionTile reverting to `Collapsed` and a D22 banner timeout. Source-only test corrections [49d9103](https://github.com/hraaaaf/IAMINA-MVP/commit/49d9103200831a88ae7ee2c0c436d139d89a9439) + [7cc4c87](https://github.com/hraaaaf/IAMINA-MVP/commit/7cc4c8784c4bf994c734e4f1624ad682fcfcf7cb) now retry a **genuine opening, only if collapsed**, with bounded attempts and *three consecutive* visible/geometry observations. No suppression of failure or bypass of clinical banner.
- Visual comparison: AFTER 390/768/1280 inspected. A same-state BEFORE browser baseline and a visual change score **do not exist**; no UX visual certification is claimed. Current code tests are local synthetic Web flows, not hosted production testing.

### Explicit limits / gates remaining

- F01, F03 and F07 are **PARTIAL**. F02 approved clinician target, F04 source-preserving record edits, F05 report/CGM/export parity, F06 two actual accounts/remote privacy, and F07 French, Arabic RTL, keyboard navigation and zoom **NOT_RUN**. No approved individual target conversion or real patient classification is demonstrated.
- Clinical/security gates G1/G4 source/factor/rounding, G2/G3/G5 provenance/classification/legacy, G6 local-language review and G7 data migration/privacy/backup/rollback remain **UNSIGNED**. The SQL legacy defaults `70/180` without intrinsic target source unit are still unresolved; synthetic G7 migration rehearsals are not a safe real migration.
- No independent PR review submitted (GitHub review count 0 at verification). **D22-B stays `DRAFT / BLOCKED_CLINICAL_CONTRACT`**; no merge, database migration, clinical activation, or Vercel deploy. Product decision D22 is not closed.

**Technical sublot verdict:** `PASS_PARTIAL_EXACT_CODE_SHA` for the three limited Chrome coverage areas and returning-patient D7 shared smoke, backed by real artifact checks. **Clinical/release verdict:** `NO_GO` pending human signoff and full FUE.

**Next exact:** qualified G1–G7 signoffs/reviews, then approved model/target/DB changes and scoped F02/F04/F05/F06 plus FR/AR RTL/keyboard/200% zoom; capture independently comparable BEFORE and AFTER, run tests on resulting exact code HEAD, obtain independent review. Requalify the stacked PR against D22-A before any merge. Vercel requires separate explicit authorization.

**Documentation-only follow-up:** this Markdown closeout is appended *after* the above code-head validation and itself creates a new commit SHA; the green runs above prove code SHA 7cc4c87, not any subsequent docs commit. Verify docs-HEAD checks separately.
