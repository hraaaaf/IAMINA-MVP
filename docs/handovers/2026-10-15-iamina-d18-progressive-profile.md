# IAMINA V1 — D18 progressive profile (backend data phase)

**Date:** 2026-10-15. **Status:** IN PROGRESS, not implemented in UI, NOT MERGED.
**PR:** [#1060](https://github.com/hraaaaf/IAMINA-MVP/pull/1060), `feat/v1-d18-progressive-demographics-weight-history-20261015`.
**Product approval:** decision #18 option A, Notion decision master (2026-10-08).
**P5 historical:** 6/12 = 50%, unchanged.

## Goal, success, proof

- **Goal:** progressive **optional** weight history (timestamp+unit+provenance), optional birth year (do not invent full DOB), optional patient-declared gender without inferential medical change. No mandatory onboarding step.
- **Success phase D18-A:** genuinely fresh account stores zero measurements and zero demographics; repeated patient weight append never overwrites previous entries; A/B physically and server-owner isolated; deterministic kg/lb conversion with original input preserved, optional year never fabricates exact birthday, export and deletion remain scoped.
- **Evidence:** exact-head Django/Postgres Ruff, migration drift and synthetic A/B unit tests. **Clinical/UI/PWA complete criteria not yet achieved.**

## BEFORE — verified

- `BasePatientProfile.weight` is one nullable scalar weight in kg, **no measured_at/unit/provenance or history**; `date_of_birth` optional date and `gender` nullable male/female, all optional.
- Existing local `PatientProfiles` had no progressive weight/history/age/gender fields, and the first-use onboarding only requires language/country.
- `PATCH /api/v1/profile` can overwrite scalar `weight`; a legacy scalar is NOT an established timestamped patient measurement and cannot be backfilled to a new history without evidence.

## Candidate phase D18-A

- New `core.PatientWeightObservation` has owner FK to Django User (cascade deletion), original weight/unit, deterministic canonical kg, `measured_at`, `created_at`, `patient_declared` provenance, unique `patient+client_uuid`, owner-time index; no other patient's UUID is treated as an owner proof.
- Append helper validates owner, UUID, finite strictly positive value, two-decimal precision, unit, aware timestamp and no implausibly future measurements. Duplicate identical UUID idempotent; conflicting content returns error, preserving prior row.
- Added nullable `BasePatientProfile.birth_year` (never inferred from `date_of_birth`) with `validated_birth_year` helper. Additive migration `core.0020` does not delete data or backfill historic scalar `weight`.
- Tests include empty identity, two weight records, unit conversion, retry/conflict, A/B namespace, invalid values, optional year and user deletion cascade. **No UI and no new remote upload API** pending D30 patient-vault binding and consent gates.
- **First code HEAD `650b53257995d74644722c57003044199cbc3fe8` failed** Python Ruff I001 imports and one test assuming Django User automatically created BasePatientProfile (it does not). Migration drift succeeded. Test assumption fixed, imports normalized; follow-up SHA `7d6db44675b2138e6ce11445970fb6f9b85da4eb` pending exact-head CI. Historical red runs do not prove subsequent green.

## Next exact and sequence

1. Verify current exact SHA CI, fix red failures until green. Verify generated schema migration consistency and PostgreSQL behaviour.
2. D18-B local-first vault-bound Drift additive table/migration, idempotent append, optional birth year/declared gender, A→B→A, backup/restore, no clinical egress without consent. Never read unscoped legacy weight as a patient measurement.
3. **UI mandatory protocol:** BEFORE screenshots for profile same mobile/desktop viewports → written Goal → approved-looking mockup/reference → implementation → AFTER same viewports → visual score + widget/accessibility tests. User has not yet viewed/approved target for D18.
4. Independent privacy/clinical review for weight interpretation, gender identity vs biological parameters, user-requested data export/deletion; no treatment or target adaptation based on demographics.
5. Release to Vercel **synthetic-only lab** after CI, review/authorized deployment. No patient trial claims. D11 separate smoke test/user checks remain open.

**HUMAN GATES:** real patient privacy approval, release outside Vercel test lab; sensitive UI choices if user input is required.
