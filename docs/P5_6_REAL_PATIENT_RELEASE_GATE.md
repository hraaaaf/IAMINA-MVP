# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **Baseline reviewed:** `main@a8762b22db50cb376b79ce20746e0d82761f9ff1`  
> **Pilot Readiness arithmetic:** 3/9 = 33.3%  
> **MENA arithmetic:** 32/38 = 84.2%  
> **Deployment:** no Vercel deployment is authorized by this gate.

## Goal

Permit real-patient pilot enablement only after the exact candidate release is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for one exact candidate release SHA:

1. issue #318 qualified clinical-human review requirements are satisfied;
2. issue #320 CNDP/legal/processor/residency requirements are satisfied with deployment-specific evidence;
3. the three repository fail-closed release audits below pass with `--require-approved` against the exact restricted evidence for that candidate;
4. the retained outputs are tied to the same exact release/deployment SHA;
5. a human release decision explicitly authorizes the real-patient pilot.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Proof boundary verified on 2026-09-11

The current tree contains all three fail-closed management commands required by the reopened gates:

| Gate | Verified command | Repository evidence | Current release result |
|---|---|---|---|
| Consent / processor governance | `python manage.py audit_pilot_consent_governance --require-approved` | `backend/core/management/commands/audit_pilot_consent_governance.py`, blob `4481b0455bc368cdc234de91248ca33d061acc0c` | **NOT RUN AS APPROVED RELEASE PROOF** |
| Morocco residency / foreign transfer | `python manage.py audit_pilot_data_residency --manifest /restricted/iamina/pilot-residency.json --require-approved` | `backend/core/management/commands/audit_pilot_data_residency.py`, blob `6eaed300cfe0719afbb1c897dbd7d9c9f24e0f02` | **NOT RUN AS APPROVED RELEASE PROOF** |
| Qualified clinical safety corpus | `python manage.py audit_safety_corpus_review --manifest /restricted/iamina/safety-review-manifest.json --require-approved` | `backend/core/management/commands/audit_safety_corpus_review.py`, blob `abd7cb951bd22282771c7754bb85ba8a4e0ebd72` | **NOT RUN AS APPROVED RELEASE PROOF** |

The recursive `backend/core` tree used for this verification reports `truncated: false`.

The commands themselves are explicitly fail-closed:

- consent governance raises a command error while required processor/regulatory evidence is pending;
- residency validation fails if its restricted manifest is missing, stale, incomplete or unapproved;
- safety-corpus validation fails if any required locale, case or parity dimension lacks approval.

This is engineering capability evidence only. It is **not** external approval evidence and it is **not** a release authorization.

## Reopened external gates

### #318 — Qualified clinical review

Current issue state: `OPEN / BLOCKED_EXTERNAL_HUMAN`.

Required retained evidence includes:

- qualified clinical-human verdict over the exact fingerprinted enabled corpus;
- safety-owner approval;
- final parity approval across text, voice transcript, mixed-language and transliteration rows;
- explicit decision for the rejected/staged variants;
- restricted manifest tied to the exact candidate release fingerprint.

### #320 — CNDP, processor and Morocco residency approval gate

Current issue state: `OPEN / BLOCKED_EXTERNAL_RELEASE`.

Required retained evidence includes:

- exact candidate release/deployed Git SHA;
- exact runtime/database/cache/email/export/provider topology and countries/regions;
- approved patient notice and consent wording;
- applicable CNDP health-data processing evidence for the actual pilot;
- applicable foreign-transfer evidence/basis for every actual external destination;
- account-specific processor evidence for every enabled external provider;
- restricted residency manifest tied to the exact deployed SHA.

The issue is the repository contract for this evidence. This document does not replace legal review or infer authorization from public provider documentation.

## Current decision matrix

| Dimension | State | Evidence |
|---|---|---|
| Fail-closed audit commands present | VERIFIED | exact current-tree command paths/blobs above |
| Synthetic/non-patient engineering rehearsal | VERIFIED | P5-5 retained closeout |
| Qualified clinical-human release approval | BLOCKED_EXTERNAL | #318 open |
| Deployment-specific CNDP/legal evidence | BLOCKED_EXTERNAL | #320 open |
| Processor/account-specific approvals | BLOCKED_EXTERNAL | #320 open |
| Residency/foreign-transfer restricted manifest approved | BLOCKED_EXTERNAL | #320 open |
| Exact candidate release audit outputs retained | MISSING | cannot exist before exact deployment evidence/manifests are supplied |
| Real-patient pilot authorization | **NO** | required gates are still open |

## Stop conditions

Real-patient enablement must stop if any of these is true:

- #318 is not satisfied;
- #320 is not satisfied;
- any `--require-approved` audit exits non-zero;
- the evidence fingerprint/SHA differs from the candidate release;
- the deployment topology differs from the reviewed manifest;
- a required human/legal release decision is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, production geography, clinical-human approval, real-device packaging approval, production deployment approval or permission to process real patient data.

Reopening #318/#320 restores the real-patient release gates that had previously been removed from the active engineering denominator. It does not change the retained MENA arithmetic and does not increment Pilot Readiness.

## Next exact action

Collect the restricted human/deployment evidence required by #318 and #320 for one frozen candidate release SHA, then execute and retain all three `--require-approved` audits against that exact candidate. Until then, P5-6 remains `ACTIVE / BLOCKED_EXTERNAL` and Pilot Readiness remains **3/9 = 33.3%**.
