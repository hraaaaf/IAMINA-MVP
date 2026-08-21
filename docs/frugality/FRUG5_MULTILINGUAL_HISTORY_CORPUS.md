# FRUG-5 — Expanded multilingual history-window preflight

Status: deterministic context-window preflight. This is **not** native-speaker linguistic certification and does not claim provider token savings.

## Scope

The production 1800-character history budget is exercised against synthetic, non-clinical locale-labelled fixtures for:

- French;
- English;
- Modern Standard Arabic;
- Moroccan Darija;
- Saudi Arabic;
- Emirati Arabic;
- Kuwaiti Arabic;
- Qatari Arabic;
- Omani Arabic;
- French/Darija code-switching.

The purpose is narrow: prove that `_trim_history` preserves the newest explicit user anchor and materially reduces history characters across the locale corpus. Full CI continues to own deterministic clinical/safety regressions. Human/native review remains required for any claim about dialect quality.

## Deterministic results

| Fixture | Baseline chars | 1800-budget chars | Reduction |
| --- | ---: | ---: | ---: |
| French | 2389 | 1423 | 40.4% |
| English | 2337 | 1385 | 40.7% |
| MSA | 2366 | 1373 | 42.0% |
| Darija MA | 2352 | 1398 | 40.6% |
| Saudi | 2158 | 1380 | 36.1% |
| Emirati | 2159 | 1381 | 36.0% |
| Kuwaiti | 2157 | 1457 | 32.5% |
| Qatari | 2156 | 1456 | 32.5% |
| Omani | 2255 | 1442 | 36.1% |
| FR/Darija code-switch | 2306 | 1352 | 41.4% |

Aggregate character preflight:

- median: 2280.5 → 1391.5 characters, about 39.0% lower;
- nearest-rank p95: 2389 → 1457 characters, about 39.0% lower;
- newest explicit anchor retained in every fixture.

## What this does not prove

- no provider token p50/p95 is inferred from characters;
- no native-speaker dialect score is claimed;
- no production LLM call-rate or cost reduction is claimed without real telemetry;
- no safety authority or model/provider behavior is changed by this benchmark.
