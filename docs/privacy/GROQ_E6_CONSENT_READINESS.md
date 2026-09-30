# IAMINA — Groq E6 Consent Readiness

Status: **ENGINEERING READY / LEGAL WORDING BLOCKED**

Date: 2026-09-30

## Goal

Prepare the exact engineering path for E6 — processor/transfer-specific patient notice
and re-consent — without changing legal copy, approving Groq, enabling provider traffic,
or sending patient data.

## Verified current architecture

Backend:
- `backend/core/consent_notice.py` owns the canonical notice version and locale hashes.
- `profile_has_current_consent()` fails closed when version/hash/locale do not match.
- `backend/core/api/v1/account.py` reports consent as inactive when stored evidence is stale.
- `AIConsentReceipt` is append-only evidence for one exact accepted notice.
- granting a new consent epoch revokes active media grants rather than silently carrying them forward.

Frontend:
- `frontend/lib/services/consent_notice_contract.dart` mirrors the canonical version/hash contract.
- `ConsentEvidenceStore` accepts and reads only current exact notice evidence.
- `ConsentService` requires both the profile timestamp and verified current evidence.
- `ConsentScreen` opens the AI gate only after exact server acceptance and secure local persistence.
- current localized notice copy lives in `frontend/lib/l10n/app_fr.arb`,
  `app_en.arb`, and `app_ar.arb`; Darija currently shares the Arabic consent hash.

## New regression proof

`backend/core/tests/test_consent_notice_contract.py::test_stale_notice_version_forces_reconsent`
proves that a previously accepted consent becomes ineffective when its stored notice
version is no longer current:

- `profile_has_current_consent` returns false;
- consent status reports `ai_consent_given=false`;
- timestamp/version/hash/locale are not exposed as current consent.

This is preparatory evidence only. The canonical notice version has **not** changed.

## E6 implementation sequence after legal/product wording approval

1. Approve exact FR/EN/AR wording naming the enabled processor and international/U.S.
   transfer context.
2. Update the nine canonical rendered consent fields in the locale ARB files.
3. Increment `NOTICE_VERSION` and Flutter `ConsentNoticeContract.version`.
4. Recompute SHA-256 hashes using the existing `NOTICE_FIELD_ORDER` contract.
5. Update backend and frontend hash registries atomically.
6. Regenerate Flutter localization artifacts if required by the build.
7. Run backend consent contract tests and frontend consent contract/service tests.
8. Prove an old notice claim fails closed and the new exact claim succeeds.
9. Because the change is visual copy, run BEFORE/AFTER consent-screen captures at the
   same canonical mobile/desktop viewports and review wrapping/overflow/RTL.
10. Record the approved wording reference, version, locale hashes, reviewer and date in
    processor governance evidence.
11. Keep Groq `PENDING` until E1–E5 are independently approved as well.
12. Run the release-scoped governance audit with `--require-approved` only after all
    evidence rows are genuinely approved.

## Explicit non-actions

This readiness lot does not:
- draft or approve legal wording;
- identify the IAMINA legal controller;
- satisfy CNDP E1/E2;
- prove Groq DPA coverage or production ZDR;
- change the active notice version;
- invalidate current consent in production;
- change `groq` from `PENDING`;
- enable provider traffic;
- deploy Vercel.

## Human gate

Required before step 1: approved processor/transfer-specific wording tied to the exact
IAMINA controller, Groq contracting context, and approved transfer basis.
