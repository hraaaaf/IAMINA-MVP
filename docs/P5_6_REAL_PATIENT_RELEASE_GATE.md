# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL / CANDIDATE_REFROZEN / CURRENT_CANDIDATE_NOT_DEPLOYED  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **P5-1 prerequisite:** CLOSED / HUMAN_APPROVED / exact-main v8 retained  
> **Frozen candidate SHA:** `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`  
> **Safety corpus:** 59 exact cases / 10 technical parity tuples  
> **Safety fingerprint:** `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`  
> **Consent notice version:** `2026-09-12.1`  
> **Pilot Readiness arithmetic:** 4/9 = 44.4%  
> **Global roadmap:** 6/12 = 50.0%

## Goal

Permit a real-patient pilot only after one exact frozen release SHA has retained clinical-human, consent, deployment, processor, residency/transfer and explicit release-authorization evidence.

## Success

P5-6 closes only when, for frozen candidate `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`:

1. #318 has an approved restricted safety manifest covering the exact fingerprint, all 59 case IDs and all 10 parity tuples;
2. #320 has the actual deployed topology plus deployment/account-specific CNDP, processor and residency/transfer evidence;
3. safety and residency manifests carry `source_commit_sha = fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
4. all three exact-SHA fail-closed audits PASS with `--require-approved`;
5. retained outputs carry `audited_source_commit_sha = fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
6. an explicit human decision authorizes real-patient processing.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Candidate re-freeze — 2026-09-13

The prior deployed candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` proved the Vercel/Django/Neon runtime, but two release-gate defects were found afterward and fixed:

- PR #602: the local-only consent audit can now consume the already-defined restricted residency manifest and bind genuine CNDP health-processing evidence to the exact release SHA instead of remaining structurally impossible to approve;
- PR #603: native password recovery now requires an explicit provider-neutral SMTP production contract, uses non-silent delivery, preserves account-enumeration resistance, and no longer implies unproven mail delivery.

Forward candidate:

`fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`

Validation retained for this candidate:

- #602 exact-head CI #4186 / workflow `34771054574` — SUCCESS;
- #602 exact-head migration drift #3733 / workflow `34771054541` — SUCCESS;
- #603 exact-head CI #4189 / workflow `34771391814` — SUCCESS;
- #603 exact-head migration drift #3736 / workflow `34771391809` — SUCCESS;
- #603 merge `main@fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- post-merge CI #4190 / workflow `34773613905` — SUCCESS;
- post-merge migration drift #3737 / workflow `34773613814` — SUCCESS.

Clinical rebind proof:

- `backend/core/safety_corpora.py` blob is identical between `5b27a22…` and `fb42e4d…`: `bf046c298ee8e77591f5c5b1049b806a6255bfcf`;
- `backend/core/triage_classification.py` blob is identical between those candidates: `eba7a57967eeec1ba4b264c90ccab1a30e516b38`;
- therefore the retained corpus remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

This is a technical exact-corpus rebind only. It does not fabricate reviewer identity, qualification or a new human approval.

Documentation-only closeout commits may advance `main` without moving the frozen candidate. Any later runtime/code change requires another explicit re-freeze.

## Deployment state

### Proven predecessor deployment

The previous candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` remains technically proven in production:

- Vercel project `iamina-certified`, project id `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, READY, production, `cdg1`;
- dedicated Neon project `IAMINA`, project id `square-sun-82359137`;
- PostgreSQL 16 in `aws-eu-central-1`, branch `br-fragrant-frost-b1lbdfzs`;
- migrations current;
- `GET /api/v1/health` returned HTTP 200 with `{"status":"ok","db":"ok","cache":"unavailable"}`;
- runtime log recorded HTTP 200;
- cache absence is non-fatal under the existing health contract.

### Current forward candidate

`fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` is **not deployed**. No new Vercel deployment was performed during #602/#603 closeout.

The previous deployment proves the underlying Vercel/Neon path, but it does not count as exact-deployment evidence for the new candidate.

PR #603 also deliberately makes production startup fail closed until an explicit SMTP/reset contract is configured. Therefore the current candidate cannot honestly satisfy the full deployment topology gate until the actual mail processor and account-specific evidence are selected/configured and a separately authorized exact deployment is performed.

