# IAmina — Truth & Capability Contract

> **Status:** chassis contract introduced by P0.2, extended to structured insight formatting by P0.3, and applied to legacy memory snapshots by P0.4.  
> **Scope:** IAmina companion reasoning, memory provenance and generative-model authority.  
> **Non-scope:** no new disease module, clinical threshold, diagnosis, prescription, treatment optimization or patient-facing UX.

## 1. Purpose

IAmina must distinguish what is **observed**, what the **patient reported**, what a **deterministic engine derived**, what is merely a **preference or conversational state**, what a **non-authoritative heuristic inferred**, and what a **generative model inferred**.

Neither heuristic nor generative inference may become a patient fact, clinical rule or durable clinical truth merely because it was plausible or repeated.

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
| `CONVERSATIONAL_STATE` | transient relationship/tone/dialogue/cache state | no clinical-fact persistence | no |
| `HEURISTIC_INFERENCE` | non-authoritative inference produced by a heuristic without an approved clinical derivation contract | no | no |
| `MODEL_INFERENCE` | hypothesis or interpretation produced by a generative model | no | no |

### Persistence rule

Patient-fact storage may contain observed facts, explicit user claims and explicit preferences. A deterministic derivation is recomputed from its source data rather than silently materialized as immutable fact. Conversational state, heuristic inference and model inference remain outside patient clinical truth.

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

## 6. Memory snapshot boundary

`companion.memory` and `companion.deep_memory` still use the existing condition-agnostic `SnapshotStore` and JSON persistence; P0.4 introduces no database schema migration.

Legacy unversioned snapshots are normalized into a canonical versioned shape on load/save. Snapshot JSON is treated as data only: truth classification is resolved from code in `companion.memory_truth` and persisted `truth_kinds` / `truth_provenance` metadata is ignored rather than trusted.

Memory rules:

- `last_concern` is retained as an explicit `USER_CLAIM`;
- cached statistics, tone, emotional signals, milestones, relationship/streak state and unknown legacy fields are retained as non-clinical `CONVERSATIONAL_STATE` rather than promoted to patient fact;
- unknown legacy fields are preserved outside active reasoning to avoid silent destructive migration;
- the historical `food_sensitivities` field was a single-entry / approximate-baseline heuristic, so it is `HEURISTIC_INFERENCE`, not a clinical derivation and not a generative-model inference;
- old food-sensitivity values are preserved only under `quarantined_heuristics`; active `food_sensitivities` is normalized empty;
- new log events no longer learn that heuristic, and quarantined values cannot select IAmina's `next_intention`.

Personal metabolic-response analysis remains the evidence-bounded deterministic Journal capability; legacy deep-memory heuristics are not upgraded into that evidence simply by migration.

## 7. Permanent regression expectations

Tests must prove at minimum that:

- `MODEL_INFERENCE` and `HEURISTIC_INFERENCE` cannot be persisted as patient fact or enter deterministic clinical logic;
- `USER_CLAIM` stays explicitly labeled while remaining available to deterministic triage/domain logic;
- deterministic derivations can feed approved logic but are not immutable patient facts;
- generative models cannot classify emergencies;
- diagnosis, prescription, dose calculation, treatment optimization and treatment change remain disabled;
- user-claim/preference writes remain confirmation-gated;
- the LLM gateway rejects forbidden generative capabilities before provider egress;
- `doctor-brief` and the structured diabetes insight formatter cannot regress to direct `get_llm()` provider access;
- unversioned legacy memory snapshots remain loadable without schema migration;
- snapshot-supplied truth metadata cannot override canonical classification;
- legacy food-sensitivity values are quarantined and cannot steer active companion intent.
