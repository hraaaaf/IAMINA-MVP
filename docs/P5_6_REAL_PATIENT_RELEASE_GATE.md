# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`  
> **Safety corpus:** 59 exact cases / 10 technical parity tuples  
> **Safety fingerprint:** `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`  
> **Consent notice version:** `2026-09-12.1`  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **Deployment:** backend infrastructure is prepared, but no P5-6 candidate deployment is authorized or claimed.

## Goal

Permit a real-patient pilot only after one exact frozen release SHA is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for frozen candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`:

1. #318 has a valid restricted safety-review manifest covering the exact fingerprint, all 59 cases and all 10 parity tuples;
2. #320 has actual deployment topology plus deployment/account-specific CNDP, processor and residency/transfer evidence;
3. the safety and residency restricted manifests carry `source_commit_sha = 52c0238fede74a1ba85fd3df32b1e89268bbe8f7`;
4. all three fail-closed audits PASS with `--require-approved --expected-source-commit-sha 52c0238fede74a1ba85fd3df32b1e89268bbe8f7`;
5. retained approved outputs carry `audited_source_commit_sha = 52c0238fede74a1ba85fd3df32b1e89268bbe8f7`;
6. an explicit human release decision authorizes real-patient processing.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Deliberate candidate re-freeze after backend infrastructure merge

The former candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce` remains retained as the consent-evidence runtime proof from PR #591, but it is superseded as the forward P5-6 candidate because PR #590 changed release/deployment runtime infrastructure.

The new frozen candidate is:

`52c0238fede74a1ba85fd3df32b1e89268bbe8f7`

Re-freeze proof:

- PR #590 `infra: prepare Vercel backend infrastructure`;
- exact PR head `2f5aa97dac9105f865b4cef10f914c58020e26c9`;
- exact-head CI #4147 / workflow `34709348736` — SUCCESS;
- exact-head Django migration drift #3721 / workflow `34709348741` — SUCCESS;
- signed merge `main@52c0238fede74a1ba85fd3df32b1e89268bbe8f7`;
- merge tree `3db5d6368b07eaa80f810f193da2ce5268c425d8`;
- post-merge CI #4154 / workflow `34723119692` — SUCCESS;
- post-merge Django migration drift #3723 / workflow `34723119717` — SUCCESS;
- post-merge UI browser screenshot #526, P5-5 rehearsal #102, UI missing-routes #59 and UI geometry #523 — SUCCESS.

PR #590 changed exactly six files: `backend/Dockerfile`, `backend/config/settings/base.py`, `backend/config/wsgi.py`, `backend/core/tests/test_production_deployment_contract.py`, `docs/P5_6_PRODUCTION_DEPLOYMENT_PREPARATION.md`, and `vercel-backend.json`.

It did **not** modify the reviewed safety corpus or the consent-evidence contract. Therefore the retained safety corpus remains 59 exact cases / 10 parity tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`, and consent notice version `2026-09-12.1` remains unchanged.

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

The project-owner attestation records completion of the 2026-09-12 clinical review and adjudication of challenged Darija rows. The enabled corpus remains 59 exact cases and 10 technical `(locale, channel, input_form)` parity tuples with fingerprint:

`823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`

GitHub does not independently verify reviewer identity or qualifications. Existing issue comments are retained provenance, not substitutes for missing `qualification_reference` evidence.

#318 therefore remains open.

## #318 — Qualified clinical/safety evidence

Current state: `OPEN / REVIEW_ATTESTED / RESTRICTED_QUALIFICATION_REFERENCES_PENDING / CANDIDATE_REFROZEN`.

Retained provenance includes clinical-review, safety-owner, English-locale and parity attestations in #318 plus runtime cutover PR #585. Still required:

- real opaque native-reviewer references for required locales `fr`, `ar`, `en`, `ar-MA` where not already represented in restricted evidence;
- real qualification references for every required locale review;
- complete approved `case_reviews` for all 59 current case IDs;
- complete approved `parity_reviews` for all 10 tuples;
- restricted safety manifest bound to `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` and the exact fingerprint;
- exact-SHA `audit_safety_corpus_review --require-approved` PASS.

No reviewer credential or qualification reference may be invented from an attestation.

## #320 — CNDP, processor and Morocco residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / CANDIDATE_NOT_DEPLOYED / TOPOLOGY_NOT_FROZEN`.

PR #590 prepares a separate Django backend target intended as `iamina-certified` in Vercel region `cdg1`; it does not deploy it.

Read-only Vercel verification found the currently active `iamina-review` production deployment is an older frontend-only offline demo built from `7ca1f9cd6ba65ce58a351a2befceddbe5cb76f38` in `iad1`, with no `API_BASE_URL`; `/api/health` resolves to the Flutter application rather than a Django health response. It is not the P5-6 candidate and cannot satisfy #320.

Still required for candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`:

- explicit owner authorization before any Vercel deployment;
- actual deployed runtime/database/cache/email/export/provider topology and exact countries/regions;
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
  --expected-source-commit-sha 52c0238fede74a1ba85fd3df32b1e89268bbe8f7

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha 52c0238fede74a1ba85fd3df32b1e89268bbe8f7

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha 52c0238fede74a1ba85fd3df32b1e89268bbe8f7
```

Fail-closed behavior remains authoritative: missing expected SHA, malformed SHA, stale/partial manifests, source-SHA mismatch, safety fingerprint mismatch, incomplete case/parity coverage, or missing approval evidence must fail.

## Decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-1 Morocco linguistic gate | CLOSED | #515 + retained v8 packet |
| P5-6 frozen candidate | REFROZEN | `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` + #590 CI/drift evidence |
| Consent-evidence contract | MERGED / GREEN | #591, inherited unchanged |
| Backend deployment infrastructure | PREPARED / GREEN | #590 |
| Candidate deployed | **NO** | explicit deployment gate remains |
| Safety fingerprint/corpus | VERIFIED / unchanged | fingerprint + 59 cases / 10 tuples |
| Human clinical review | ATTESTED_COMPLETE | #318 retained provenance |
| Restricted qualification references | MISSING | #318 |
| Deployment-specific CNDP/legal evidence | MISSING | #320 |
| Processor/account-specific approvals | MISSING | #320 |
| Residency/transfer manifest | MISSING | #320 |
| Three approved exact-SHA audit outputs | MISSING | cannot pass before restricted evidence exists |
| Real-patient pilot authorization | **NO** | external/human gates remain open |

## Stop conditions

Real-patient enablement must stop while any #318/#320 evidence is incomplete, while the candidate is not explicitly authorized/deployed for evidence collection, if any approved audit fails, if any manifest/audit SHA differs from the frozen candidate, if the safety fingerprint differs, if deployment topology differs from reviewed evidence, or if explicit human release authorization is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, independently verified reviewer credentials, production deployment, production geography, or permission to process real patient data.

Canonical global progress remains 6/12 = 50.0%. P5 whole-lot progress remains 4/9 = 44.4%.

## Next exact action

The repository side is prepared and re-frozen. The next executable release step is a **human gate**: explicit authorization to deploy the exact candidate backend/topology. In parallel, #318 still requires real restricted reviewer qualification references. After actual deployment topology and restricted evidence exist, bind both manifests to `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`, run the three exact-SHA approved audits, then require an explicit human real-patient release decision.
