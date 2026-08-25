# FRUG-9 — Pre-pilot scenario envelope

Date: 2026-08-25
Base: `main@7f0b1b70d76752d4b319201ca1e5e94709f807e3`

## Goal

Publish one reproducible, explicitly hypothetical scale envelope for 1k / 10k / 50k / 100k MAU using only measured provider inputs plus clearly labelled traffic assumptions. This is not a production forecast.

## Inputs

Measured / externally verified:
- model: `openai/gpt-oss-120b` on Groq;
- current controlled non-patient p95 input tokens: 874 tokens/call (FRUG-5 run `32604267329`);
- controlled provider output p95 retained in FRUG-5 evidence: 76 tokens/call;
- Groq list price verified 2026-08-25: $0.15 / 1M input tokens, $0.60 / 1M output tokens, $0.075 / 1M cached input tokens;
- cached-token benefit: 0 assumed in this envelope because IAMINA probes have not exposed usable `cached_tokens` evidence;
- Groq Free Plan limit verified 2026-08-25: 8,000 TPM, 200,000 TPD, 30 RPM, 1,000 RPD.

Scenario assumptions, not measurements:
- 20 interactions / MAU / month;
- 50% of interactions reach the LLM; the other 50% are deterministic/zero-model/safety paths;
- therefore 10 LLM calls / MAU / month;
- 30-day month;
- no retries in the nominal envelope;
- this document costs only the GPT-OSS language lane. OCR, hosted backend/DB, retained object storage and egress remain unresolved until those deployment/scenario choices are pinned.

Official provider sources:
- https://console.groq.com/docs/model/openai/gpt-oss-120b
- https://console.groq.com/docs/rate-limits
- https://console.groq.com/docs/prompt-caching

## Variable GPT-OSS cost calculation

Per LLM call, without cache credit:
- input: `874 × $0.15 / 1,000,000 = $0.0001311`;
- output: `76 × $0.60 / 1,000,000 = $0.0000456`;
- total: **$0.0001767 / LLM call**.

At 10 LLM calls / MAU / month:
- **$0.001767 / MAU / month** variable GPT-OSS list-price equivalent.

| Scenario tier | LLM calls/month | GPT-OSS tokens/month | Variable GPT-OSS cost/month |
|---:|---:|---:|---:|
| 1,000 MAU | 10,000 | 9.50M | $1.767 |
| 10,000 MAU | 100,000 | 95.0M | $17.67 |
| 50,000 MAU | 500,000 | 475M | $88.35 |
| 100,000 MAU | 1,000,000 | 950M | $176.70 |

These figures are list-price-equivalent scenario outputs, not observed invoices.

## First bottleneck: Free Plan quota, not token price

Under the same scenario, average token demand is:
- 1,000 MAU: about 316,667 tokens/day;
- Free Plan allowance: 200,000 tokens/day.

Therefore the current Groq Free Plan is already insufficient for the 1,000-MAU scenario even before peak-hour/concurrency effects are considered.

Ignoring peaks and using only the 200K TPD average ceiling, the theoretical break-even is approximately:

`200,000 × 30 / (10 calls per MAU × 950 tokens per call) ≈ 632 MAU`.

This **~632 MAU figure is only an average-throughput scenario bound for the documented Free Plan**, not production capacity, SLA, or architectural capacity. RPM/RPD/TPM and arrival bursts can bind earlier. Paid/developer limits must be re-evaluated against the actual account tier before launch.

## Unresolved cost components

This envelope deliberately does not invent:
- hosted Django/PostgreSQL fixed monthly cost;
- cloud OCR usage or page price;
- retained object-storage GB-month;
- patient-media egress;
- cache-hit savings;
- STT/TTS/vision spend;
- real retries/fallback distribution;
- real traffic peaks/concurrency.

Those inputs remain `unresolved` in the canonical FRUG-9 model until a deployment architecture or explicit scenario source is selected.

## Conclusion

Pre-pilot FRUG-9 can already state one defensible result: **GPT-OSS token cost is not the first scaling concern under this scenario; the current Groq Free Plan quota is.** The variable GPT-OSS list-price equivalent remains below $177/month even at the hypothetical 100k-MAU traffic mix above, while the free-tier daily token quota is exceeded before 1k MAU.

No claim of total IAMINA cost, production readiness, real MAU economics, provider SLA or billing reconciliation is made.
