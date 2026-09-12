# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `fd3e4a53543e515100b493acc63c99cc9e8464ce`  
> **Safety corpus:** 59 exact cases / 10 technical parity tuples  
> **Safety fingerprint:** `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **MENA arithmetic:** 32/38 = 84.2% retained pending separate reconciliation  
> **Deployment:** no Vercel deployment is authorized by this gate.

## Goal

Permit real-patient pilot enablement only after one exact frozen release SHA is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for frozen candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce`:

1. #318 has a valid restricted safety-review manifest covering the exact 59-case fingerprint and all 10 parity tuples;
2. #320 CNDP/legal/processor/residency requirements are satisfied with deployment-specific evidence;
3. the three fail-closed release audits pass with `--require-approved` and `--expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce`;
4. residency and safety restricted manifests carry `source_commit_sha = fd3e4a53543e515100b493acc63c99cc9e8464ce`;
5. retained approved outputs carry `audited_source_commit_sha = fd3e4a53543e515100b493acc63c99cc9e8464ce`;
6. a human release decision explicitly authorizes the real-patient pilot.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Deliberate candidate re-freeze after consent-evidence contract

The prior frozen candidate `a25ec4dd1118784c8968588bab035dca4d0f71b6` is superseded for P5-6 because PR #591 changed runtime consent/release behavior. The freeze is therefore moved explicitly rather than silently drifting with `main`.

The new candidate is:

`fd3e4a53543e515100b493acc63c99cc9e8464ce`

Re-freeze proof:

- PR #591 `P5-6: bind AI consent to exact notice evidence`;
- exact PR head `b018f724aeaa7b34217cd2810c35e95881332ee1`;
- exact-head CI run #4145 / workflow run `34708902735` — SUCCESS;
- exact-head Django migration drift run #3719 / workflow run `34708902710` — SUCCESS;
- merge `main@fd3e4a53543e515100b493acc63c99cc9e8464ce`;
- GitHub merge signature — verified/valid;
- merge tree `b206837824cd67f05b541efd59336cb358851f21`;
- post-merge CI run #4148 / workflow run `34709544750` — SUCCESS;
- post-merge Django migration drift run #3722 / workflow run `34709544765` — SUCCESS;
- post-merge P5-5 rehearsal #101, UI geometry #522, UI missing-routes #58 and UI browser screenshot #525 — SUCCESS.

PR #591 changed consent evidence, account consent API, egress/provider release checks, migration/model state, Flutter consent storage/gating, tests and OpenAPI. Its 32-file diff did **not** modify the safety corpus. Therefore the retained safety corpus remains **59 exact cases / 10 parity tuples** with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

A later code or runtime change does not silently move this freeze. A documentation-only closeout may move repository `main` without moving the frozen candidate. Any future candidate change requires another explicit re-freeze and re-binding of approval/manifests.

## Consent evidence contract now retained in the frozen candidate

Candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce` now enforces:

- exact consent notice version/hash/locale evidence;
- legacy timestamp-only consent invalidation and re-consent;
- server receipt creation for acceptance;
- withdrawal clearing active proof and revoking granular media grants;
- central outbound-AI egress verification against current notice proof;
- consent epoch separation for media grants;
- Flutter fail-closed behavior when server acceptance fails;
- local UI gating requiring both Drift consent timestamp and current Secure Storage evidence;
- local-only release scope excluding disabled external providers while retaining global CNDP health-processing blockers.

Notice version retained by this candidate: `2026-09-12.1`.

## Qualified-human safety review outcome

The project owner attests that a qualified clinical reviewer completed the 2026-09-12 safety review. The review produced explicit adjudication of challenged Darija rows and the following merged runtime result:

- 16 rejected/rewrite-required Latin variants removed;
- approved replacements `dekht`, `fiya doukha`, `kantra33ad` promoted;
- explicitly re-approved unchallenged forms retained;
- historical native-review fixtures preserved as provenance instead of being rewritten to impersonate the new runtime;
- English lane explicitly validated by the user during the same review session;
- safety-owner/parity behavior explicitly approved by project-owner attestation.

The exact enabled corpus contains **59 cases** with **10 technical `(locale, channel, input_form)` parity tuples**.

Exact fingerprint:

`823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`

### Evidence boundary

GitHub does not independently verify reviewer identity or qualifications. The attestation is not a substitute for the manifest's required real opaque evidence and qualification references.

#318 remains open until the restricted manifest can be populated with real references and passes the exact-SHA audit.

## P5-1 prerequisite retained

P5-1 Morocco linguistic certification remains closed via #515 and canonical closeout `docs/assessments/2026-09-12-p5-1-mena-linguistic-certification-closeout.md`.

Retained evidence:

- PR #579 merged;
- exact-main linguistic evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`;
- post-merge CI #34682380854 — SUCCESS;
- post-merge Django migration drift #34682380897 — SUCCESS;
- exact-main packet #34683056185 — SUCCESS;
- artifact #10295285314;
- digest `sha256:496d2aae06ab3f9cea934f93d37a461a228433aca91dff9f67cad04e040a751b`;
- retained human approval recorded in closed issue #515.

