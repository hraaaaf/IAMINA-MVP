# IAmina — Truth & Capability Contract

> **Status:** chassis contract introduced by P0.2.  
> **Scope:** IAmina companion reasoning, memory provenance and generative-model authority.  
> **Non-scope:** no new disease module, clinical threshold, diagnosis, prescription, treatment optimization or patient-facing UX.

## 1. Purpose

IAmina must distinguish what is **observed**, what the **patient reported**, what a **deterministic engine derived**, what is merely a **preference or conversational state**, and what a **generative model inferred**.

A generative inference must never become a patient fact, clinical rule or durable clinical truth merely because it was plausible or repeated.

The executable source is:

- `backend/core/contracts/truth.py`
- `backend/core/contracts/capabilities.py`

## 2. Truth classes

| Truth kind | Meaning | May persist as patient fact? | May enter deterministic clinical logic? |
|---|---|---:|---:|
| `OBSERVED_FACT` | measured/imported/explicitly recorded observation from an authoritative product source | yes | yes |
| `USER_CLAIM` | information explicitly reported by the patient but not independently validated | yes, as a claim | yes, while remaining explicitly a claim |
| `DETERMINISTIC_DERIVATION` | KPI/pattern/result produced by approved deterministic logic from authoritative inputs | no, recalculate from source | yes |
| `PREFERENCE` | patient-selected product preference such as language/presentation choice | yes | no |
| `CONVERSATIONAL_STATE` | transient relationship/tone/dialogue state | no clinical-fact persistence | no |
| `MODEL_INFERENCE` | hypothesis or interpretation produced by a generative model | no | no |

### Persistence rule

Patient-fact storage may contain observed facts, explicit user claims and explicit preferences. A deterministic derivation is recomputed from its source data rather than silently materialized as immutable fact. Conversational state and model inference remain outside patient clinical truth.

### Deterministic clinical-input rule

Observed facts, explicitly labeled patient claims and approved deterministic derivations may be consumed by deterministic clinical/safety logic. A patient-reported symptom can therefore inform deterministic triage without being promoted into a validated diagnosis or independently observed fact. Generative output and conversational state never become clinical decision inputs.

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

`narrate()` is explicitly classified as `SUMMARIZE_APPROVED_DATA`.

The existing egress authorization, consent, PHI stripping, deterministic safety and output-safety layers remain mandatory and independent. Passing the capability contract does **not** itself authorize external data transfer.

## 6. Legacy-memory boundary

The current `companion.memory` and `companion.deep_memory` stores predate this typed truth contract and contain mixed historical structures such as cached observations, emotional signals and heuristic food-response memory.

P0.2 does **not** claim those legacy snapshots are already migrated. Their classification/migration must be a separate focused lot with backward-compatible snapshot handling and regression evidence. Until then, legacy memory must not be treated as a new authoritative clinical fact source merely because this contract exists.

## 7. Permanent regression expectations

Tests must prove at minimum that:

- `MODEL_INFERENCE` cannot be persisted as patient fact or enter deterministic clinical logic;
- `USER_CLAIM` stays explicitly labeled while remaining available to deterministic triage/domain logic;
- deterministic derivations can feed approved logic but are not immutable patient facts;
- generative models cannot classify emergencies;
- diagnosis, prescription, dose calculation, treatment optimization and treatment change remain disabled;
- user-claim/preference writes remain confirmation-gated;
- the LLM gateway rejects forbidden generative capabilities before provider egress.
