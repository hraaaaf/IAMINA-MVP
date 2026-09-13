# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`  
> **Safety corpus:** 59 exact cases / 10 technical parity tuples  
> **Safety fingerprint:** `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`  
> **Consent notice version:** `2026-09-12.1`  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **Deployment:** exact frozen candidate is deployed successfully to Vercel production in `cdg1`, backed by dedicated Neon PostgreSQL 16 in `aws-eu-central-1`; `/api/v1/health` returns HTTP 200 with `db=ok`. Real-patient release remains blocked on restricted safety/compliance evidence and explicit human release authorization.

## Goal

Permit a real-patient pilot only after one exact frozen release SHA is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for frozen candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`:

1. #318 has a valid restricted safety-review manifest covering the exact fingerprint, all 59 cases and all 10 parity tuples;
2. #320 has actual deployment topology plus deployment/account-specific CNDP, processor and residency/transfer evidence;
3. the safety and residency restricted manifests carry `source_commit_sha = 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
4. all three fail-closed audits PASS with `--require-approved --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
5. retained approved outputs carry `audited_source_commit_sha = 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
6. an explicit human release decision authorizes real-patient processing.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Deliberate candidate re-freeze after Vercel runtime correction

The former candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` remains retained as the PR #590 backend-infrastructure proof, but it is superseded as the forward P5-6 candidate because an exact Vercel deployment attempt exposed an incompatible function-path contract.

The frozen candidate is:

`5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`

Re-freeze proof:

- old exact candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` produced Vercel deployment `dpl_5AcyTUotrjRi5pt7A9zv92dxQsEX`, which failed with `unused_function` for the former `amina/wsgi.py` function glob;
- PR #597 `fix(infra): route Django through explicit Vercel Python function`;
- exact PR head `edd4a3d86e4f773c527111b20349dfa6dd09dab5`;
- exact-head CI #4169 / workflow `34749918504` — SUCCESS;
- exact-head Django migration drift #3729 / workflow `34749918503` — SUCCESS;
- merge `main@5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, tree `5b07093b3df9b0d337104e0e82133feb18341d80`;
- exact post-merge CI workflow `34750040306` — SUCCESS after re-running the jobs cancelled only by a later documentation-only push;
- post-merge Django migration drift #3730 / workflow `34750040338` — SUCCESS.

PR #597 changes exactly three files: `backend/api/index.py`, `backend/vercel.json`, and `backend/core/tests/test_vercel_deployment_contract.py`.

It does **not** modify the reviewed safety corpus or the consent-evidence contract. The retained safety corpus remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`, and consent notice version `2026-09-12.1` remains unchanged.

Documentation-only closeout commits may advance repository `main` without moving the frozen candidate. Any later runtime/code change requires another explicit re-freeze.

## Retained consent-evidence contract

The candidate inherits the merged #591 behavior:

- exact consent notice version/hash/locale evidence;
- legacy timestamp-only consent invalidation and re-consent;
- server acceptance receipts;
- withdrawal clearing active proof and revoking granular media grants;
- central outbound-AI egress verification against current notice proof;
- consent epoch separation for media grants;
- Flutter fail-closed when server acceptance fails;
- local UI gate requiring Drift consent timestamp plus current Secure Storage evidence;
- local-only release scope retaining the global CNDP health-processing blocker.

## Retained qualified-human safety review

The project-owner attestation records completion of the retained safety review and adjudication of challenged Darija rows. The enabled corpus remains 59 exact cases and 10 technical `(locale, channel, input_form)` parity tuples with fingerprint:

`823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`

The owner-selected qualification wording is **« professionnels qualifiés »**, with machine-readable reference:

`issue-318:owner-attestation:professionnels-qualifies`

This is an owner attestation. GitHub does not independently verify identity, diploma, registration, licence or professional credentials. No such detail is invented or required by this retained wording.

#318 remains open because the restricted exact-corpus manifest and complete approved case/parity evidence are not yet retained.

## #318 — Qualified clinical/safety evidence

Current state: `OPEN / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / MANIFEST_PENDING / CANDIDATE_REFROZEN`.

Still required:

- restricted review evidence references required by the manifest, using `issue-318:owner-attestation:professionnels-qualifies` where applicable;
- complete approved `case_reviews` for all 59 current case IDs;
- complete approved `parity_reviews` for all 10 tuples;
- restricted safety manifest bound to `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` and the exact fingerprint;
- exact-SHA `audit_safety_corpus_review --require-approved` PASS.

