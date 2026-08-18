# IAMINA AI Cost Optimization Plan

Status: **ARCHITECTURE + VERIFIED IMPLEMENTATION EVIDENCE / NO PROVIDER CUTOVER**

## Goal

Preserve IAMINA's deterministic clinical intelligence and safety while minimizing variable AI cost per active patient.

## Success criteria

A cost optimization is accepted only when evidence shows that it preserves the governed safety/quality floor and lowers or bounds variable cost. Primary KPI: **cost per accepted safe answer**, not raw API-call price.

## Verified architecture

IAMINA separates clinical authority from generation:

- urgent / insulin / prescription boundaries are evaluated before conversational generation;
- governed clinical/domain context is computed outside the model;
- the model narrates approved context rather than deciding diagnosis, treatment, dose or clinical priority;
- PHI/egress and processor policy remain upstream of external-provider invocation;
- zero-model routing exists for bounded deterministic conversation cases;
- DeepSeek and Qwen have governed low-cost OpenAI-compatible adapters;
- STT is isolated behind a provider-neutral injectable boundary; Gemini remains the current default;
- cloud meal/glucometer vision is isolated behind a provider-neutral injectable boundary; Gemini remains the current default;
- native client-side `flutter_tts` exists and remains the preferred TTS path;
- mobile glucometer OCR remains local-first with on-device ML Kit; web/cloud is fallback;
- current Gemini, Kimi and governed OpenAI-compatible low-cost text adapters enforce a `160` output-token ceiling at the provider API layer;
- controlled expiring pricing and budget authorization exist for text and now for generic metered modalities such as STT seconds, OCR pages, images and TTS characters.

These facts allow aggressive cost optimization without moving clinical authority into a cheaper model.

## Verified local OCR evidence

### Tesseract C10

Synthetic zero-egress baseline:

- `54 mg/dL`: PASS;
- lab diagnostic case: `HbA1c` misread as `HbAlc`;
- decision: retain only as a narrow digit/glucometer baseline, not lab-document OCR authority.

### PaddleOCR C12

Prior exact-head measurement on `5a36b281437e84d5726c040eea831a8b12522e5c`:

- PaddleOCR `3.7.0`, PaddlePaddle `3.2.2`;
- `PP-OCRv6_small_det` + `PP-OCRv6_small_rec`;
- CPU local inference;
- 2/2 synthetic gating cases PASS;
- setup: `57282.16 ms`;
- `54 mg/dL`: `582.93 ms`, mean recognition confidence `0.99978`;
- `HbA1c 7.4 % / Glycemie a jeun 1.32 g/L`: `509.38 ms`, mean recognition confidence `0.998261`;
- patient data: false; provider API: false; paid inference: false.

This proves only the synthetic fixtures. Real camera conditions, Arabic OCR and production suitability remain unproven.

## Target architecture: deterministic brain, cheap language layer

### Tier 0 — zero-model

Use deterministic code/templates when the response can be safely produced from known governed state:

- emergency / insulin / prescription boundaries;
- fixed safety notices;
- exact device/status/provenance responses;
- bounded acknowledgements/help/navigation;
- repeated state-stable requests where deterministic reuse is safe.

The model-call avoidance rate must be measured; no target percentage is declared achieved without telemetry.

### Tier 1 — cheap narrator

For normal companion narration over approved context:

- short governed prompt;
- no reasoning/chain-of-thought mode;
- task-specific output ceiling;
- cheapest adequate model only.

Candidate benchmark:

- DeepSeek V4 Flash;
- Gemini 2.5 Flash-Lite;
- Qwen low-cost candidate;
- Kimi low-cost candidate;
- GPT-5 nano as an ultra-cheap control.

The cheapest candidate passing the safety/language/quality floor wins.

### Tier 2 — quality fallback

Escalate at most once when Tier 1 fails a deterministic acceptance condition such as invalid output contract, unsupported language quality or material narration ambiguity.

Candidate: GPT-5 mini or the best evidence-backed stronger Tier-1 family variant.

### Tier 3 — frontier exception

No frontier model in routine patient runtime. Any future use requires an explicitly benchmarked task for which cheaper candidates fail a demonstrated requirement.

## Text optimization

### Prompt diet

Continue to minimize repeated payload while preserving governed context:

- compact recent conversational state instead of unnecessary raw history;
- stable byte-identical prefix where provider caching can exploit it;
- remove unused structured-output fields where callers do not consume them;
- prefer bounded plain text where machine parsing is unnecessary.

### Output ceilings

The old plan item “add a hard provider output cap” is already partially delivered: current Gemini/Kimi/governed low-cost compatible adapters use a `160` token provider-side ceiling.

Remaining optimization is **task-specific ceilings**, not a blind global reduction. Routine narration may justify a lower ceiling, while structured summaries can require more. Evidence must prevent truncation regressions.

### Reasoning

Gemini `think()` exposes a 2048-token thinking budget. It must not become the routine patient-chat path without a separately justified task.

