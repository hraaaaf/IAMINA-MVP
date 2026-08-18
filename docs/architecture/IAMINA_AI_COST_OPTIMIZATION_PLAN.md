# IAMINA AI Cost Optimization Plan

Status: **ARCHITECTURE PLAN / NO RUNTIME CHANGE**

## Goal

Preserve IAMINA's deterministic clinical intelligence and safety while minimizing variable AI cost per active patient.

## Verified current architecture

IAMINA already separates clinical authority from generation:

- high-risk safety / prescription / insulin boundaries are evaluated before the conversational LLM path;
- approved clinical/domain context is computed outside the model;
- the model is a narrator over governed context, not the source of diagnosis, treatment, dose or clinical priority;
- PHI minimization/pseudonymization and processor policy sit before provider egress;
- the current LLM factory is provider-level routing, primarily Gemini -> Kimi -> static fallback;
- the conversational prompt caps normal answers at 2 sentences / 40 words but currently resends repeated instructions and up to ~3000 characters of conversation history on each turn.

This separation allows aggressive model-cost optimization without moving clinical authority into a cheaper model.

## Main cost leaks to remove

1. **Model used too often**: routine deterministic replies can bypass generation entirely.
2. **Static prompt resent every turn**: the system safety/narrator contract is highly repetitive and should be cache-friendly.
3. **History resent as raw text**: the conversation path can include up to ~3000 characters plus older snippets on every model call.
4. **Unnecessary structured output**: the runtime requests `reply` plus `concern_detected`, while the caller only requires `reply`; JSON reliability also forces a stronger model than plain bounded narration may require.
5. **No hard provider output-token cap**: 40-word behavior is prompt-enforced rather than API-enforced.
6. **Routing is quota-first rather than task/cost-first**: current Gemini -> Kimi fallback does not select the cheapest adequate model by task.
7. **Reasoning path exists**: `think()` exposes a 2048-token thinking budget in the Gemini provider and must never become the routine patient-chat path.
8. **Cloud media can become the dominant bill** if TTS/OCR/STT are invoked indiscriminately.

## Target architecture: deterministic brain, cheap language layer

### Tier 0 — zero-model path

Use deterministic code/templates when the response can be safely produced from known state:

- emergency / insulin / prescription boundaries;
- fixed safety notices;
- exact CGM/device states and source provenance;
- confirmations, acknowledgements, simple navigation/help;
- repeated FAQ whose answer is already governed and locale-approved;
- identical/recent duplicate user requests when the underlying governed state has not changed.

Target: **30-50% of conversational turns should require no generative call** after instrumentation proves equivalence.

### Tier 1 — cheap narrator

For normal companion conversation over approved context:

- short prompt;
- no chain-of-thought/reasoning mode;
- response API capped to a small output budget;
- cheap model only;
- candidate benchmark: DeepSeek V4 Flash, Gemini 2.5 Flash-Lite, Qwen low-cost API candidate, Kimi low-cost candidate;
- GPT-5 nano may be tested as a control for simple narration/classification.

The cheapest model passing the safety/language/quality floor wins.

### Tier 2 — quality fallback

Escalate only when Tier 1 fails a deterministic acceptance test:

- invalid output contract;
- unsupported language/mixed Darija confidence;
- material ambiguity in narration;
- repeated provider failure;
- complex longitudinal explanation whose governed context is valid but Tier 1 quality is below threshold.

Candidate: GPT-5 mini or the best cost/quality winner from Qwen/Kimi/Gemini-class models.

Target: **<10% of generative turns**.

### Tier 3 — frontier exception

No frontier model in routine patient runtime.

Allowed only for an explicitly benchmarked future task with a demonstrated quality requirement that Tier 1/2 cannot meet. Never silently escalate based on provider marketing or model availability.

## Prompt optimization

### P1 — remove redundant payload

- Replace raw 3000-character rolling history with:
  - last 1-2 user/assistant turns;
  - deterministic compact relationship-state summary;
  - governed clinical context already produced by CompanionContext/DomainContext.
- Keep all clinical facts out of free-text memory unless already approved by the governed context contract.
- Remove unused `concern_detected` output if no caller consumes it.
- Prefer bounded plain-text narration where safe; keep JSON only where machine parsing is truly required.

### P2 — stable prefix and caching

Keep the immutable narrator/safety contract at the beginning of the request and stable byte-for-byte across turns so provider prefix caching can work.

Track per call:

- uncached input tokens;
- cached input tokens;
- output tokens;
- cache-hit ratio;
- total provider cost.

DeepSeek supports automatic prefix caching. Gemini and OpenAI offer discounted cached input/context mechanisms; implementation remains provider-specific and must be benchmarked rather than assumed.

### P3 — hard token ceilings

For routine patient narration:

- output target: <= 60 tokens unless a safety response is deterministic and bypasses the model;
- API `max_output_tokens` / equivalent must enforce the ceiling;
- no thinking/reasoning budget by default;
- reject or truncate oversized generative context before egress.

## STT optimization

Pipeline:

1. device-side voice activity detection;
2. trim silence before upload;
3. mono 16 kHz or provider-recommended compact encoding;
4. reject accidental long recordings before network invocation;
5. hash audio and reuse an existing transcript for exact duplicate uploads;
6. specialized low-cost STT only;
7. higher-cost STT only when confidence/quality gate fails.

Benchmark candidates:

- Voxtral Mini Transcribe 2;
- GPT-4o-mini-transcribe;
- xAI/Grok STT if current official pricing/quality makes it competitive;
- on-device transcription as a zero-cloud challenger where FR/AR/Darija quality is adequate.

