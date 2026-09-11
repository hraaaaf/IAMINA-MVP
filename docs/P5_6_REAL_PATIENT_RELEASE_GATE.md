# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **Engineering gate baseline verified:** `main@b27a71f4c337265e4351bb49b5c727c2b9b78dc5`  
> **Pilot Readiness arithmetic:** 3/9 = 33.3%  
> **MENA arithmetic:** 32/38 = 84.2%  
> **Deployment:** no Vercel deployment is authorized by this gate.

## Goal

Permit real-patient pilot enablement only after one exact candidate release SHA is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for one exact candidate release SHA:

1. issue #318 qualified clinical-human review requirements are satisfied;
2. issue #320 CNDP/legal/processor/residency requirements are satisfied with deployment-specific evidence;
3. the three repository fail-closed release audits pass with `--require-approved` and the same `--expected-source-commit-sha <40-char SHA>`;
4. residency and safety restricted manifests carry the same `source_commit_sha` as the candidate SHA;
5. retained approved outputs contain `audited_source_commit_sha` equal to that candidate SHA;
6. a human release decision explicitly authorizes the real-patient pilot.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Engineering gate proof retained

PR #574 hardened the release gate so approval evidence cannot silently drift across candidate SHAs.

Verified evidence:

- PR #574 exact head `79ea16893545be0748b462be0a4b5bc47cdba41d`;
- exact-head CI `#34637628458` — SUCCESS;
- exact-head Django migration drift `#34637628453` — SUCCESS;
- merged main `b27a71f4c337265e4351bb49b5c727c2b9b78dc5`;
- post-merge CI `#34642183422` — SUCCESS;
- post-merge Django migration drift `#34642183363` — SUCCESS.

This proves the SHA-binding mechanism and its repository integration. It does **not** prove any external approval.

## Exact-SHA release audit contract

Approved release audits must be executed with the same candidate SHA:

```bash
python manage.py audit_pilot_consent_governance \
  --require-approved \
  --expected-source-commit-sha <CANDIDATE_SHA>

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <CANDIDATE_SHA>

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha <CANDIDATE_SHA>
```

Fail-closed behavior:

- an approved audit without `--expected-source-commit-sha` fails;
- a non-40-character SHA fails;
- residency/safety fail when restricted-manifest `source_commit_sha` differs from the candidate SHA;
- successful approved output carries `audited_source_commit_sha`.

## Reopened external gates

### #318 — Qualified clinical review

Current state: `OPEN / BLOCKED_EXTERNAL_HUMAN`.

Required retained evidence:

- qualified clinical-human verdict over the exact fingerprinted enabled corpus;
- safety-owner approval;
- final parity approval across text, voice transcript, mixed-language and transliteration rows;
- explicit decision for rejected/staged variants;
- restricted safety manifest tied to the exact candidate release SHA.

### #320 — CNDP, processor and Morocco residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE`.

Required retained evidence:

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
| Fail-closed audit commands present | VERIFIED | repository commands under `backend/core/management/commands/` |
| Exact-SHA binding implementation | VERIFIED | PR #574 + exact-head/post-merge green runs above |
| Synthetic/non-patient engineering rehearsal | VERIFIED | P5-5 retained closeout |
| Qualified clinical-human release approval | BLOCKED_EXTERNAL | #318 open |
| Deployment-specific CNDP/legal evidence | BLOCKED_EXTERNAL | #320 open |
| Processor/account-specific approvals | BLOCKED_EXTERNAL | #320 open |
| Residency/foreign-transfer restricted manifest approved | BLOCKED_EXTERNAL | #320 open |
| Exact candidate approved audit outputs retained | MISSING | cannot exist before restricted approvals/manifests exist |
| Real-patient pilot authorization | **NO** | required gates are still open |

## Stop conditions

Real-patient enablement must stop if any of these is true:

- #318 is not satisfied;
- #320 is not satisfied;
- any `--require-approved` audit exits non-zero;
- approved audit output lacks the exact candidate `audited_source_commit_sha`;
- residency/safety manifest SHA differs from the candidate release SHA;
- deployment topology differs from the reviewed manifest;
- required human/legal release decision is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, production geography, clinical-human approval, real-device packaging approval, production deployment approval or permission to process real patient data.

The retained MENA arithmetic and Pilot Readiness arithmetic remain unchanged by this gate-hardening work.

## Next exact action

After this documentation-only closeout lands and its exact-main CI is green, freeze that resulting main SHA in issues #318 and #320 as the candidate for external review. Then collect the restricted human/deployment evidence and execute all three approved audits against that same SHA. Until those external gates are satisfied, P5-6 remains `ACTIVE / BLOCKED_EXTERNAL` and Pilot Readiness remains **3/9 = 33.3%**.
