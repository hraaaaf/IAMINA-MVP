# FRUG-5A — History budget evidence

Status: runtime activation and paired provider-token comparison completed. FRUG-5 remains open pending the external/live evidence explicitly listed below.

## Goal

Measure whether a smaller recent-history budget materially reduces conversational prompt size while preserving the newest explicit user anchor across French, Arabic, English and a Gulf-Arabic fixture, then verify the activated setting with provider-reported token evidence.

## Deterministic preflight

The benchmark exercised the production `_trim_history` implementation with synthetic, non-clinical histories. It compared the former 3000-character budget with the 1800-character candidate.

`_trim_history` reserves 20% of the configured budget for older-history summary material, so the recent-turn window changes from 2400 to 1440 characters.

| Fixture | Baseline chars | Candidate chars | Reduction | Latest anchor retained |
| --- | ---: | ---: | ---: | --- |
| French | 2379 | 1329 | 44.1% | yes |
| Arabic | 2359 | 1453 | 38.4% | yes |
| English | 2337 | 1385 | 40.7% | yes |
| Gulf Arabic | 2351 | 1397 | 40.6% | yes |

Nearest-rank aggregate preflight:

- p50: 2355 → 1391 characters, 40.9% lower;
- p95: 2379 → 1453 characters, 38.9% lower.

The tests also lock the zero-model boundary: exact greetings/thanks remain eligible, while open-ended health questions in French and Arabic remain model-routed.

## Activated runtime

The production Companion history budget is now `1800` characters in `backend/companion/conversation.py`.

The paired Groq benchmark merged by PR #497 compared the former 3000-character baseline with the current 1800-character runtime using the same hardened narrator, the same three synthetic non-patient FR/EN/MSA cases, the same model, and the same deterministic machine-safety gate.

Provider-reported results:

- p95 input tokens: 1169 → 949, 18.82% lower;
- uncached-equivalent cost per machine-accepted safe answer: 224.00 → 187.67 micro-USD, 16.22% lower;
- machine-safe answers: 3/3 baseline and 3/3 current.

These are machine-accepted safety results, not human acceptance or clinical-quality claims. The cost comparison is an uncached-equivalent calculation from controlled pricing evidence, not provider billing reconciliation.

## Call-rate evidence

A pinned paired pre-farewell/current corpus already proves LLM routing reduction from 8/12 interactions (66.7%) to 4/12 (33.3%), a 50% relative reduction, while clinical/ambiguous cases remain model-routed.

## Prompt-cache limitation

Three probe strategies were attempted, including raw HTTP with three identical requests. Groq did not expose a usable `cached_tokens` measurement on the tested account/surface; the raw field was absent/null on repeated calls. This is recorded as **unavailable**, never as 0% cache usage.

## Remaining FRUG-5 evidence

FRUG-5 is not declared closed by this document. Remaining external/live evidence:

1. FRUG-0 real-traffic token/call/cost telemetry and provider billing reconciliation sufficient for the roadmap's real-cost claims;
2. provider prompt-cache measurement if/when the authenticated surface exposes a usable cache metric.

No patient data, human acceptance, production billing reconciliation, CNDP/legal conclusion or Vercel deployment is claimed here.