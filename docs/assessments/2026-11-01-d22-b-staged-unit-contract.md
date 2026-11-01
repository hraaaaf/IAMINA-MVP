# IAMINA D22-B — staging G1/G4: candidate typed unit contract (non-clinical)

Date: 2026-11-01. Parent: PR #1213, exact SHA 3e55ff069a4bc9601ea548390f78af48e8e003dd.

**Decision:** stage a fail-closed model for glucose quantities independently of PatientProfiles and presentation; do **not** activate the candidate in an existing patient workflow before clinical/security contracts are signed.

**Goal:** reject unsupported source units, keep raw input lexical representation (and owner), derive conversions without rounding or writing back, refuse ambiguous historical rows and prevent cross-owner review. **Success criterion:** synthetic tests run in CI on exact HEAD; no runtime import from onboarding/profile/dashboard, no DB migration, no new clinical claim. **Proof:** tests and diff, CI run to attach; PRE-EXECUTION status NOT_RUN.

### Candidate contract, not approved for clinical use

- Source unit parser accepts only `mg/dL` or `mmol/L`. No implicit `mg/dL` fallback, including for empty, `unknown`, casing, aliases or whitespace. A reviewed import adapter may map verified aliases separately later.
- `D22CapturedGlucoseCandidate.rawInput` is immutable text, allowing a future approved schema to preserve lexical precision. `sourceUnit` and `ownerId` accompany it; derived `double` is ephemeral and nullable on invalid input.
- Candidate conversion factor `18.01559 mg/dL per mmol/L` is **mathematical only**, based on NIST molecular weight 180.1559 g/mol (https://webbook.nist.gov/cgi/cbook.cgi?ID=50997). D19 app-wide 18.016 and legacy 18.018/18.0 remain unchanged. The factor is NOT medically signed for use as a software-wide numerical policy.
- Display rounding `toStringAsFixed(1)` is demonstrated only in test; rounded strings are never resaved. Legacy 70/180 with no source unit returns `null` for conversion. A target may be `canBeSubmittedForReview` if structurally checkable, but there is **no method authorizing clinical classification**. A `sourceReference` string alone is NOT proof of a clinician's authentication.
- No actual patient record read/write, no clinical threshold, no user-facing target, no TIR, no backend/Drift/schema/API change, no Vercel deploy.

### Known patient-facing gaps — OPEN (do not mistake staging for correction)

1. Drift PatientProfiles columns have SQL defaults `70/180`, unknown historical source; G7 approved migration/rollback is needed.
2. Onboarding persists `70/180` regardless of preferred unit, Profile displays/saves raw target numbers; must be fixed together only once data contract reviewed.
3. Existing `GlucoseFormatter` falls back to mg/dL for unsupported display units; new candidate does not yet replace it. Producer→consumer audit and fail-closed runtime wiring still required.
4. Dashboard, journals, reports, CGM metrics and exports require G2/G5 clinical authority, verified measurement provenance and same-quantity comparisons before target classification.
5. Qualified review of G1/G4 numerics, G2–G5 target/metrics, G6 FR/AR RTL, G7 DB/privacy/rollback pending.
6. D22-specific FUE F01–F07 Chrome, BEFORE/AFTER 390/768/1280, a11y/keyboard, patient A/B isolation: NOT_RUN.

**Next exact:** CI exact HEAD and correction if red; when green document bounded pass. Then qualified G1/G4/G7 signatures, complete approved schema/model + UI producer/consumer patch, real FUE and certification, separate merge and Vercel authorization. Never infer the old 70/180 from numeric magnitude.
