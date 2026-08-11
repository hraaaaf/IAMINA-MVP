# IAmina — Truth & Capability Contract

> **Status:** ✅ Certified through P0.5 implementation — truth/capability chassis, structured insight gateway, legacy-memory/heuristic quarantine and epistemic patient-visible output boundaries are implemented; P0.5A PR #120 and P0.5B PR #121 are both exact-head certified and post-merge green.  
> **Scope:** IAmina companion reasoning, memory provenance, patient-visible claim authority and generative-model authority.  
> **Non-scope:** no new disease module, clinical threshold, diagnosis, prescription, treatment optimization or autonomous clinical write.

## 1. Purpose

IAmina must distinguish what is **observed**, what the **patient reported**, what a **deterministic engine derived**, what is merely a **preference or conversational state**, what an **unapproved heuristic inferred**, and what a **generative model inferred**.

Neither a heuristic inference nor a generative inference may become a patient fact, clinical rule or durable clinical truth merely because it was plausible, repeated or persisted.

The same evidence ceiling applies at presentation time: an internal detector label, a legacy fallback string or a generative reformulation must never gain more diagnostic, causal or therapeutic authority than the underlying evidence.

The executable source is:

- `backend/core/contracts/truth.py`
- `backend/core/contracts/capabilities.py`
- `backend/companion/memory_truth.py`
- `backend/core/medical_safety.py`
- `backend/core/epistemic_safety.py`

## 2. Truth classes

| Truth kind | Meaning | May persist as patient fact? | May enter deterministic clinical logic? |
|---|---|---:|---:|
| `OBSERVED_FACT` | measured/imported/explicitly recorded observation from an authoritative product source | yes | yes |
| `USER_CLAIM` | information explicitly reported by the patient but not independently validated | yes, as a claim | yes, while remaining explicitly a claim |
| `DETERMINISTIC_DERIVATION` | KPI/pattern/result produced by approved deterministic logic from authoritative inputs | no, recalculate from source | yes |
| `PREFERENCE` | patient-selected product preference such as language/presentation choice | yes | no |
| `CONVERSATIONAL_STATE` | transient relationship/tone/dialogue state | no clinical-fact persistence | no |
| `HEURISTIC_INFERENCE` | output of a non-authoritative heuristic without an approved clinical derivation contract | no | no |
| `MODEL_INFERENCE` | hypothesis or interpretation produced by a generative model | no | no |

### Persistence rule

Patient-fact storage may contain observed facts, explicit user claims and explicit preferences. A deterministic derivation is recomputed from its source data rather than silently materialized as immutable fact. Conversational state, heuristic inference and model inference remain outside patient clinical truth.

A companion-memory snapshot is **not** a patient-fact store. If non-clinical runtime state, a recomputable derivative or compatibility-only heuristic data is cached there, it must carry an explicit truth kind and stable source and must never gain additional clinical authority merely because it survived a restart.

### Deterministic clinical-input rule

Observed facts, explicitly labeled patient claims and approved deterministic derivations may be consumed by deterministic clinical/safety logic. A patient-reported symptom can therefore inform deterministic triage without being promoted into a validated diagnosis or independently observed fact. Heuristic inference, generative output and conversational state never become clinical decision inputs.

## 3. Capability authority

The product separates a capability from the authority allowed to perform it.

### Generative-model capabilities allowed

A generative model may:

- explain approved data;
- summarize approved data;
- verbalize approved evidence within the patient-visible claim ceiling;
- help prepare questions for a clinician.

The model does not become the source of the underlying metric, pattern or clinical rule. A semantic detector name is not itself approved patient-facing evidence.

### Deterministic-only capability

Emergency classification is owned exclusively by deterministic safety logic upstream of generative AI.

### Disabled capabilities

No authority inside IAmina is permitted to autonomously:

