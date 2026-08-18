# MENA Safety Corpus Human Review Runbook

Status: **ACTIVE HUMAN-GATE RUNBOOK / NO APPROVAL RECORDED**  
Tracker: issue #318

## Goal

Produce the restricted human evidence required by `audit_safety_corpus_review --require-approved` against one exact current corpus fingerprint, without committing reviewer identities or private evidence to Git.

## Preconditions

- candidate Git SHA frozen;
- PR #324 (or successor) merged so the Darija clinical packet is internally consistent;
- qualified reviewers assigned for required locales and clinical safety;
- safety owner identified;
- restricted evidence store available outside Git.

## 1. Export the authoritative packet

From the exact candidate SHA:

```bash
cd backend
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-corpus-review-packet.json
```

The command writes the fingerprinted synthetic packet atomically with mode 0600. The exported fingerprint, case inventory and required parity dimensions are authoritative for the review batch.

Do not review an older exported packet after the safety corpus changes.

## 2. Record locale/native review

The manifest requires all configured locales: `fr`, `ar`, `en`, `ar-MA`.

For each locale, controlled evidence must include:

- opaque native reviewer reference;
- opaque qualification reference;
- `approved` or `rejected` decision tied to the exported fingerprint.

Existing Darija native evidence from PR #247 may be used only if the reviewer/evidence owner confirms it remains applicable to the exact current fingerprint and the restricted manifest requirements.

## 3. Record clinical review for every exported case

For each exported `case_id`, the qualified clinical reviewer must record:

- `native_decision`: `approved` or `rejected`;
- `clinical_decision`: `approved` or `rejected`;
- optional opaque issue reference for any finding.

Clinical review must verify that the expected classification is appropriate and does not convert symptom vocabulary into diagnosis, prescribing, dose advice or treatment optimization.

For the Darija remediation delta, use:

- `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md`;
- `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_RECEIPT_TEMPLATE.md`;
- `docs/assessments/2026-08-18-darija-clinical-ai-prereview.md` as non-authoritative preparation only.

## 4. Record parity review

Review every parity tuple emitted by the exported packet. Each tuple needs:

- locale;
- channel;
- input form;
- opaque reviewer reference;
- `approved` or `rejected`.

Technical parity tests do not substitute for this restricted human approval.

## 5. Build the restricted manifest

The manifest schema is defined by `backend/core/safety_corpus_review.py` and requires exactly:

- `schema_version`;
- `corpus_fingerprint`;
- `source_commit_sha`;
- `review_batch_reference`;
- `clinical_approval_reference`;
- `safety_owner_approval_reference`;
- `reviewed_on`;
- `review_due_on`;
- `locale_reviews`;
- `case_reviews`;
- `parity_reviews`.

Use opaque references only. Do not commit names, emails, phone numbers, certificates or signed approval documents.

## 6. Fail-closed verification

```bash
cd backend
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved
```

A non-zero result is **STOP**. Do not mark #318 complete and do not promote Darija runtime remediation.

## 7. Exit criteria

Issue #318 may close only when:

- the manifest matches the exact current corpus fingerprint;
- all required locale reviews are present and approved;
- every case has approved native + clinical decisions;
- every required parity tuple is approved;
- clinical approval reference exists;
- safety-owner approval reference exists;
- review dates are current;
- `audit_safety_corpus_review --require-approved` exits successfully on the exact candidate SHA.

A successful #318 gate still does not itself authorize provider cutover, CNDP release approval or any unrelated deployment gate.