## STT optimization

Provider selection is now decoupled from the clinical pipeline. Remaining benchmark pipeline:

1. trim avoidable silence / accidental long recordings where feasible;
2. compact provider-supported encoding;
3. specialized low-cost STT first;
4. one higher-quality fallback only after measured failure;
5. deterministic triage remains after transcription and outside provider authority.

Candidates:

- Voxtral Mini Transcribe 2;
- GPT-4o-mini-transcribe;
- xAI/Grok STT if current controlled price/API availability remains competitive;
- on-device transcription challenger where FR/AR/Darija quality is adequate.

## TTS optimization

Default remains **native iOS/Android TTS through `flutter_tts`**.

Cloud TTS is an exception only if measured device intelligibility fails the UX floor. Fixed approved help/safety phrases should be reusable locally rather than regenerated.

Target variable TTS API cost remains approximately zero for the median patient, but this is not yet a measured production result.

## OCR / vision optimization

### Glucometer

- mobile: on-device ML Kit remains primary;
- Tesseract: narrow digit baseline only;
- PP-OCRv6 small: promising measured local candidate on synthetic fixtures;
- cloud: explicit fallback after local uncertainty/failure, not routine first choice.

### Documents

PP-OCRv6 small earned a local synthetic candidate position after C12 2/2, but harder camera/document fixtures and multilingual requirements must be measured before production use. Arabic support/quality must not be inferred from Latin-script synthetic evidence.

### Meal photos

- explicit user intent only;
- capture already reduces image payload (`maxWidth: 1600`, image quality `85`);
- bounded food identification only;
- no exact carbohydrate claim unless a separate governed estimator establishes it;
- provider-neutral cloud vision boundary enables later cost/quality comparison without changing clinical authority.

## Pricing and budget control

### Delivered contracts

- controlled expiring text-token pricing registry;
- fail-closed text spend authorization before paid invocation;
- generic exact-rational `MeteredPrice` for non-text units;
- fail-closed metered spend authorization under existing per-subject/month and single-call caps.

No real provider price is hard-coded in these contracts. Current provider/model/modality pricing must be loaded from controlled, current evidence and rejected when missing, ambiguous or stale.

### Remaining runtime guardrails

Before production provider cutover, prove:

- per-patient/day/month usage accounting;
- modality/tier call counts;
- tokens/seconds/pages/images/characters as applicable;
- cache-hit and fallback rates;
- single-call and monthly budget enforcement under synthetic load;
- provider circuit breaker / abuse limits;
- deterministic approved fallback when monetary limits are hit.

Safety must never degrade because a budget is exhausted.

## Provider abstraction

Text, STT and cloud vision now have important abstraction boundaries, but the final capability + cost router remains an evidence-driven target.

Provider metadata should include:

- provider/model/version;
- modality/capability;
- locale quality status;
- current controlled price evidence + review date;
- output/caching support;
- account/region eligibility;
- observed quality and latency;
- hard-floor status.

## Runtime routing target

```text
input
 -> deterministic safety gate
 -> deterministic zero-model resolver
 -> modality router
 -> cheapest eligible candidate
 -> deterministic output validator
      PASS -> answer
      FAIL -> at most one evidence-approved fallback
      FAIL -> governed offline/static fallback
```

No cascading 3-5-provider retry chain.

## Economic target

Engineering targets to validate, not production claims:

- median active patient AI-variable cost: **<= $0.15/month**;
- normal active patient: **<= $0.25/month**;
- heavy legitimate patient: **<= $0.50/month**;
- no routine cloud TTS;
- no routine frontier-model dependency.

These targets exclude hosting, database, notifications/SMS and support.

## Execution roadmap

### Delivered / evidence-backed foundation

- usage instrumentation foundation;
- prompt/output diet foundation;
- bounded zero-model conversation routing;
- governed DeepSeek/Qwen adapters;
- local STT benchmark lane;
- native TTS benchmark lane;
- controlled expiring pricing registry;
- local OCR execution boundary;
- pricing -> budget authorization bridge;
- C10 Tesseract measured baseline;
- provider-neutral STT boundary;
- provider-neutral cloud vision boundary;
- C13 metered-media pricing/budget contract;
- C12 PaddleOCR prior 2/2 synthetic measurement, with exact-head recertification tracked in #319.

### Remaining critical path

1. exact-head C12 recertification and merge;
2. broaden local OCR real-world/synthetic-hardening fixtures;
3. measured STT comparison on FR/AR/Darija/mixed audio;
4. native TTS real-device intelligibility gate;
5. paid/network text-provider benchmark only after explicit network/credential authorization and spend ceiling;
6. final evidence-backed capability + cost routing/cutover decision;
7. production budget/usage certification before any patient-data release.

## Non-claims

This plan does not claim production provider selection, production cost, real-world OCR accuracy, clinical approval, CNDP/legal/data-residency authorization, patient-data release or production readiness. Local benchmark success is evidence for one bounded task, not permission for provider or patient cutover.
