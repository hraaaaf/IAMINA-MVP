# Pilot external approval handoff

**Status:** operational handoff only. This document does not constitute legal, privacy, security, processor, native-language or clinical approval.

**Pilot country:** Morocco

## 1. Purpose

The repository contains executable fail-closed gates for the remaining external pilot approvals. This handoff provides one deterministic order of operations for the human owners and release operator. It does not weaken, replace or bypass any underlying gate.

## 2. Hard stop: security issue #30

### Provenance correction

The historical PekPik values were present in `.claude/settings.local.json` from the initial IAMINA repository snapshot. That file is a local Claude/agent permission file; the later removal commit explicitly classified it as local agent settings containing secret material.

The project owner reports no knowledge of, or intentional account relationship with, PekPik. A connected-mailbox search found no PekPik registration/billing/account correspondence. Public PekPik documentation currently describes public test keys usable without registration.

Therefore IAMINA does **not** have evidence that the historical values were user-owned PekPik account credentials. The incident is classified as **public/test-key provenance plus forbidden historical secret-like material** unless contrary evidence appears.

This does not make the historical blob acceptable. `.claude/settings.local.json` remains a forbidden historical path and must be removed from all reachable Git refs.

Before issue #30 can close:

1. remove `.claude/settings.local.json` from every affected branch/tag using a reviewed history rewrite;
2. verify the rewritten mirror with the unchanged full-history scanner and `git fsck --full`;
3. force-update affected refs only after impact review;
4. require fresh clones and prevent stale history from being pushed back;
5. run tracked-tree and full-history scans from a fresh non-shallow clone;
6. activate the blocking push/pull-request history gate without weakening scanner logic;
7. obtain Security Reviewer and Release Certifier approval on the exact rewritten state.

Do **not** require the project owner to rotate or revoke a PekPik account credential unless independent evidence first demonstrates that a private/user-owned PekPik account credential existed.

Any missing history-remediation evidence is a **STOP**.

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

Human review must cover the fingerprinted corpus for French, Modern Standard Arabic, English, Moroccan Darija, script/transliteration variants, mixed-language cases, text/voice-transcript channels, every exact high-severity phrase, every clinical severity decision and every parity row.

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

1. complete and certify issue #30 Git history purge plus blocking history gate;
2. freeze the candidate release Git SHA;
3. complete CNDP, processor, contract, privacy and security evidence against that candidate deployment;
4. build the restricted residency manifest for the exact deployed SHA;
5. export the native/clinical review packet from the exact candidate release head;
6. obtain all native, clinical and parity approvals against its exact fingerprint;
7. run all three fail-closed `--require-approved` gates;
8. run standard exact-head CI, PostgreSQL source-of-truth, migration drift, secret hygiene, Bandit, OpenAPI, import-linter and Flutter gates;
9. obtain applicable independent Reviewer verdicts;
10. obtain Release Certifier approval;
11. merge/deploy only with expected-head protection and re-run post-merge/post-deploy evidence where required;
12. perform the real-patient pilot go/no-go only after every required gate is current.

## 7. Evidence matrix

| Lane | Required external/operational evidence | Repository proof | Result required |
|---|---|---|---|
| PekPik / Git history | provenance classification + affected-ref coordination; provider rotation only if private ownership is later proven | fresh non-shallow full-history scanner + blocking history gate | PASS |
| CNDP / processor | authorization, transfer basis, contracts, processor/subprocessor, retention/no-training, privacy/security | `audit_pilot_consent_governance --require-approved` | PASS |
| Residency | exact deployed topology, countries/regions, evidence references | `audit_pilot_data_residency --require-approved` | PASS |
| Native/clinical | locale reviewers, clinical decisions, parity decisions, safety-owner approval | `audit_safety_corpus_review --require-approved` | PASS |
| Release | none substituted by preparation work | exact-head CI + migration drift + specialized reviewers | PASS |

## 8. What this document does not close

Creating or updating this handoff does **not**:

- close issue #30;
- prove the historical blob has been purged;
- prove CNDP authorization;
- approve a processor or subprocessor;
- prove production geography;
- approve any native-language or clinical phrase;
- increase the MENA critical-path numerator;
- authorize a real-patient pilot.

The project remains blocked wherever underlying evidence is absent. The correct response to missing evidence is to stop, not to infer approval.
