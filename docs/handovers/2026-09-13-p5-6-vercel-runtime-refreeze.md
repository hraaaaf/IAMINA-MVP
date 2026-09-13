# P5-6 Vercel runtime re-freeze — 2026-09-13

## Goal
Retain exact evidence for the corrected Vercel Django runtime and dedicated IAMINA PostgreSQL deployment of frozen candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, without claiming real-patient release.

## Verified candidate proof
- PR #597 merged as `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`.
- Exact PR head: `edd4a3d86e4f773c527111b20349dfa6dd09dab5`.
- Exact-head CI #4169 / run `34749918504`: SUCCESS.
- Exact-head Django migration drift #3729 / run `34749918503`: SUCCESS.
- Exact post-merge CI run `34750040306`: SUCCESS after re-running backend jobs cancelled only by a later documentation-only push.
- Post-merge Django migration drift #3730 / run `34750040338`: SUCCESS.
- PR changed exactly:
  - `backend/api/index.py`
  - `backend/core/tests/test_vercel_deployment_contract.py`
  - `backend/vercel.json`

## Dedicated database proof
- Neon project: `IAMINA` / `square-sun-82359137`.
- PostgreSQL: 16.
- Region: `aws-eu-central-1`.
- Default branch: `production` / `br-fragrant-frost-b1lbdfzs`.
- GitHub Actions run `34752706286`, successful rerun job `103717805309`.
- Django migrations applied successfully.
- `python manage.py migrate --check` clean.
- `db_connectivity=ok`.
- `django_migrations=applied_and_current`.
- Neon table inventory confirms the expected Django/core/diabetes tables now exist.
- No AqarFinder/Supabase database and no unrelated Neon database was reused.

## Exact Vercel production proof
- Vercel project: `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`.
- Deployment: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`.
- Source SHA in Vercel metadata: `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`.
- Target: `production`.
- State: `READY`.
- Runtime region: `cdg1`.
- Python serverless function: present.
- Stable alias `iamina-certified.vercel.app` resolves to this deployment.
- `GET https://iamina-certified.vercel.app/api/v1/health` returns HTTP 200:
  - `status=ok`
  - `db=ok`
  - `cache=unavailable`
- Runtime log records the health request as HTTP 200.
- `cache=unavailable` is non-fatal under the current health contract; no Redis readiness claim is made.

## Candidate state
The prior candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` remains retired as the forward candidate because its old Vercel packaging was incompatible with the actual runtime.

The forward runtime candidate remains frozen at:

`5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`

Documentation-only commits after this merge do not move the frozen runtime candidate.

## Qualification wording
The owner-selected qualification wording retained in #318 is **« professionnels qualifiés »**, machine reference `issue-318:owner-attestation:professionnels-qualifies`. It is an owner attestation, not independent credential verification.

## Release posture
`NOT_RELEASE_AUTHORIZED`.

Technical deployment and database readiness are now proven. They do not establish CNDP, processor, foreign-transfer, residency or real-patient approval.

## Next exact
Build the restricted P5-6 evidence packet against the proven deployment:

1. #318: complete approved 59-case / 10-parity safety evidence and restricted safety manifest;
2. #320: freeze actual runtime/database/cache/email/export/provider topology and collect account/deployment-specific CNDP, processor, residency/transfer evidence;
3. bind both manifests to `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
4. run the three exact-SHA `--require-approved` audits;
5. require explicit human real-patient release authorization.

Until all five are proven, P5-6 remains open.