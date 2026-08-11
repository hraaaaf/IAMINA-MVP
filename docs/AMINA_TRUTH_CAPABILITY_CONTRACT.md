# IAmina — Truth & Capability Contract

> **Status:** chassis contract introduced by P0.2, extended to structured insight formatting by P0.3 and legacy-memory enforcement by P0.4/P0.4.1.  
> **Scope:** IAmina companion reasoning, memory provenance and generative-model authority.  
> **Non-scope:** no new disease module, clinical threshold, diagnosis, prescription, treatment optimization or patient-facing UX.

## 1. Purpose

IAmina must distinguish what is **observed**, what the **patient reported**, what a **deterministic engine derived**, what is merely a **preference or conversational state**, what an **unapproved heuristic inferred**, and what a **generative model inferred**.

Neither a heuristic inference nor a generative inference may become a patient fact, clinical rule or durable clinical truth merely because it was plausible, repeated or persisted.

The executable source is:

- `backend/core/contracts/truth.py`
- `backend/core/contracts/capabilities.py`
- `backend/companion/memory_truth.py`

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
- verbalize a pattern that was already detected deterministically;
- help prepare questions for a clinician.

The model does not become the source of the underlying metric, pattern or clinical rule.

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
- write a clinical record autonomously on behalf of the patient.

Changing this list requires an explicit product/regulatory architecture decision and is not a prompt-level change.

## 4. User-confirmed writes

Recording a user claim or changing a user preference requires explicit user confirmation. A generative model may propose wording or ask a question, but it may not silently persist the answer as a validated clinical fact.

## 5. LLM gateway enforcement

`core.llm_gateway.GatewayLLM` accepts only capabilities for which `GENERATIVE_MODEL` is an allowed authority. A forbidden capability fails closed before provider egress.

`narrate()` and `doctor-brief` are classified as `SUMMARIZE_APPROVED_DATA`. The diabetes structured insight formatter is classified as `SURFACE_DETERMINISTIC_PATTERN`; it may only verbalize patterns already produced by deterministic logic and preserves its structured JSON parse/fallback and patient-visible sanitation contract behind the same gateway.

The existing egress authorization, consent, PHI stripping, deterministic safety and output-safety layers remain mandatory and independent. Passing the capability contract does **not** itself authorize external data transfer.

## 6. Legacy-memory boundary

P0.4/P0.4.1 migrates the legacy companion snapshot boundary without changing the database schema. `memory` and `deep` continue to use the condition-agnostic `SnapshotStore` and existing JSON fields, while new writes use the versioned `iamina.companion-memory` v3 envelope defined in `backend/companion/memory_truth.py`.

Each persisted field carries its expected `TruthKind` and stable non-PHI source. Wrong namespace, unknown schema version, malformed envelopes or provenance mismatch fail closed rather than silently gaining authority. The stored `patient_id` can never override the identity selected by the caller.

Legacy flat snapshots and P0.4 v2 envelopes remain readable for backward compatibility. Legacy `last_concern`, `current_tone` and `emotional_signals` from flat snapshots are reset to neutral defaults because their old format cannot prove whether the value came from deterministic keyword handling or generative output. New deterministic keyword-derived emotion/tone state is persisted explicitly as `CONVERSATIONAL_STATE`; direct generative mutations are rejected at the durable `IAminaMemory.save()` boundary.

Historical `food_sensitivities` are explicitly `HEURISTIC_INFERENCE`, not `DETERMINISTIC_DERIVATION`. During flat/v2 decoding and every new deep-memory encode boundary, such values move into `quarantined_heuristics.food_sensitivities` and the active `food_sensitivities` field is cleared. The compatibility learning method writes quarantine only. The IAmina orchestrator does not learn this legacy heuristic and `compute_state()` cannot turn it into a meal-related intention.

Compatibility retention therefore preserves historical information without making the heuristic a patient fact, an approved clinical pattern or an allowed deterministic clinical input.

Detailed implementation and acceptance evidence live in `docs/P0_4_LEGACY_MEMORY_TRUTH_MIGRATION.md`.

## 7. Permanent regression expectations

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
- historical food-response heuristic memory is quarantine-only and cannot drive patient-facing reasoning or deterministic clinical logic.
