# FRUG-5 — Evidence status receipt

Status: OPEN — internal optimization evidence complete; live/external proof remains.

## Goal

Use GPT-OSS for language rather than as a database or clinical engine, while reducing prompt tokens and avoidable LLM calls without weakening deterministic safety authority.

## Verified evidence

- Runtime Companion history budget: 1800 characters.
- Paired provider-token benchmark, PR #497 / benchmark run `32783224909`: p95 input tokens 1169 → 949 (-18.82%).
- Same paired benchmark: uncached-equivalent cost per machine-accepted safe answer 224.00 → 187.67 micro-USD (-16.22%).
- Same paired benchmark: 3/3 machine-safe answers on both former 3000-character baseline and current 1800-character runtime.
- Paired routing corpus: LLM calls 8/12 (66.7%) → 4/12 (33.3%), a 50% relative reduction.
- PR #497 exact-head gates: benchmark run `32783224909` success, migration drift run `32783224838` success, CI run `32783224942` success.
- PR #497 merged to `main` as `7e144b234e77299f2a49ee894761468a8702c8d2`.

## Limits / non-claims

- Prompt cache is not measured as zero. Three probe strategies failed to obtain a usable `cached_tokens` value; the tested Groq surface returned absent/null cache telemetry.
- Cost is controlled uncached-equivalent cost, not provider billing reconciliation.
- Acceptance is deterministic machine-safety acceptance, not human review or clinical-quality certification.
- No real-patient payload was used for these provider benchmarks.
- No Vercel deployment is implied or authorized by this receipt.

## Remaining gates before FRUG-5 CLOSED

1. FRUG-0 real-traffic telemetry sufficient to report real p50/p95 token distribution, actual model/zero-model call rate and cost per response/MAU.
2. Provider billing reconciliation for real-cost claims.
3. Prompt-cache evidence if/when the authenticated provider surface exposes a measurable cache metric.

Until those gates are proven, FRUG-5 remains OPEN and the P4-FRUGAL canonical numerator is not increased by this receipt.