# P5-6 — Backend infrastructure re-freeze closeout

## Goal

Explicitly move the P5-6 frozen release candidate after PR #590 changed release/deployment runtime infrastructure, without claiming a deployment or weakening the external release gates.

## Success

This closeout is successful only if the exact PR #590 head and post-merge runtime are green, the candidate is rebound to the signed merge SHA, unchanged safety/consent contracts are retained, canonical trackers bind future manifests/audits to the new SHA, and no deployment/legal/real-patient claim is made.

## Verified evidence

- PR #590: `infra: prepare Vercel backend infrastructure`;
- exact PR head: `2f5aa97dac9105f865b4cef10f914c58020e26c9`;
- exact-head CI #4147 / workflow `34709348736`: SUCCESS;
- exact-head Django migration drift #3721 / workflow `34709348741`: SUCCESS;
- signed merge: `main@52c0238fede74a1ba85fd3df32b1e89268bbe8f7`;
- merge tree: `3db5d6368b07eaa80f810f193da2ce5268c425d8`;
- post-merge CI #4154 / workflow `34723119692`: SUCCESS;
- post-merge migration drift #3723 / workflow `34723119717`: SUCCESS;
- post-merge UI browser screenshot #526, P5-5 rehearsal #102, UI missing-routes #59 and UI geometry #523: SUCCESS.

PR #590 changed exactly six files: `backend/Dockerfile`, `backend/config/settings/base.py`, `backend/config/wsgi.py`, `backend/core/tests/test_production_deployment_contract.py`, `docs/P5_6_PRODUCTION_DEPLOYMENT_PREPARATION.md`, and `vercel-backend.json`.

It did not modify the safety corpus or consent-evidence contract. Safety therefore remains 59 exact cases / 10 parity tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`; consent notice version remains `2026-09-12.1`.

## Deployment boundary

PR #590 prepares a separate Django backend target (`iamina-certified`) using Vercel region `cdg1`; it does not deploy it.

Read-only account verification found the active `iamina-review` production deployment is still an older frontend-only offline demo built from `7ca1f9cd6ba65ce58a351a2befceddbe5cb76f38` in `iad1`, with no `API_BASE_URL` and no Django health response. It is not the frozen candidate and is not valid deployment-specific evidence for #320.

No deployment was performed by this closeout.

## Re-freeze decision

Frozen P5-6 candidate becomes `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`.

Former candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce` remains retained as historical consent-evidence proof but is superseded as the forward release candidate because #590 changed release runtime/deployment infrastructure.

Documentation-only commits after this closeout do not silently move the candidate.

## Remaining gates

#318 remains blocked on real restricted reviewer/qualification references and a complete safety-review manifest bound to the new candidate and unchanged fingerprint.

#320 remains blocked on explicit deployment authorization, actual deployed topology, deployment/account-specific CNDP and processor evidence, transfer basis where applicable, and a restricted residency manifest bound to the new candidate.

After those evidence sets exist, all three `--require-approved` audits must pass against `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`, followed by an explicit human real-patient release decision.

## Non-claims

No legal advice, CNDP authorization, independently verified reviewer qualification, processor approval, production deployment, production geography or permission to process real patient data is claimed.

Canonical global progress remains 6/12 = 50.0%. P5 whole-lot progress remains 4/9 = 44.4%. Release posture remains `NOT_RELEASE_AUTHORIZED`.
