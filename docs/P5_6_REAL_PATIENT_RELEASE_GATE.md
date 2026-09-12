# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_FROZEN  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`  
> **Freeze proof:** canonical closeout PR #580 merged + exact-main CI #34683568116 SUCCESS  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **MENA arithmetic:** 32/38 = 84.2% retained pending separate arithmetic reconciliation  
> **Deployment:** no Vercel deployment is authorized by this gate.

## Goal

Permit real-patient pilot enablement only after one exact candidate release SHA is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for the frozen candidate SHA `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`:

1. issue #318 qualified clinical-human review requirements are satisfied;
2. issue #320 CNDP/legal/processor/residency requirements are satisfied with deployment-specific evidence;
3. the three repository fail-closed release audits pass with `--require-approved` and `--expected-source-commit-sha b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
4. residency and safety restricted manifests carry `source_commit_sha = b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
5. retained approved outputs contain `audited_source_commit_sha = b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
6. a human release decision explicitly authorizes the real-patient pilot.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Candidate freeze retained

The P5-6 candidate is frozen at:

`b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`

Freeze evidence:

- P5-1 Morocco linguistic certification CLOSED via issue #515;
- canonical P5-1 closeout PR #580 merged;
- resulting `main@b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
- exact-main post-merge CI #34683568116 — SUCCESS;
- issue #318 records `BLOCKED_EXTERNAL_HUMAN / CANDIDATE_FROZEN`;
- issue #320 records `BLOCKED_EXTERNAL_RELEASE / CANDIDATE_FROZEN`.

A later code, documentation or runtime change does not silently move this freeze. Any candidate change requires an explicit re-freeze and re-binding of all approval evidence.

## P5-1 prerequisite closed

P5-1 Morocco linguistic certification is closed via issue #515 and canonical closeout `docs/assessments/2026-09-12-p5-1-mena-linguistic-certification-closeout.md`.

Retained prerequisite evidence:

- PR #579 merged;
- exact-main linguistic evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`;
- post-merge CI #34682380854 — SUCCESS;
- post-merge Django migration drift #34682380897 — SUCCESS;
- exact-main workflow-dispatch packet #34683056185 — SUCCESS;
- artifact #10295285314;
- digest `sha256:496d2aae06ab3f9cea934f93d37a461a228433aca91dff9f67cad04e040a751b`;
- retained human approval of all five Morocco lanes recorded in #515.

This prerequisite closure does **not** satisfy #318, #320 or authorize real-patient processing.

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

Approved release audits for the frozen candidate must be executed exactly as follows:

```bash
python manage.py audit_pilot_consent_governance \
  --require-approved \
  --expected-source-commit-sha b560d97763a1a944d4a1a4cdf0e9f73467bfa78a

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha b560d97763a1a944d4a1a4cdf0e9f73467bfa78a

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha b560d97763a1a944d4a1a4cdf0e9f73467bfa78a
```

Fail-closed behavior:

- an approved audit without `--expected-source-commit-sha` fails;
- a non-40-character SHA fails;
- residency/safety fail when restricted-manifest `source_commit_sha` differs from the candidate SHA;
- successful approved output carries `audited_source_commit_sha`.

## External gates

### #318 — Qualified clinical review

Current state: `OPEN / BLOCKED_EXTERNAL_HUMAN / CANDIDATE_FROZEN`.

Required retained evidence:

- qualified clinical-human verdict over the exact fingerprinted enabled corpus;
- safety-owner approval;
- final parity approval across text, voice transcript, mixed-language and transliteration rows;
- explicit decision for the 21 rejected variants and 4 staged replacements;
- restricted safety manifest with `source_commit_sha = b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`.

### #320 — CNDP, processor and Morocco residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / CANDIDATE_FROZEN`.

Required retained evidence:

- exact candidate release/deployed Git SHA `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
- exact runtime/database/cache/email/export/provider topology and countries/regions;
- approved patient notice and consent wording;
- applicable CNDP health-data processing evidence for the actual pilot;
- applicable foreign-transfer evidence/basis for every actual external destination;
- account-specific processor evidence for every enabled external provider;
- restricted residency manifest with `source_commit_sha = b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`.

The issues are the repository contracts for this evidence. This document does not replace legal or clinical review and does not infer authorization from public provider documentation.

## Current decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-1 Morocco linguistic gate | CLOSED | #515 + exact-main v8 packet #34683056185 |
| P5-6 candidate SHA | FROZEN | `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a` + CI #34683568116 |
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
- residency/safety manifest SHA differs from `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`;
- deployment topology differs from the reviewed manifest;
- required human/legal release decision is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, production geography, clinical-human approval, real-device packaging approval, production deployment approval or permission to process real patient data.

Closing P5-1 changes Pilot Readiness arithmetic to 4/9 = 44.4%. It does not by itself change the retained MENA 32/38 arithmetic.

## Next exact action

Collect the external evidence required by #318 and #320 for frozen candidate `b560d97763a1a944d4a1a4cdf0e9f73467bfa78a`. Only after those approvals and restricted manifests exist may the three approved exact-SHA audits be executed. Until then, P5-6 remains `ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_FROZEN` and release posture remains `NOT_RELEASE_AUTHORIZED`.
