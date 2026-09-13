# P5-6 Vercel runtime re-freeze — 2026-09-13

## Goal
Retain exact evidence for the Vercel Django runtime packaging correction merged by PR #597, without claiming database readiness or real-patient release.

## Verified
- PR #597 merged as `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`.
- Exact PR head: `edd4a3d86e4f773c527111b20349dfa6dd09dab5`.
- Exact-head CI #4169 / run `34749918504`: SUCCESS.
- Exact-head Django migration drift #3729 / run `34749918503`: SUCCESS.
- Exact post-merge CI run `34750040306`: SUCCESS after re-running the backend jobs cancelled only by a later documentation-only push.
- Post-merge Django migration drift #3730 / run `34750040338`: SUCCESS.
- PR changed exactly:
  - `backend/api/index.py`
  - `backend/core/tests/test_vercel_deployment_contract.py`
  - `backend/vercel.json`
- Exact preview source `2fb0eabd8c2be4ada0a6377e257bb5f2a692db85` produced Vercel deployment `dpl_67XyJnauqp427XPrQhGtn9rAiKfE` in region `cdg1` with one Python function.
- `/api/health/` reaches Django through `api/index.py`.
- Vercel runtime configuration has `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.
- `DATABASE_URL` is absent for preview and production; runtime fails closed with `DATABASE_URL is required on Vercel; SQLite fallback is forbidden`.
- No IAMINA database exists in connected Neon or Supabase accounts. Existing databases belong to other projects and were not reused.

## Candidate state
The prior candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` is retired as the forward candidate because its Vercel packaging was incompatible with the actual runtime.

The forward runtime candidate is now re-frozen at:

`5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`

Documentation-only commits after this merge do not move the frozen runtime candidate.

## Qualification wording
The owner-selected qualification wording retained in #318 is **« professionnels qualifiés »**, machine reference `issue-318:owner-attestation:professionnels-qualifies`. It is an owner attestation, not independent credential verification.

## Release posture
`NOT_RELEASE_AUTHORIZED`.

## Next exact
Provision a dedicated IAMINA PostgreSQL topology, bind `DATABASE_URL`, validate migrations/connectivity and prove `/api/health/` on exact frozen candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`.

Database-specific processor/residency evidence, restricted manifests, exact-SHA approved audits, and explicit human real-patient release authorization remain open gates.
