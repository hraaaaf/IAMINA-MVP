# Gate A — Secure Core certification

**Date:** 2026-08-14  
**Baseline:** `main` at `0c256073cecc2d3eb489c402b93cba668faa4409`  
**Decision:** **PASS at 9.0/10** for the Gate A engineering threshold.  
**Important:** this certification does **not** clear the separate real-patient pilot security/compliance gate. Issue #30 remains an explicit blocker there.

## Scoring contract

Gate A is scored on ten equally weighted, independently checkable secure-core dimensions. A point is awarded only when the repository contains an implemented control and current evidence supports it. Known residual risk is scored as failure rather than diluted into a partial point.

| # | Dimension | Result | Evidence |
|---|---|---|---|
| 1 | API write/session safety | PASS | P0-A: cookie/session writes retain CSRF; diabetes routes are unit-guarded; unexpected normalization failures fail closed. |
| 2 | Deterministic clinical authority | PASS | Deterministic triage remains authoritative; diagnosis, dosing, prescription and treatment optimization/change remain outside companion authority. |
| 3 | High-risk request refusal parity | PASS | Pilot gate records deterministic refusal of insulin-dose/treatment requests across sync chat, SSE and post-STT voice, with the same no-prescription ceiling on doctor-facing/summary output. |
| 4 | Emergency truthfulness | PASS | `SELF_CARE_ONLY` operating model is explicit; the product does not claim automatic human monitoring and emergency handling remains deterministic/upstream. |
| 5 | AI/data-egress authorization | PASS | P0-MENA-1 centralizes patient + purpose + modality authorization and checks server-side consent at real egress time. |
| 6 | Data minimization / DLP / raw-media consent | PASS | Payload allowlists/minimization, semantic DLP, granular raw-media consent and processor-policy boundaries are implemented; CI includes AI-egress anti-bypass. |
| 7 | Sovereign authentication core | PASS | P0-MENA-3 is merged: Django-owned registration/login/logout, signed expiring IAMINA bearer tokens, global revocation and guarded Firebase migration/reconciliation. |
| 8 | Data-integrity / database safety | PASS | PostgreSQL is the analytical source-of-truth path; current main CI passes the full PostgreSQL suite and migration validation; dedicated migration-drift is green. |
| 9 | Current-tree code/secret hygiene | PASS | Current main CI passes ruff, import-linter, LLM gateway anti-bypass, AI-egress anti-bypass, Bandit SAST, tests and tracked-file secret hygiene. |
| 10 | Reachable Git-history secret hygiene | **FAIL** | Issue #30 is closed `not planned`, explicitly **not remediated**. Historical `.claude/settings.local.json` material remains reachable and the full-history scanner must remain fail-closed. |

**Score: 9 PASS / 10 = 9.0/10.**

## Current proof

On baseline `0c256073...`:

- CI push run **#2126** (`31759107722`) completed **SUCCESS**.
- `Frontend — analyze + tests`: PASS.
- `Backend — PostgreSQL source-of-truth`: PASS, including migration validation and full PostgreSQL test suite.
- `Backend — ruff + pytest`: PASS, including architecture boundaries, LLM gateway anti-bypass, AI egress authorization anti-bypass, Bandit SAST, OpenAPI freshness and tests.
- `Secret hygiene — tracked files`: PASS.
- Django migration drift run **#1938** (`31759107720`) completed **SUCCESS**.

## Residual risk and hard boundary

The one failed dimension is deliberately not papered over. The historical local-agent settings material remains reachable in Git history. Existing governance requires either the documented full-history remediation/verification sequence or an explicit governance supersession before the real-patient pilot go/no-go.

This Gate A certification therefore means:

- the **secure runtime/core engineering baseline** meets the requested 9/10 threshold;
- the repository must **not** be represented as having a fully clean reachable history;
- this document does **not** authorize an irreversible history rewrite;
- this document does **not** waive issue #30 or any restricted CNDP/privacy/deployment/native-language approval;
- real-patient pilot authorization remains a separate later gate.

## Closeout rule

Gate A may be reopened only if a secure-core regression is found, an authority boundary is widened, authentication/egress architecture materially changes, or the scoring evidence becomes stale due to a relevant runtime change.
