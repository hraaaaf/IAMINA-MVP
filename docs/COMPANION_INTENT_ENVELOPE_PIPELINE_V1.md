# IAMINA — Companion Intent Envelope Pipeline V1

Status: **CANDIDATE — NOT RUNTIME-WIRED — NOT FROZEN**  
Branch: `feat/companion-intent-envelope-router`

## Goal

Replace unbounded phrase dictionaries with a scalable intent-understanding layer while preserving IAMINA's authority boundary:

> **IAMINA decides. The LLM classifies/formulates. IAMINA verifies.**

The LLM must never become the authority for safety, patient identity, database access, source selection, treatment, dose, diagnosis, or backend actions.

## Success criteria before freeze

- safety-critical requests are intercepted locally before any classifier call;
- provider-bound classifier input is deterministically minimized and never claims certified anonymity;
- known identifiers / precise dates / exact clinical values are removed or the call is denied;
- classifier has no tools, no DB, no patient object, no durable memory;
- classifier output is exactly `IntentEnvelope schema_version=1`;
- invalid / ambiguous / low-confidence output fails closed to local clarification;
- patient-data routes are read-only and deterministic;
- synthetic multilingual benchmark: JSON/schema validity 100%;
- safety interception 100%;
- unsafe patient-data authorization count = 0;
- route accuracy >= 95% target for freeze;
- exact-head CI green;
- no production/Vercel deployment before explicit owner authorization.

## Pipeline

```text
USER MESSAGE
    |
    v
[1] LOCAL INPUT SAFETY
    |-- urgent / crisis ----------------------> deterministic safety response
    |-- dose / prescription / treatment ------> deterministic clinical boundary
    |
    v
[2] EXISTING DETERMINISTIC FAST PATHS
    |-- already-known exact route -----------> local response
    |
    v
[3] LOCAL PRIVACY MINIMIZER
    |-- direct identifiers removed
    |-- exact dates/times coarsened
    |-- exact clinical values withheld
    |-- stable IDs / coordinates / explicit location fields removed
    |-- residual known risk -----------------> DENY classifier call
    |
    v
[4] INTENT-ONLY LLM
    |  no tools / no DB / no patient object / no memory
    |  input = minimized unresolved message only
    |  output = strict JSON IntentEnvelope V1 only
    |
    v
[5] ENVELOPE VALIDATOR
    |-- invalid schema ----------------------> local clarification
    |-- inconsistent fields -----------------> local clarification
    |-- high ambiguity ----------------------> local clarification
    |-- confidence below route threshold ----> local clarification
    |
    v
[6] BACKEND POLICY ROUTER
    |-- deterministic_local
    |-- deterministic_patient_data
    |-- conversational
    |-- clarify
    |
    v
[7] DATA / RESPONSE EXECUTION
    |-- patient data: canonical local source, read-only
    |-- conversational: no patient data unless separately authorized
    |
    v
[8] FINAL OUTPUT GUARD
    |
    v
USER RESPONSE
```

## IntentEnvelope V1

Exact keys only:

- `schema_version`
- `intent`
- `target`
- `operation`
- `needs_patient_data`
- `answer_mode`
- `confidence`
- `ambiguity`

No free-text reasoning field is permitted.

### Intent enum

- `meta_greeting`
- `meta_identity`
- `meta_capabilities`
- `conversation_recall`
- `patient_data_read`
- `patient_data_summary`
- `general_health_education`
- `clinician_prep`
- `casual_conversation`
- `emotional_support`
- `unknown`

### Exact semantic combinations

| Intent | Target | Operation | Patient data | Answer mode |
| --- | --- | --- | --- | --- |
| meta_greeting | conversation | chat | false | deterministic |
| meta_identity | none | explain | false | deterministic |
| meta_capabilities | none | explain | false | deterministic |
| conversation_recall | conversation | recall | false | deterministic |
| patient_data_read | patient target | read | true | deterministic |
| patient_data_summary | patient target | summarize | true | deterministic |
| general_health_education | none | explain | false | conversational |
| clinician_prep | none | prepare | false | conversational |
| casual_conversation | conversation | chat | false | conversational |
| emotional_support | conversation | chat | false | conversational |
| unknown | none | none | false | clarify |

## Patient targets

V1 keeps the same read-only patient-owned surface already certified by the Whole-App Context Router:

- glucose
- meal
- sleep
- stress
- treatment
- diabetes_type
- targets
- lab_document
- medications
- cgm
- proactive
- paired_meal

The classifier may propose the semantic target. It cannot read it. IAMINA resolves the canonical source after validation.

## Backend authority map — V1

The intent model never selects a database table, ORM query or executable function. It proposes only a semantic `target`. IAMINA owns the canonical source and execution policy:

