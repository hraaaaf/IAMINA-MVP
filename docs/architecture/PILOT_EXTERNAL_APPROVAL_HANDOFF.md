# Pilot external approval handoff

**Status:** operational handoff only. This document does not constitute legal, privacy, security, processor, native-language or clinical approval.

**Pilot country:** Morocco

## 1. Purpose

The repository contains executable fail-closed gates for the remaining external pilot approvals. This handoff gives the deterministic order of operations for human owners and the release operator.

Canonical real-patient release gate:

`docs/P5_6_REAL_PATIENT_RELEASE_GATE.md`

## 2. Security history gate — CLOSED

Issue #30 reachable-history remediation is complete and no longer a current STOP:

- forbidden `.claude/settings.local.json` history was removed from reachable refs;
- fresh non-shallow history verification passed;
- rewritten `main` CI and migration drift passed;
- Security Reviewer and Release Certifier evidence was recorded;
- Gate A is certified 10/10.

Canonical closeout: PR #230 and `docs/assessments/2026-08-14-security-30-history-rewrite-certification.md`.

Any future reachable secret finding creates a new security STOP.

## 3. Gate A — consent, CNDP and processor approval

Authoritative engineering contract:

`docs/architecture/PILOT_CONSENT_PROCESSOR_GOVERNANCE.md`

External approval is not complete. The human approval owner must provide current restricted evidence for the exact candidate:

- final patient notice and consent wording;
- CNDP health-data processing authorization;
- foreign-transfer authorization or approved basis for every destination;
- exact processor, account, product/model and region for every runtime-approved external provider;
- subprocessors;
- current DPA and service terms;
- retention, deletion and no-training behavior;
- privacy approval;
- security approval.

Public provider pages are review inputs only and cannot substitute for account-specific evidence.

Restricted consent manifest:

`/restricted/iamina/pilot-consent-governance.json`

Release command:

```bash
cd backend
python manage.py audit_pilot_consent_governance \
  --manifest /restricted/iamina/pilot-consent-governance.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

A non-zero result is a **STOP**. Do not patch the validator or synthesize approvals to make it green.

## 4. Gate B — production residency and foreign transfers

Authoritative engineering contract:

`docs/architecture/PILOT_DATA_RESIDENCY_AND_TRANSFERS.md`

The deployment owner must produce a restricted manifest tied to the exact frozen candidate SHA and record verified locations for:

- application runtime;
- primary database;
- Redis/cache;
- password-reset e-mail;
- Firebase migration bridge when enabled;
- patient export staging;
- every registered external AI provider flow.

The manifest remains outside Git and uses opaque evidence references only. It must not contain secrets, patient identifiers, signed contracts or private regulator correspondence.

Release command:

```bash
cd backend
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

A missing, stale, failing or SHA-mismatched manifest is a **STOP**.

## 5. Gate C — native-language, clinical and parity approval

Authoritative engineering contracts:

- `docs/architecture/P0_MENA_2_HUMAN_REVIEW_GATE.md`
- `docs/architecture/P0_MENA_2_NATIVE_SAFETY_REVIEW.md`
- `docs/DARIJA_LEXICON_RUNTIME_PROMOTION_CONTRACT.md`

Substantial engineering evidence exists, but independent human approval remains required.

Generate the review packet from the final candidate code before obtaining the final approvals:

```bash
cd backend
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-review-packet.json
```

Release command:

```bash
cd backend
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

Any stale fingerprint, SHA mismatch, missing coverage, rejected decision or failing parity row is a **STOP**.

## 6. Candidate SHA rule

The exact candidate SHA is supplied explicitly:

```bash
export PILOT_RELEASE_SOURCE_SHA=<exact-40-char-git-sha>
```

All three approval audits must receive that same SHA, either through the environment variable above or `--expected-source-sha`.

A manifest created for candidate N cannot authorize N+1. Any code or configuration change after freeze invalidates the candidate approval package and requires a new SHA plus refreshed evidence where affected.

## 7. Provider live benchmark lane — separate dependency

Provider benchmarking does not authorize patient-data egress. Network providers remain unusable for patient data until their runtime processor policy is `APPROVED` and the candidate-bound restricted evidence covers the provider.

No provider score or approval may be fabricated from preparation artifacts.

## 8. Exact release order

1. Complete all intended code/configuration remediation first.
2. Merge the gate-hardening changes and require exact-main CI green.
3. Freeze the resulting immutable candidate Git SHA and export it as `PILOT_RELEASE_SOURCE_SHA`.
4. Capture the exact deployment/runtime/database/cache/e-mail/export/provider topology for that candidate.
5. Complete CNDP, consent, processor, contract, privacy and security evidence against that candidate and topology.
6. Build and approve the restricted consent and residency manifests with that exact SHA.
7. Generate the safety review packet from that candidate and obtain qualified native/clinical/safety-owner/parity approvals.
8. Run all three `--require-approved` audits with the same expected SHA.
9. Retain the outputs and confirm all show the frozen candidate SHA.
10. Obtain the explicit human release decision required by P5-6.
11. Deploy only under the project's explicit deployment authorization rules.
12. Perform the real-patient pilot go/no-go only after every required gate remains current.

If any code/configuration change occurs after step 3, return to step 2. Do not carry an old approval packet forward.

## 9. Current evidence matrix

| Lane | Engineering preparation | External/human approval | Release proof |
|---|---|---|---|
| Git history security | CLOSED | CLOSED | Gate A 10/10 / PR #230 |
| Exact-candidate release binding | ENGINEERING GATE | N/A | all 3 release audits must match `PILOT_RELEASE_SOURCE_SHA` |
| CNDP / processor | PREPARED | OPEN | candidate-bound consent manifest + audit |
| Residency / transfer | PREPARED | OPEN | candidate-bound residency manifest + audit |
| Native / clinical / parity | ENGINEERING PACKET PREPARED | OPEN | candidate-bound safety manifest + audit |
| Provider live benchmark | SEPARATE | OPEN where used | never substitutes for processor approval |

## 10. Non-claims

Updating this handoff does not:

- prove CNDP authorization;
- approve a processor or subprocessor;
- prove production geography;
- provide clinical-human or safety-owner approval;
- approve Darija runtime promotion;
- create live provider benchmark evidence;
- increase the MENA or Pilot Readiness numerator;
- authorize a real-patient pilot or a Vercel deployment.

Missing external evidence remains a STOP, not an invitation to infer approval.