This prerequisite does not satisfy #318 or #320 and does not authorize real-patient processing.

## Exact-SHA release audit contract

```bash
python manage.py audit_pilot_consent_governance \
  --require-approved \
  --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce
```

Fail-closed behavior retained:

- an approved audit without `--expected-source-commit-sha` fails;
- a non-40-character SHA fails;
- residency/safety fail when restricted-manifest `source_commit_sha` differs from the frozen candidate;
- safety fails on missing/stale/partial/fingerprint-mismatched/rejected evidence;
- successful approved output carries `audited_source_commit_sha`.

## External gates

### #318 — Qualified clinical/safety evidence

Current state: `OPEN / REVIEW_ATTESTED / RUNTIME_CUTOVER_MERGED / RESTRICTED_QUALIFICATION_REFERENCES_PENDING / CANDIDATE_REFROZEN`.

Completed:

- qualified-clinical review attested by project owner;
- challenged Darija rows adjudicated and runtime cutover merged;
- owner safety/parity approval attested;
- English lane explicitly validated;
- exact candidate/fingerprint/case-count/parity-count frozen.

Still required:

- real opaque clinical/safety approval references;
- locale-review evidence references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references for those locale reviews;
- complete approved `case_reviews` for all 59 current case IDs;
- complete approved `parity_reviews` for all 10 required tuples;
- restricted safety manifest bound to the exact frozen SHA/fingerprint;
- exact-SHA `audit_safety_corpus_review --require-approved` PASS.

### #320 — CNDP, processor and Morocco residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / CANDIDATE_REFROZEN`.

Still required for `fd3e4a53543e515100b493acc63c99cc9e8464ce`:

- actual runtime/database/cache/email/export/provider topology and countries/regions;
- approved patient notice and consent wording for the actual pilot;
- applicable CNDP health-data processing evidence;
- applicable foreign-transfer basis/evidence for every actual external destination;
- account-specific processor/DPA/subprocessor/retention/deletion/no-training/privacy/security evidence;
- restricted residency manifest bound to the frozen SHA;
- exact-SHA consent/residency audit PASS outputs.

No public provider documentation is sufficient by itself to claim these account/deployment-specific approvals.

## Current decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-1 Morocco linguistic gate | CLOSED | #515 + exact-main v8 packet #34683056185 |
| P5-6 candidate | REFROZEN | `fd3e4a53543e515100b493acc63c99cc9e8464ce` + #4145/#3719 + #4148/#3722 |
| Consent-evidence runtime contract | MERGED / GREEN | #591 |
| Safety corpus fingerprint | VERIFIED / unchanged | `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5` |
| Safety corpus / parity | VERIFIED / unchanged | 59 cases / 10 tuples |
| Human clinical review | ATTESTED_COMPLETE | #318 + 2026-09-12 retained session |
| Restricted qualification/evidence references | MISSING | #318 remains open |
| Deployment-specific CNDP/legal evidence | BLOCKED_EXTERNAL | #320 |
| Processor/account-specific approvals | BLOCKED_EXTERNAL | #320 |
| Residency/foreign-transfer restricted manifest | BLOCKED_EXTERNAL | #320 |
| Three exact-candidate approved audit outputs | MISSING | cannot pass before restricted evidence exists |
| Real-patient pilot authorization | **NO** | required gates remain open |

## Stop conditions

Real-patient enablement must stop if any of these is true:

- #318 restricted evidence/manifest is incomplete;
- #320 is not satisfied;
- any `--require-approved` audit exits non-zero;
- approved audit output lacks exact `audited_source_commit_sha`;
- residency/safety manifest SHA differs from `fd3e4a53543e515100b493acc63c99cc9e8464ce`;
- safety manifest fingerprint differs from `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- deployment topology differs from reviewed restricted evidence;
- explicit human release decision is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, production geography, independently verified reviewer credentials, real-device packaging approval, production deployment approval, or permission to process real patient data.

Pilot Readiness remains 4/9 = 44.4%. Retained MENA arithmetic remains 32/38 = 84.2% pending its separate reconciliation.

## Next exact action

Obtain the real restricted qualification/evidence references required by #318 and the deployment/legal evidence required by #320 for frozen candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce`. Then create the restricted manifests and execute the three exact-SHA approved audits. Until all three pass and an explicit human release decision exists, P5-6 remains `ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN` and release posture remains `NOT_RELEASE_AUTHORIZED`.
