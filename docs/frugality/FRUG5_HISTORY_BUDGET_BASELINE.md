# FRUG-5A — History budget preflight

Status: deterministic preflight only. Production history budget remains unchanged at 3000 characters in this lot.

## Goal

Measure whether a smaller recent-history budget can materially reduce conversational prompt size while preserving the newest explicit user anchor across French, Arabic, English and a Gulf-Arabic fixture.

## Method

The benchmark exercises the production `_trim_history` implementation with synthetic, non-clinical histories. It compares the current configured budget of 3000 characters with a candidate budget of 1800 characters.

`_trim_history` reserves 20% of the configured budget for older-history summary material, so the recent-turn window is 2400 characters at the current setting and 1440 characters at the candidate setting.

These are character measurements, not token measurements. IAMINA does not infer or fabricate token precision when the provider did not report tokens.

## Deterministic results

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

## Decision

The 1800-character setting is eligible for a controlled runtime comparison, but is **not activated by this lot**. Before changing production, FRUG-5 still requires:

1. exact-head CI proof for this benchmark;
2. multilingual multiturn quality/safety comparison with the candidate window;
3. provider-reported prompt-token p50/p95 from telemetry when a stable authenticated provider is available;
4. actual LLM-call-rate and cost/MAU comparison from the usage ledger.

No clinical authority, safety ordering, provider routing or model output cap changes in FRUG-5A.
