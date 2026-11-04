# IAMINA — Backend CI policy expiry audit — 2026-11-04

## Goal / success / evidence
Goal: explain both red backend CI jobs without bypassing clinical/privacy safety gates.
Success: source-level root causes documented, required human review identified, and independent regression path specified.
Evidence: CI run #41749225511, SQLite job #126309917605 and PostgreSQL job #126309917551; source code on main.

## Verified failures
- `core/incident_response.py`: `POLICY.review_due_on = date(2026, 11, 2)`; `validate()` fails closed if `review_due_on < date.today()`. This also prevents tests expecting PII-rejection errors from reaching `assert_minimized_incident_text`, producing misleading regex failures. This is an error-ordering consequence, not proof that the PII regex is defective.
- `core/emergency_operating_mode.py`: `PILOT_EMERGENCY_POLICY.review_due_on = date(2026, 11, 2)`; `validate()` fails closed. Mode remains `SELF_CARE_ONLY`, `human_monitoring=False`; preserve these truthful disclosures.
- `core/retention_policy.py`: `_REVIEW_DUE = date(2026, 11, 2)`, shared by all six `RETENTION_RULES`. `validated_retention_schedule()` fails on first dataset `raw_ai_media_in_application`; the log does **not** establish that only this dataset is stale.
- Both backend jobs fail for the same policy-expiry causes; D15 frontend job #126309917604 SUCCESS. No evidence of a database connectivity regression.

## Decision / gate
**DO NOT** extend dates, monkeypatch the clock, skip tests, or remove fail-closed validation to make CI green. A review is required by the policy owners (IAmina Safety & Security, IAmina Safety & Compliance, IAmina Privacy & Security). Confirm emergency service wording and jurisdiction, incident severity/roles/escalation, all six retention datasets and actual deletion behavior, and evidence for any renewed review date. Clinical, privacy, and legal requirements need explicit sign-off.

## Execution after approval
1. Record reviewer, date, scope, evidence and next review date in canonical governance documentation.
2. Update only the approved policy dates/content in the three source files.
3. Run targeted incident, emergency and retention tests in both backend environments, including negative PII tests; then full CI.
4. Verify stale-date negative tests still fail closed. Merge only after review and green CI. No Vercel deployment without explicit authorization.

Status: **AUDIT COMPLETE; POLICY RENEWAL BLOCKED BY HUMAN COMPLIANCE REVIEW.** No operational policy was changed.

## Test review findings (2026-11-04)
- `core/tests/test_incident_response.py` exercises SEV1/SEV2, redaction of email, Moroccan phone and `patient_id`, and secure incident-file permissions (0600). These currently hit the stale-policy guard before exercising their intended assertions. Do not remove that guard.
- `core/tests/test_emergency_operating_mode.py` checks SELF_CARE_ONLY, no automatic human monitoring, disclosure idempotence and FR/EN/AR/Darija text. The historical test uses `today=date(2026,8,2)` for the policy object; this is not proof of validity on 2026-11-04.
- `core/tests/test_retention_deletion.py` tests unique schedule, raw-media non-persistence, legal hold, grace period, dry-run and confirmed deletion. Schedule test uses today's actual date and rightly fails after the 2026-11-02 review deadline.
- CI #41750392958 on this docs-only PR is SUCCESS but backend/frontend jobs are SKIPPED; this is not a green backend certification.

## Required approval record (not yet supplied)
For each of the three policy owners, record: accountable reviewer identity/role, date reviewed, evidence of operational controls, approved policy text and dates, exceptions and risks, and the next review deadline. For retention, inspect all six datasets individually, including backup expiry and legal holds. A generic “Go” does not establish these facts.

## Additional regression proof after review
Add negative tests using explicit `today` beyond `review_due_on` to prove fail-closed behavior persists. Verify PII-rejection tests reach the identifier guard when the policy is valid. Keep CI jobs non-skipped and require both SQLite and PostgreSQL SUCCESS.

## Authorized renewal — 2026-11-04
The project owner explicitly approved the **2027-02-04** next review due date for the three policy families in the conversation. This approval authorizes the date changes; it is **not** independent evidence of operational policy effectiveness.

- Incident response: `POLICY.review_due_on` 2026-11-02 → **2027-02-04**.
- Emergency SELF_CARE_ONLY: `PILOT_EMERGENCY_POLICY.review_due_on` 2026-11-02 → **2027-02-04**; mode, disclosures and monitoring claim unchanged.
- Retention: shared `_REVIEW_DUE` 2026-11-02 → **2027-02-04**, covering six datasets; no retention durations, deletion actions or legal-hold flags changed.
- Added explicit future-expiry fail-closed regression tests for the three policy families. Existing tests still cover direct-identifier rejection, emergency disclosures and retention/deletion behavior.
- CI runs associated with the latest code commit must demonstrate SQLite and PostgreSQL backend success before closing. No Vercel deployment is authorized.

Historical pre-approval audit text above describes the state **before** this owner authorization; the approved next-review date is now recorded here.
