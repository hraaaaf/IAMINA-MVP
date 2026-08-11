# Pilot external approval handoff

**Status:** operational handoff only. This document does not constitute legal, privacy, security, processor, native-language or clinical approval.

**Pilot country:** Morocco

## 1. Purpose

The repository already contains executable fail-closed gates for the remaining external pilot approvals. The remaining risk is operational fragmentation: security rotation, processor/CNDP approval, deployment residency evidence and native/clinical review are documented separately.

This handoff provides one deterministic order of operations for the human owners and the release operator. It does not weaken, replace or bypass any underlying gate.

## 2. Hard stop: security issue #30

Before destructive Git remediation or pilot approval can proceed, the security owner must confirm restricted evidence for all of the following:

- every potentially affected PekPik credential has been revoked or rotated;
- PekPik provider activity logs have been reviewed from the first known exposure onward;
- every real deployed and developer environment has been checked and no old credential remains active;
- the restricted evidence ledger contains only opaque references and has security-owner approval.

Do not place credential values, provider-private logs, screenshots containing secrets or replacement tokens in Git, GitHub issues, PRs or chat.

Only after those four facts are approved may the repository history be rewritten according to `docs/security/SECRET_HISTORY_AND_ROTATION.md`.

After the rewrite:

1. force-update every affected branch/tag during the approved maintenance window;
2. require fresh clones so old history cannot be pushed back;
3. run `scripts/audit_git_history_secrets.py` from a fresh full non-shallow checkout;
4. require a clean tracked-tree scan and a clean reachable-history scan;
5. activate the blocking push/pull-request history gate without weakening scanner logic;
6. obtain Security Reviewer and Release Certifier approval on the exact rewritten head.

Any missing security evidence is a **STOP**.

## 3. Consent, CNDP and processor approval

Authoritative engineering contract:

`docs/architecture/PILOT_CONSENT_PROCESSOR_GOVERNANCE.md`

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

A non-zero result is a **STOP**. Do not patch the validator or change approval state merely to make the command green.

## 4. Production residency and foreign-transfer manifest

Authoritative engineering contract:

`docs/architecture/PILOT_DATA_RESIDENCY_AND_TRANSFERS.md`

The deployment owner must produce a restricted manifest tied to the **exact deployed Git SHA** and record the verified locations for:

- application runtime;
- primary database;
- Redis/cache;
- password-reset e-mail;
- Firebase migration bridge when enabled;
- patient export staging;
- every registered external AI provider flow.

The manifest must remain outside Git and contain opaque evidence references only. It must not contain connection strings, tokens, passwords, private keys, patient identifiers, signed contracts or private regulator correspondence.

Release command:

```bash
cd backend
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved
```

A missing, stale or failing manifest is a **STOP**.

## 5. Native-language, clinical and parity review

Authoritative engineering contract:

`docs/architecture/P0_MENA_2_NATIVE_SAFETY_REVIEW.md`

Generate the exact review packet from the candidate release head:

```bash
cd backend
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-review-packet.json
```

Human review must cover the fingerprinted corpus for:

- French;
- Modern Standard Arabic;
- English;
- Moroccan Darija;
- Darija Arabic script;
- Darija Latin transliteration;
- mixed-language cases;
- text and voice-transcript channels;
- every exact high-severity phrase;
- every clinical severity decision;
- every locale/channel/input-form parity row.

Reviewer identities and direct contact information must not be committed. Use opaque reviewer/evidence references in the restricted manifest.

Release command:

```bash
cd backend
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved
```

Any stale fingerprint, missing coverage, rejected decision or failing parity row is a **STOP**.

## 6. Exact release order

The release operator must use this sequence:

1. confirm issue #30 external rotation/log/environment evidence is approved;
2. complete and certify the Git history rewrite and blocking history gate;
3. freeze the candidate release Git SHA;
4. complete CNDP, processor, contract, privacy and security evidence against that candidate deployment;
5. build the restricted residency manifest for the exact deployed SHA;
6. export the native/clinical review packet from the exact candidate release head;
7. obtain all native, clinical and parity approvals against its exact fingerprint;
8. run all three fail-closed `--require-approved` gates;
9. run the standard exact-head CI, PostgreSQL source-of-truth suite, migration drift, secret hygiene, Bandit, OpenAPI, import-linter and Flutter gates;
10. obtain the applicable independent Reviewer verdicts;
11. obtain Release Certifier approval;
12. merge/deploy only with expected-head protection and re-run post-merge/post-deploy evidence where required;
13. perform the real-patient pilot go/no-go only after every required gate is current.

## 7. Evidence matrix

| Lane | Human owner evidence | Repository proof | Result required |
|---|---|---|---|
| PekPik / Git history | rotation/revocation, provider-log review, deployed-environment verification | full non-shallow history scanner + blocking history gate | PASS |
| CNDP / processor | authorization, transfer basis, contracts, processor/subprocessor, retention/no-training, privacy/security | `audit_pilot_consent_governance --require-approved` | PASS |
| Residency | exact deployed topology, countries/regions, evidence references | `audit_pilot_data_residency --require-approved` | PASS |
| Native/clinical | locale reviewers, clinical decisions, parity decisions, safety-owner approval | `audit_safety_corpus_review --require-approved` | PASS |
| Release | none substituted by preparation work | exact-head CI + migration drift + specialized reviewers | PASS |

## 8. What this document does not close

Creating or updating this handoff does **not**:

- close issue #30;
- prove PekPik credentials were rotated;
- authorize a history rewrite;
- prove CNDP authorization;
- approve a processor or subprocessor;
- prove production geography;
- approve any native-language or clinical phrase;
- increase the MENA critical-path numerator;
- authorize a real-patient pilot.

The project remains blocked wherever the underlying external evidence is absent. The correct response to missing evidence is to stop, not to infer approval.
