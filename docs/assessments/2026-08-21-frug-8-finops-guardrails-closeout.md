# FRUG-8 — Persistent FinOps guardrails closeout

Date: 2026-08-21  
Tracking: #431 / parent roadmap #422  
Engineering merge: PR #467 → `main@c99a91cadb0c465d1f266088d5df4a78be43ce19`

## Status

**CLOSED — engineering controls certified with exact-tree post-merge equivalence.**

The GitHub connector does not expose push-triggered runs for merge SHAs. Instead of inferring their result, closure uses content-equivalence proof: the final closeout content is certified on a PR branch whose Git tree is compared against the final squash-merged `main` tree before crediting the lot. No unobserved push-run status is asserted.

No production FinOps amount, provider approval, real-patient provider egress, CNDP/legal approval or Vercel deployment is asserted here.

## Goal

Turn the existing fail-closed budget contracts into persistent, atomic runtime protection against billing loops and quota explosions while preserving deterministic/static safety paths.

## Delivered control matrix

| # | #431 target control | Delivered evidence |
|---|---|---|
| 1 | Persistent atomic reserve/settle/cancel ledger | FRUG-8A / PR #462, DB-backed account + reservation rows, durable idempotency, PostgreSQL row locking |
| 2 | Provider + workload + global ceilings | FRUG-8B / PR #463, atomic hierarchical budget bundle and shared global serialization point |
| 3 | Soft alert + hard stop before paid egress | FRUG-8B + FRUG-8D2, soft-threshold signal and runtime hard authorization before provider execution |
| 4 | Deterministic/static paths remain available | FRUG-8D2 / PR #466, local fallback remains outside paid FinOps enforcement |
| 5 | Retry ceilings + idempotency | FRUG-8C + FRUG-8D2, persistent operation attempts and HMAC operation identity |
| 6 | Per-user abuse throttle independent of emergency routing | FRUG-8E / PR #467, persistent fixed-window HMAC throttle only on external paid text completion |
| 7 | Circuit breaker for 429/5xx/timeouts | FRUG-8C / PR #464, persistent provider circuit state + attempt leases |
| 8 | Usage anomaly detection | FRUG-8E, aggregate token/OCR/vision/STT/TTS/media-byte dimensions with pre-billing anomaly alerts |
| 9 | Controlled pricing expiry fails closed | FRUG-8D2, paid runtime resolves current controlled pricing before provider attempt |
| 10 | Audit-safe reports/alerts contain no patient payload | FRUG-8E, allowlisted aggregate metrics and reconciliation; tests inject rogue PHI-like fields and prove non-propagation |

## Final FRUG-8E exact-head proof

Certified head before merge: `a93c261f7ccd78462097994d63f2b103b0d2c32c`.

- CI #3332 / run `32530092852` — success.
- Django migration drift #3145 / run `32530092907` — success.
- PostgreSQL forward migration applies `core.0015_ai_user_throttle` — success.
- PostgreSQL full suite: **1744 passed, 3 xfailed, 52 subtests passed**.
- Ruff — success.
- Import-linter architecture boundaries — success.
- LLM gateway anti-bypass — success.
- AI-egress authorization anti-bypass — success.
- Bandit/SAST — success.
- OpenAPI current — success.
- Secret hygiene — success.
- Frontend analyze/tests — success.
- Final concurrency test proves 3 simultaneous requests against ceiling 2 result in exactly 2 allowed and 1 blocked.
- The earlier FRUG-8E worker-connection teardown warning was removed before this final head; remaining warnings are unrelated Ninja deprecations.

## Independent reviews

- Database & Migration Reviewer — **PASS**, PR review `4997705098`.
- Security Auditor — **PASS**, PR review `4997706122`.
- Release Certifier — **CERTIFIED_WITH_NON_BLOCKING_FINDINGS**, PR review `4997708136`.
- Open inline review threads at certification: **0**.

## Merge proof

PR #467 was marked ready and squash-merged with expected-head lock on `a93c261f7ccd78462097994d63f2b103b0d2c32c`.

- Merge SHA: `c99a91cadb0c465d1f266088d5df4a78be43ce19`.
- Merged tree SHA: `42219bd4c2f1553bd26af3b9026163ff976dd94d`.
- Exact tested head tree SHA: `42219bd4c2f1553bd26af3b9026163ff976dd94d`.
- Engineering tree identity: exact.

Closeout PR #468 added only this assessment document:

- Tested closeout head: `52fc4228541867f7198f5ca61210d2cc9681a9f1`.
- CI #3334 / run `32530732211` — success.
- Django migration drift #3147 / run `32530732259` — success.
- Tested closeout tree: `076525b477380bb90fdaa27d9d6b533bf58ef9ae`.
- Merge/main after #468: `40cbcb4e008cf02f6bc46d83947ef2f214065d47`.
- Main tree after #468: `076525b477380bb90fdaa27d9d6b533bf58ef9ae`.
- Tree identity: exact.

## Privacy and safety boundaries retained

- Per-user throttle persistence stores only domain-separated HMAC-SHA256 subjects, never raw patient IDs.
- Throttle and FinOps warnings omit patient identifiers, HMAC subjects, prompts, document/media content and object keys.
- Paid runtime enforcement remains downstream of the sanctioned patient/purpose/modality egress and processor-policy boundary.
- Local deterministic/static fallback is not converted into a paid provider cascade.
- No new clinical authority resides in FinOps/provider code.

## Residuals outside FRUG-8 engineering scope

- Production budget/throttle values remain deployment governance inputs, not repository defaults.
- External provider patient-data approval remains subject to processor/CNDP/legal/residency gates.
- Real billing data is still required by FRUG-0 for final cost truth.
- Scale envelopes belong to FRUG-9.
- Push-triggered post-merge run IDs remain unobservable through the current connector; closure relies on exact-tree equality plus successful CI/drift on that exact tree, not on an inferred run state.

## Governance recovery

A docs-only closeout update was accidentally written directly to `main` after PR #468. No runtime code or configuration changed. The follow-up certification PR exists specifically to restore the normal governed path: branch → CI/drift → Release review → expected-head squash merge → exact-tree equality check. No history rewrite is used.

## Roadmap arithmetic

This FRUG lane remains parallel to the canonical MENA numerator. Nothing in this closeout changes the `32/38` MENA critical-path arithmetic in `docs/ROADMAP.md`.

FRUG-8 is credited only after the follow-up certification PR passes and final main tree equality is proven. FRUG-7 (#430) is evaluated separately.