- diagnose;
- prescribe;
- calculate a medication or insulin dose;
- optimize treatment;
- change treatment;
- promote a model inference into patient fact;
- promote a heuristic inference into approved clinical truth;
- upgrade an association/temporal sequence into proven causality;
- write a clinical record autonomously on behalf of the patient.

Changing this list requires an explicit product/regulatory architecture decision and is not a prompt-level change.

## 4. User-confirmed writes

Recording a user claim or changing a user preference requires explicit user confirmation. A generative model may propose wording or ask a question, but it may not silently persist the answer as a validated clinical fact.

## 5. LLM gateway enforcement

`core.llm_gateway.GatewayLLM` accepts only capabilities for which `GENERATIVE_MODEL` is an allowed authority. A forbidden capability fails closed before provider egress.

`narrate()` and `doctor-brief` are classified as `SUMMARIZE_APPROVED_DATA`. The diabetes structured insight formatter is classified as `SURFACE_DETERMINISTIC_PATTERN`; it may call the gateway, but P0.5A independently constrains the final patient-visible structured insight to an observation-only envelope. A successful LLM call therefore does not grant the generated title/content/action clinical authority.

For summary/doctor-brief narration, P0.5B constrains the generative evidence surface to deterministic KPI/stat input and applies a focused fail-closed epistemic guard to the exact `narrative/key_insight/doctor_brief` schema.

The existing egress authorization, consent, PHI stripping, deterministic safety, no-prescription sanitation and epistemic-output safety layers remain mandatory and independent. Passing the capability contract does **not** itself authorize external data transfer or a stronger clinical claim.

## 6. Legacy-memory boundary

P0.4/P0.4.1 migrates the legacy companion snapshot boundary without changing the database schema. `memory` and `deep` continue to use the condition-agnostic `SnapshotStore` and existing JSON fields, while new writes use the versioned `iamina.companion-memory` v3 envelope defined in `backend/companion/memory_truth.py`.

Each persisted field carries its expected `TruthKind` and stable non-PHI source. Wrong namespace, unknown schema version, malformed envelopes or provenance mismatch fail closed rather than silently gaining authority. The stored `patient_id` can never override the identity selected by the caller.

Legacy flat snapshots and P0.4 v2 envelopes remain readable for backward compatibility. Legacy `last_concern`, `current_tone` and `emotional_signals` from flat snapshots are reset to neutral defaults because their old format cannot prove whether the value came from deterministic keyword handling or generative output. New deterministic keyword-derived emotion/tone state is persisted explicitly as `CONVERSATIONAL_STATE`; direct generative mutations are rejected at the durable `IAminaMemory.save()` boundary.

Historical `food_sensitivities` are explicitly `HEURISTIC_INFERENCE`, not `DETERMINISTIC_DERIVATION`. During flat/v2 decoding and every new deep-memory encode boundary, such values move into `quarantined_heuristics.food_sensitivities` and the active `food_sensitivities` field is cleared. The compatibility learning method writes quarantine only. The IAmina orchestrator does not learn this legacy heuristic and `compute_state()` cannot turn it into a meal-related intention.

Historical `peak_hours` is also compatibility-only heuristic state, not an approved deterministic clinical derivation. It remains structurally readable but carries `HEURISTIC_INFERENCE` provenance in v3, so it cannot become a patient fact or deterministic clinical input. The exact `DETERMINISTIC_DERIVATION` marker emitted for `peak_hours` by the brief P0.4 v2 window is accepted only during v2 decoding and is rewritten as `HEURISTIC_INFERENCE` on the next v3 encode/save.

Compatibility retention therefore preserves historical information without making either legacy heuristic a patient fact, an approved clinical pattern or an allowed deterministic clinical input.

Detailed implementation and acceptance evidence live in `docs/P0_4_LEGACY_MEMORY_TRUTH_MIGRATION.md`.

## 7. Patient-visible epistemic output boundary

P0.5 separates **detector authority** from **presentation authority**.

### Structured clinical insights — P0.5A