## #318 — Qualified clinical/safety evidence

Current state:

`OPEN / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / EXACT_CORPUS_REBOUND_TECHNICALLY / RESTRICTED_QUALIFICATION_REFERENCES_PENDING / BLOCKED_EXTERNAL_HUMAN`

Retained owner wording:

`issue-318:owner-attestation:professionnels-qualifies`

Still required:

- real opaque native-reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references required by the manifest contract;
- non-stale `reviewed_on` / `review_due_on`;
- approved coverage of all 59 exact case IDs;
- approved coverage of all 10 parity tuples;
- restricted safety manifest bound to `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` and the exact fingerprint;
- exact-SHA `audit_safety_corpus_review --require-approved` PASS.

No individual reviewer credential, registration, licence or diploma is inferred from repository history.

## #320 — CNDP, processor and residency gate

Current state:

`OPEN / BLOCKED_EXTERNAL_RELEASE / PREDECESSOR_DEPLOYMENT_PROVEN / CURRENT_CANDIDATE_NOT_DEPLOYED / SMTP_PROCESSOR_PENDING / COMPLIANCE_EVIDENCE_PENDING`

Still required:

- choose and configure the actual password-reset mail processor under the provider-neutral SMTP contract;
- account-specific processor/DPA/subprocessor/retention/deletion/privacy/security evidence for every enabled processor;
- actual exact-candidate topology with countries/regions after an explicitly authorized deployment;
- deployment-specific patient notice/consent approval evidence;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination where applicable;
- restricted residency manifest bound to `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation can define requirements but cannot substitute for account-specific approvals.

## Exact-SHA release audit contract

External AI egress remains local-only/runtime-denied for the release gate. Disabled network AI providers do not become release blockers, but global health-data authorization remains fail-closed and must come from the validated restricted residency manifest.

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b
```

Fail-closed behavior is authoritative: missing/malformed expected SHA, stale/partial manifests, source mismatch, fingerprint mismatch, incomplete case/parity coverage, missing topology/processor evidence, or missing approval evidence must fail.

## Decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-1 Morocco linguistic gate | CLOSED | #515 + retained v8 packet |
| P5-6 frozen candidate | REFROZEN | `fb42e4d…` + #602/#603 + post-merge CI/drift |
| Safety fingerprint/corpus | VERIFIED / unchanged | identical safety blobs + 59 cases / 10 tuples |
| Human safety review | ATTESTED_COMPLETE | #318 retained provenance |
| Restricted safety manifest | MISSING | #318 |
| Consent audit evidence plumbing | MERGED / GREEN | #602 |
| Password-reset production contract | MERGED / GREEN | #603 |
| Exact current-candidate deployment | MISSING | no deploy of `fb42e4d…` |
| Proven predecessor runtime/DB | HEALTHY | `5b27a22…`, Vercel `cdg1`, Neon `aws-eu-central-1` |
| Mail processor/account evidence | MISSING | #320 |
| CNDP/legal evidence | MISSING | #320 |
| Residency/transfer manifest | MISSING | #320 |
| Three approved exact-SHA audits | MISSING | blocked by restricted evidence |
| Real-patient pilot authorization | **NO** | human/external gates remain open |

## Stop conditions

Real-patient enablement must stop while any #318/#320 evidence is incomplete, if any approved audit fails, if any manifest/audit SHA differs from the frozen candidate, if the safety fingerprint differs, if exact deployment topology differs from reviewed evidence, or if explicit human release authorization is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, independently verified reviewer credentials, approved production geography for the current candidate, or permission to process real patient data.

## Next exact action

Complete the work that does not require deployment: update #318/#320 to the new frozen SHA and assemble the restricted evidence templates. The next unavoidable external decisions are the real #318 qualification references/review-due policy and #320 processor/CNDP/account evidence, including the actual password-reset mail processor. Only after those inputs exist can an exact deployment be separately authorized, topology frozen, manifests approved, the three exact-SHA audits run, and a human real-patient release decision be made.