| Intent target | Backend authority / canonical source |
| --- | --- |
| glucose | diabetes journal / governed monitoring read path |
| meal | patient journal meal history |
| sleep | patient journal sleep history |
| stress | patient journal stress history |
| treatment | DiabetesProfile recorded treatment |
| diabetes_type | DiabetesProfile recorded diabetes type |
| targets | DiabetesProfile configured range + provenance |
| lab_document | confirmed LabReport structured fields |
| medications | document persistence contract; no invented historical medication list |
| cgm | CGMReadingRecord |
| proactive | read-only proactive preview |
| paired_meal | deterministic paired-meal computation from explicit episode links |

The adapter from `IntentTarget` to these backend authorities may be improved without changing V1 semantics, but it may never grant a new authority, bypass patient scoping, or make the classifier choose the physical data source.

For `patient_data_summary`, the backend may summarize only facts already available through an approved deterministic/read-only authority. If no deterministic summary exists for that target, the route must clarify or fall back to the existing bounded deterministic read — never promote the LLM to patient-data authority.

## Confidence policy — candidate

- patient-data route: minimum `0.88`;
- meta/conversational route: minimum `0.78`;
- `ambiguity=high`: always clarify regardless of confidence;
- confidence is advisory and never overrides deterministic policy.

Thresholds are tunable before/after freeze. The existence of a confidence gate is frozen.

## Privacy terminology

The pipeline deliberately uses **minimized** / **de-identified candidate payload**, not “certified anonymous”.

**Important governance boundary:** minimization does not make an authenticated health message automatically non-patient data. Free text can retain re-identification context even after known direct identifiers, exact dates and exact measurements are removed. Therefore this V1 architecture and its synthetic benchmark do **not** authorize external intent classification for authenticated patient traffic. Production activation must separately satisfy the applicable processor/transfer/consent policy, or use a future locally-proven abstraction layer that does not transfer patient data.

`core/anonymization_gateway.py` explicitly keeps `certified_anonymous=False`.

A residual-risk check can deny the classifier call. No raw patient context, patient object, patient ID, DB result, or conversation database is supplied to the intent model.

## Prompt-injection boundary

The classifier receives the minimized message as untrusted data.

It has:
- zero tools;
- zero function calls;
- zero DB access;
- zero backend credentials;
- zero authority to select an action directly.

Even a valid classifier result is only an **untrusted proposal**. The backend schema validator and policy router derive the executable route.

## Failure behavior

No user-visible “technical error” for classifier failure.

Any of:
- provider unavailable;
- malformed JSON;
- unsupported enum;
- privacy minimization rejection;
- high ambiguity;
- low confidence;

becomes a local clarification route.

## Latency UX contract

Runtime target after integration:

- deterministic fast path: no classifier;
- unresolved classified path: display a neutral transient state such as **“IAMINA réfléchit…”** while classification runs;
- do not expose chain-of-thought or model reasoning;
- measured p50/p95 from benchmark before UI implementation.

No UI change is part of this candidate branch yet. Any future indicator follows the project UI protocol: BEFORE → goal → mockup → implementation → AFTER same viewports → comparison/tests.

## Freeze contract

After owner approval, V1 becomes **FROZEN**.

### Frozen invariants — may not be changed inside V1

1. Local safety runs before external classification.
2. External classifier has no tools, DB, patient object or backend action authority.
3. Provider-bound classifier text passes through deterministic privacy minimization.
4. The payload never self-certifies legal anonymity.
5. Intent model returns a strict, versioned envelope only.
6. The intent adapter never creates a network provider implicitly; an explicitly governed provider must be injected by the backend boundary.
7. Backend validates the envelope before use.
8. High ambiguity / invalid output fails closed.
9. Patient-data access remains canonical-source, read-only and deterministic.
10. Treatment/dose/diagnosis authority never moves to the LLM.
11. Final patient-visible output remains independently guarded.

### Improvements allowed inside V1

- model/provider selection for this bounded non-patient classifier;
- classifier prompt wording/examples;
- confidence thresholds;
- latency/caching optimizations that do not change semantics;
- additional synthetic/adversarial tests;
- additional intent aliases mapped to existing semantics;
- UI waiting-state copy/animation after visual certification.

### Requires V2 instead of modifying frozen V1

- new envelope keys with new authority;
- tools/function calling in the classifier;
- direct database access by the classifier;
- raw patient context sent for intent parsing;
- moving safety after the LLM;
- allowing the LLM to execute backend actions;
- changing patient-data routes from deterministic/read-only to generative authority.

## Evidence required to change status to FROZEN

1. Local unit/privacy/adversarial tests green.
2. Groq synthetic multilingual benchmark artifact reviewed.
3. Route accuracy >= 95%.
4. Unsafe patient-data authorizations = 0.
5. Safety interception = 100%.
6. Exact-head CI green.
7. Independent adversarial review completed.
8. Explicit owner approval to freeze V1.

Production integration and Vercel deployment are separate later gates.