No individual reviewer credential, registration or diploma is claimed by the owner attestation.

## #320 — CNDP, processor and residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / EXACT_PRODUCTION_HEALTHY / COMPLIANCE_EVIDENCE_PENDING`.

The owner explicitly authorized Vercel deployment for evidence collection on 2026-09-13. This technical deployment authorization is **not** real-patient release authorization.

### Exact deployed topology now verified

- frozen source SHA: `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- GitHub Actions production run `34752706286`, successful rerun job `103717805309`;
- dedicated Neon project `IAMINA`, project id `square-sun-82359137`;
- Neon PostgreSQL 16, region `aws-eu-central-1`;
- Neon default branch `production`, branch id `br-fragrant-frost-b1lbdfzs`;
- Django migrations applied successfully, `migrate --check` clean, `db_connectivity=ok`, `django_migrations=applied_and_current`;
- Vercel project `iamina-certified`, project id `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- exact production deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- deployment state `READY`, target `production`, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolves to that exact deployment;
- Vercel deployment metadata reports exact source SHA `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- `GET https://iamina-certified.vercel.app/api/v1/health` returns HTTP 200 with `{"status":"ok","db":"ok","cache":"unavailable"}`;
- runtime log for the health request is HTTP 200;
- cache unavailability is non-fatal under the existing health contract and currently falls back to DB behavior;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

The database/runtime portion of the technical deployment gate is therefore proven. This does not prove legal/CNDP or processor approval.

### Still required for real-patient release

- freeze the complete actual runtime/database/cache/email/export/provider topology with exact countries/regions in restricted evidence;
- approved deployment-specific patient notice/consent evidence;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for each actual external destination, where applicable;
- account-specific processor/DPA/subprocessor/retention/deletion/no-training/privacy/security evidence;
- restricted residency manifest bound to the frozen SHA;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation may define requirements but is not account-specific approval evidence.

## Exact-SHA release audit contract

```bash
python manage.py audit_pilot_consent_governance \
  --require-approved \
  --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6
```

Fail-closed behavior remains authoritative: missing expected SHA, malformed SHA, stale/partial manifests, source-SHA mismatch, safety fingerprint mismatch, incomplete case/parity coverage, missing deployment evidence, or missing approval evidence must fail.

## Decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-1 Morocco linguistic gate | CLOSED | #515 + retained v8 packet |
| P5-6 frozen candidate | REFROZEN | `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` + #597 exact-head/post-merge CI/drift |
| Consent-evidence contract | MERGED / GREEN | #591, inherited unchanged |
| Backend deployment infrastructure | **EXACT_PRODUCTION_HEALTHY** | `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, `cdg1`, health 200 |
| Dedicated PostgreSQL | **READY / MIGRATED** | Neon `square-sun-82359137`, PG16, `aws-eu-central-1`, migrations current |
| Safety fingerprint/corpus | VERIFIED / unchanged | fingerprint + 59 cases / 10 tuples |
| Human safety review | ATTESTED_COMPLETE | #318 retained provenance |
| Qualification wording | OWNER_ATTESTATION_RETAINED | `professionnels qualifiés` / #318 |
| Restricted safety manifest | MISSING | #318 |
| Deployment-specific CNDP/legal evidence | MISSING | #320 |
| Processor/account-specific approvals | MISSING | #320 |
| Residency/transfer manifest | MISSING | #320 |
| Three approved exact-SHA audit outputs | MISSING | cannot pass before restricted evidence exists |
| Real-patient pilot authorization | **NO** | external/human gates remain open |

## Stop conditions

Real-patient enablement must stop while any #318/#320 evidence is incomplete, if any approved audit fails, if any manifest/audit SHA differs from the frozen candidate, if the safety fingerprint differs, if deployment topology differs from reviewed evidence, or if explicit human release authorization is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, independently verified reviewer credentials, approved production geography for health-data processing, or permission to process real patient data.

Canonical global progress remains 6/12 = 50.0%. P5 whole-lot progress remains 4/9 = 44.4%.

## Next exact action

Build the restricted P5-6 evidence packet against the now-proven exact deployment: complete #318's 59-case/10-parity safety manifest and #320's deployment-specific residency/processor/CNDP evidence for the actual Vercel `cdg1` + Neon `aws-eu-central-1` topology. Then bind both manifests to `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, run the three exact-SHA `--require-approved` audits, and require an explicit human real-patient release decision.