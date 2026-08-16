# CGM-GW-V1 — Closeout evidence

## Scope

Read-only vendor-neutral CGM ingestion boundary for Dexcom and Libre through an external Nightscout-compatible bridge.

## Delivered runtime

- `backend/integrations/cgm/contracts.py`: `CGMProvider`, `CGMReading`, `CGMSource`, `ProviderHealth`.
- `backend/integrations/cgm/nightscout.py`: Nightscout-compatible read adapter.
- Explicit configured provenance for Dexcom or Libre; no inference from device text.
- HTTPS required for non-loopback endpoints; exact loopback HTTP only.
- Embedded URL credentials rejected; one authentication mechanism at a time.
- Timezone-aware cursors required.
- Malformed provider payloads fail closed or invalid readings are discarded.
- Provider failure detail is collapsed and not exposed.
- External Nightscout/nightscout-connect AGPL code remains outside IAMINA.

## Safety / authority ceiling

CGM-GW-V1 is transport and normalization only. It adds no diagnosis, urgency, threshold, prediction, treatment, dose, treatment optimization/change, persistence into patient clinical tables, patient endpoint/UI, or generative clinical authority.

## Review and validation

PR #276 exact head before merge: `706225a49a7c8bfeb28ac0fd25f1fd7894878270`.

- Security/Privacy Reviewer: PASS after URL-validation remediation.
- Clinical Safety Reviewer: PASS.
- Release Certifier pre-merge: GO.
- Exact-head CI #2568: SUCCESS, including ruff, import-linter, both AI anti-bypass checks, Bandit, OpenAPI, pytest, PostgreSQL full suite, frontend analyze/tests and secret hygiene.
- Exact-head migration drift #2380: SUCCESS.
- PR #276 squash merge: `f8a4ce7f09147818c9ebc7da6a5cf8bed76d9fc6`.
- `main` verified at the merge SHA.

## Post-merge closure

Post-merge CI #2569 and migration drift #2381 are required before final closure. At creation of this evidence file, drift #2381 is green while CI #2569 is still running.

Canonical `docs/ROADMAP.md` and `docs/architecture/ARCHITECTURE.md` must be synchronized to the final post-merge truth before CGM-GW-V1 is declared 100% closed.