At the final `sanitize_patient_visible()` boundary, the stable structured insight shape keeps only deterministic metadata (`code`, `priority`, `icon`) from the upstream insight. Patient-visible `title`, `content` and `action` are replaced with a localized deterministic observation-only envelope.

The envelope states that the observed trend alone is insufficient to establish a cause or diagnosis and offers only a non-therapeutic documentation/discussion step. This prevents legacy fallback strings or adversarial model text from promoting an internal detector into a named mechanism, causal claim, diagnosis or treatment instruction.

This boundary is implemented in FR, EN, Modern Standard Arabic and Moroccan Darija in Arabic script.

### Summary / doctor brief — P0.5B

`SUMMARY_USER` receives deterministic KPI/stat evidence only. The prompt no longer exposes semantic detector codes/names and no longer contains the legacy therapeutic few-shot example.

The prompt explicitly forbids causal upgrades, named syndrome/phenomenon/mechanism claims and therapeutic/food/exercise/timing/medication/insulin interventions.

`core.epistemic_safety` then provides a focused multilingual fail-closed guard for the exact `narrative/key_insight/doctor_brief` response schema. If one field exceeds the evidence authority, that field alone is discarded; safe sibling fields survive.

Other parser schemas remain outside this focused P0.5B guard and continue to rely on their existing capability/safety boundaries.

### Closure evidence

- P0.5A PR #120 — exact-head `18f14805a240594071a147ad527448a7dcee909b`; CI #1680 + drift #1492; merge `8a941185511b1c0e96b0acb9754794cdfb6209b3`; post-merge CI #1681 + drift #1493 — all green.
- P0.5B PR #121 — exact-head `4ac2f3a9a0c86ffad4386ff22bb9b75b30b8a190`; CI #1688 + drift #1500; merge `9febaaf96b9b17d716f183d2adae625f11d1dce2`; post-merge CI #1690 + drift #1502 — all green.

Detailed evidence lives in `docs/P0_5_EPISTEMIC_CLINICAL_OUTPUT_SAFETY.md`.

## 8. Permanent regression expectations

Tests must prove at minimum that:

- `MODEL_INFERENCE` cannot be persisted as patient fact or enter deterministic clinical logic;
- `HEURISTIC_INFERENCE` cannot be persisted as patient fact or enter deterministic clinical logic;
- `USER_CLAIM` stays explicitly labeled while remaining available to deterministic triage/domain logic;
- deterministic derivations can feed approved logic but are not immutable patient facts;
- generative models cannot classify emergencies;
- diagnosis, prescription, dose calculation, treatment optimization and treatment change remain disabled;
- user-claim/preference writes remain confirmation-gated;
- the LLM gateway rejects forbidden generative capabilities before provider egress;
- `doctor-brief` and the structured diabetes insight formatter cannot regress to direct `get_llm()` provider access;
- legacy flat and P0.4 v2 companion snapshots decode backward-compatibly into the current provenance contract;
- malformed/tampered companion provenance fails closed;
- legacy emotion/tone with unprovable origin is quarantined;
- direct generative concern/tone mutations cannot survive a durable companion-memory save;
- deterministic keyword-derived conversational state can persist with explicit provenance;
- historical food-response heuristic memory is quarantine-only and cannot drive patient-facing reasoning or deterministic clinical logic;
- historical peak-hour heuristic memory is non-clinical `HEURISTIC_INFERENCE`, with v2 compatibility that rewrites corrected provenance on v3 save;
- structured clinical insight metadata can survive while legacy/model patient-visible clinical authority is replaced by the observation-only envelope;
- provider failure cannot resurrect legacy structured-insight therapeutic/causal strings;
- summary/doctor-brief prompts cannot leak semantic detector names through the legacy `patterns=` argument;
- generated summary fields that assert named mechanisms, proven causality or unauthorized interventions fail closed;
- safe uncertainty/caveat language remains allowed rather than being blanket-blocked.
