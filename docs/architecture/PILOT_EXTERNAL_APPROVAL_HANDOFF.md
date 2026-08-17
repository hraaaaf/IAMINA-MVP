# Pilot external approval handoff

**Status:** operational handoff only. This document does not constitute legal, privacy, security, processor, native-language or clinical approval.

**Pilot country:** Morocco

## 1. Purpose

The repository contains executable fail-closed gates for the remaining external pilot approvals. This handoff gives the current deterministic order of operations for human owners and the release operator.

## 2. Security history gate — CLOSED

Issue #30 reachable-history remediation is complete and no longer a current STOP:

- forbidden `.claude/settings.local.json` history was removed from reachable refs;
- fresh non-shallow history verification passed;
- rewritten `main` CI and migration drift passed;
- Security Reviewer and Release Certifier evidence was recorded;
- Gate A is now certified 10/10.

Canonical closeout: PR #230 and `docs/assessments/2026-08-14-security-30-history-rewrite-certification.md`.

Do not reopen or weaken the permanent history scanner. Any future reachable secret finding creates a new security STOP.

## 3. Remaining Pilot Safety gate A — consent, CNDP and processor approval

Authoritative engineering contract:

`docs/architecture/PILOT_CONSENT_PROCESSOR_GOVERNANCE.md`

Engineering preparation is complete through PR #34, but approval is not.

The human approval owner must provide current restricted evidence for:

- final patient notice and consent wording;
- CNDP health-data processing authorization;
- foreign-transfer authorization or approved basis for every destination;
- exact processor, account, product/model and region;
- exact subprocessors;
- current DPA and service terms;
- retention, deletion and no-training behavior;
- privacy approval;
- security approval.

Public provider pages are review inputs only and cannot substitute for account-specific evidence.

Release command:

```bash
cd backend
python manage.py audit_pilot_consent_governance --require-approved
```

A non-zero result is a **STOP**. Do not patch the validator or synthesize approvals to make it green.

## 4. Remaining Pilot Safety gate B — production residency and foreign transfers

Authoritative engineering contract:

`docs/architecture/PILOT_DATA_RESIDENCY_AND_TRANSFERS.md`

Engineering preparation is complete through PR #35, but the exact deployment manifest is not approved.

The deployment owner must produce a restricted manifest tied to the **exact deployed Git SHA** and record verified locations for:

- application runtime;
- primary database;
- Redis/cache;
- password-reset e-mail;
- Firebase migration bridge when enabled;
- patient export staging;
- every registered external AI provider flow.

The manifest remains outside Git and uses opaque evidence references only. It must not contain connection strings, tokens, passwords, private keys, patient identifiers, signed contracts or private regulator correspondence.

Release command:

```bash
cd backend
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved
```

A missing, stale or failing manifest is a **STOP**.

## 5. Remaining Pilot Safety gate C — native-language, clinical and parity approval

Authoritative engineering contracts:

- `docs/architecture/P0_MENA_2_HUMAN_REVIEW_GATE.md`
- `docs/architecture/P0_MENA_2_NATIVE_SAFETY_REVIEW.md`
- `docs/DARIJA_LEXICON_RUNTIME_PROMOTION_CONTRACT.md`

Substantial evidence is already complete:

- RTL technical certification: PR #36;
- exact Darija high-severity native review: PR #247, 36/36 variants;
- staged fail-closed Darija remediation: PR #255;
- technical 2-channel × 3-input-form Darija parity: PR #256;
- clinical-human review worksheet: `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md`.

Still required:

- qualified clinical-human approval;
- safety-owner/restricted approval;
- required native-human receipts for other enabled baseline locales where absent;
- restricted parity approval;
- exact current safety-corpus fingerprint;
- explicit runtime-promotion approval before the staged Darija delta can be applied.

Generate the exact release-head review packet:

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
  --require-approved
```

Any stale fingerprint, missing coverage, rejected decision or failing parity row is a **STOP**.

## 6. Provider live benchmark lane — separate external evidence dependency

P0-MENA-4 execution tooling is prepared through PRs #18–#22, but no live provider ranking or production cutover is approved.

Before live execution, obtain current provider/legal evidence, approved credentials/environment, budget/network authorization and applicable human review. No provider scores may be fabricated from preparation artifacts.

## 7. Exact release order from current state

1. Freeze the candidate release Git SHA.
2. Complete CNDP, processor, contract, privacy and security evidence against that candidate deployment.
3. Build and approve the restricted residency manifest for the exact deployed SHA.
4. Export the native/clinical review packet from the exact candidate release head.
5. Obtain required native, clinical, safety-owner and parity approvals against its exact fingerprint.
6. Apply any approved Darija remediation atomically, then regenerate fingerprint/evidence and recertify.
7. Run the three fail-closed approval gates.
8. Run exact-head CI, PostgreSQL source-of-truth, migration drift, secret hygiene, Bandit, OpenAPI, import-linter and Flutter gates.
9. Obtain applicable independent Reviewer verdicts and Release Certifier approval.
10. Deploy only under the project's explicit deployment authorization rules and re-run post-deploy evidence where required.
11. Perform the real-patient pilot go/no-go only after every required gate is current.

## 8. Current evidence matrix

| Lane | Engineering preparation | External/human approval | Release proof |
|---|---|---|---|
| Git history security | CLOSED | CLOSED | Gate A 10/10 / PR #230 |
| CNDP / processor | READY, PR #34 | OPEN | `audit_pilot_consent_governance --require-approved` |
| Residency / transfer | READY, PR #35 | OPEN | `audit_pilot_data_residency --require-approved` |
| Native / clinical / parity | PARTIAL; Darija native + technical parity advanced | OPEN | `audit_safety_corpus_review --require-approved` |
| Provider live benchmark | READY TO EXECUTE WHEN AUTHORIZED | OPEN | live reports + approved decision matrix |

## 9. Non-claims

Updating this handoff does not:

- prove CNDP authorization;
- approve a processor or subprocessor;
- prove production geography;
- provide clinical-human or safety-owner approval;
- approve Darija runtime promotion;
- create live provider benchmark evidence;
- increase the MENA critical-path numerator;
- authorize a real-patient pilot or a Vercel deployment.

Missing external evidence remains a STOP, not an invitation to infer approval.