Never send an audio stream continuously merely because the microphone UI is open.

## TTS optimization

Default: **native iOS/Android TTS**.

Cloud TTS is an exception, not the normal path:

- only if native FR/AR/Darija intelligibility fails the UX floor;
- user-triggered playback rather than automatic playback;
- cache generated speech by `(normalized_text, locale, voice, version)` hash;
- never regenerate identical fixed safety/help phrases;
- prebundle approved fixed emergency/help audio locally if needed.

Target variable TTS API cost: approximately zero for the median patient.

## OCR / image optimization

### Documents and glucometers

1. local crop / perspective correction / contrast normalization;
2. local PaddleOCR PP-OCRv6 first;
3. deterministic validation of extracted units, ranges and expected field formats;
4. accept locally only above a measured confidence threshold;
5. send **only the uncertain crop/page**, not the complete original media, to a dedicated cheap cloud OCR fallback;
6. general-purpose VLM only after local + dedicated OCR failure.

For numeric glucometer displays, benchmark a digit/display-specific local path against general OCR; a specialized local recognizer may be both cheaper and safer than a VLM.

### Meal photos

Do not invoke vision automatically for every image.

- local resize/compression first;
- small multimodal model only on explicit meal-analysis intent;
- force qualitative/bounded uncertainty output;
- no exact carbohydrate claim unless a separate governed estimator provides it.

## Provider abstraction

Current provider-specific classes should evolve toward a **capability + cost router** while preserving the central LLM gateway and egress policy.

Recommended provider metadata:

- provider/model/version;
- capabilities: text, structured output, vision, STT, TTS, OCR;
- locale quality status;
- current input/cached-input/output/audio/page pricing;
- max output cap support;
- cache support;
- account/region eligibility;
- observed benchmark quality;
- observed P50/P95 latency;
- hard-floor status.

DeepSeek, Kimi and several Qwen endpoints are OpenAI-compatible. Prefer one governed OpenAI-compatible adapter with provider configuration rather than duplicating nearly identical HTTP/client implementations, while retaining provider-specific policy metadata.

## Runtime router decision

Pseudo-policy:

```text
input
 -> deterministic safety gate
 -> deterministic zero-model resolver
 -> modality router
 -> cheapest eligible Tier-1 candidate
 -> deterministic output validator
      PASS -> answer
      FAIL -> one Tier-2 retry
      FAIL -> governed offline/static fallback
```

Maximum one paid escalation per user turn. No cascading 3-5-model retry chain.

## Cost guardrails

Introduce first-class usage accounting independent of provider billing:

- cost per patient/day/month;
- calls by modality and route tier;
- tokens/minutes/pages/images;
- cache hit ratio;
- Tier-2 escalation rate;
- offline fallback rate;
- accepted-answer cost;
- provider error rate.

Recommended product guards to benchmark before production:

- soft per-patient monthly AI budget warning;
- hard abuse/rate limits;
- no model call for duplicate requests with unchanged governed state;
- global provider circuit breaker;
- no paid background generation when deterministic/batch computation can produce the same result.

Do not degrade safety when a monetary cap is hit: fall back to deterministic approved responses, never to an ungoverned cheaper model.

## Background work

Move non-interactive tasks to cheaper asynchronous execution where latency is irrelevant:

- aggregate analytics;
- non-patient-facing summaries;
- offline evaluation;
- optional memory compaction if deterministic compaction is insufficient.

Use batch pricing only when the task is non-interactive and contains approved minimized data.

## Quality-preservation gates

A cost optimization may ship only if it preserves:

1. deterministic safety interception;
2. no-prescription/no-dose behavior;
3. approved-context-only narration;
4. FR/AR/Darija/mixed-language minimum quality;
5. output factuality against the supplied governed state;
6. fallback behavior under quota/network failure.

Primary KPI is **cost per accepted safe answer**, not raw cost per API call.

## Implementation roadmap

### C0 — instrumentation baseline

Measure current real/synthetic prompt bytes, tokens, model route, output size and estimated cost. No behavior change.

Success: reproducible cost trace per synthetic benchmark case.

### C1 — prompt diet

- compact conversation history;
- remove unused output fields;
- API output-token ceiling;
- prohibit routine `think()`;
- stable cacheable system prefix.

Success: >= 40% reduction in uncached text input tokens on the canonical conversation benchmark with no quality-floor regression.

### C2 — zero-model router

Add deterministic intent classes and duplicate/state-stable reply reuse.

Success: measured model-call avoidance with exact regression coverage; no safety path routed to generation.

### C3 — cost-first text router

Benchmark cheap Tier-1 candidates, then one quality fallback.

Success: cheapest candidate passes all hard floors; Tier-2 escalation threshold fixed from evidence.

### C4 — local-first media

- native TTS;
- local OCR preprocessing/PaddleOCR;
- STT compression/silence trimming;
- cloud fallback only on measured failure.

Success: median TTS API cost ~0 and OCR cloud invocation rate minimized without accuracy regression.

### C5 — budget controller

Per-patient/month usage ledger, circuit breakers and operational dashboard metrics.

Success: synthetic load test cannot exceed configured cost budget silently.

## Economic target

Initial engineering target, to be validated by benchmark rather than declared as achieved:

- median active patient AI-variable cost: **<= $0.15/month**;
- normal active patient: **<= $0.25/month**;
- heavy but legitimate patient: **<= $0.50/month**;
- no routine cloud TTS;
- no frontier-model dependency.

These targets exclude hosting/database/SMS/support and are not current measured production costs.

## Non-claims

This document is an optimization architecture plan. It does not claim benchmark success, provider selection, production cost, clinical approval or production readiness.
