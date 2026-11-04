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
