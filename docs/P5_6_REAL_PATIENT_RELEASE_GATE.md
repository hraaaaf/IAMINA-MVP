# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`  
> **Safety corpus:** 59 exact cases / 10 technical parity tuples  
> **Safety fingerprint:** `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`  
> **Consent notice version:** `2026-09-12.1`  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **Deployment:** Vercel Python runtime packaging is preview-proven in `cdg1`; the exact frozen candidate is not yet healthy/deployed for pilot use because dedicated PostgreSQL / `DATABASE_URL` is still absent.

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

The new frozen candidate is:

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

It does **not** modify the reviewed safety corpus or the consent-evidence contract. Therefore the retained safety corpus remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`, and consent notice version `2026-09-12.1` remains unchanged.

A documentation-only closeout may advance repository `main` without moving the frozen candidate. Any later runtime/code change requires another explicit re-freeze.

## Retained consent-evidence contract

The new candidate inherits the merged #591 behavior:

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

Retained provenance includes clinical-review, safety-owner, English-locale and parity attestations in #318 plus runtime cutover PR #585. Still required:

- restricted review evidence references required by the manifest, using `issue-318:owner-attestation:professionnels-qualifies` as the retained qualification reference where applicable;
- complete approved `case_reviews` for all 59 current case IDs;
- complete approved `parity_reviews` for all 10 tuples;
- restricted safety manifest bound to `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` and the exact fingerprint;
- exact-SHA `audit_safety_corpus_review --require-approved` PASS.

No individual reviewer credential, registration or diploma is claimed by the owner attestation.

## #320 — CNDP, processor and residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / PREVIEW_RUNTIME_PROVEN / DATABASE_TOPOLOGY_INCOMPLETE`.

The owner explicitly authorized Vercel deployment for evidence collection on 2026-09-13. This technical deployment authorization is **not** real-patient release authorization.

Verified Vercel topology evidence:

- project `iamina-certified`, project id `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- GitHub source repository `hraaaaf/IAMINA-MVP`;
- exact preview source `2fb0eabd8c2be4ada0a6377e257bb5f2a692db85` produced deployment `dpl_67XyJnauqp427XPrQhGtn9rAiKfE`;
- deployment state READY with one Python serverless function and configured runtime region `cdg1`;
- `backend/api/index.py` routes into Django WSGI and `/api/health/` reaches the Django function;
- `SECRET_KEY` is stored as sensitive Vercel configuration and its value was never logged;
- `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` are configured;
- `DATABASE_URL` is absent for preview and production, so runtime correctly fails closed with `DATABASE_URL is required on Vercel; SQLite fallback is forbidden`;
- connected Neon contains only the unrelated `tasdis` project; connected Supabase contains only the unrelated `AqarFinder` project; neither was reused for IAMINA.

The preview proves the corrected runtime packaging, but it is not the exact frozen merge SHA and is not a healthy pilot deployment. No successful production candidate is claimed.

Still required for candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`:

- provision a dedicated IAMINA PostgreSQL topology and bind `DATABASE_URL` without reusing another project's database;
- validate migrations/connectivity and obtain `/api/health/` success on the exact candidate;
- deploy/freeze the exact runtime/database/cache/email/export/provider topology and exact countries/regions;
- approved deployment-specific patient notice/consent;
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
| Backend deployment infrastructure | MERGED / PREVIEW-PROVEN | #597 + `dpl_67XyJnauqp427XPrQhGtn9rAiKfE` |
| Exact frozen candidate healthy deployment | **NO** | dedicated PostgreSQL / `DATABASE_URL` still missing |
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

Real-patient enablement must stop while any #318/#320 evidence is incomplete, while the exact frozen candidate lacks a healthy reviewed deployment, if any approved audit fails, if any manifest/audit SHA differs from the frozen candidate, if the safety fingerprint differs, if deployment topology differs from reviewed evidence, or if explicit human release authorization is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, independently verified reviewer credentials, healthy production deployment, approved production geography, or permission to process real patient data.

Canonical global progress remains 6/12 = 50.0%. P5 whole-lot progress remains 4/9 = 44.4%.

## Next exact action

Provision a **dedicated IAMINA PostgreSQL** topology, bind it to `iamina-certified` as `DATABASE_URL`, validate migrations/connectivity, then deploy and prove `/api/health/` on exact frozen candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`. After the actual topology and restricted evidence exist, bind both manifests to this SHA, run the three exact-SHA approved audits, then require an explicit human real-patient release decision.