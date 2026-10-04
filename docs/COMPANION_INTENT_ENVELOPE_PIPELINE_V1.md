# IAMINA — Companion Intent Envelope Pipeline V1

Status: **FROZEN — NOT RUNTIME-WIRED**
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

Exact model-output keys only:

- `schema_version`
- `intent`
- `target`
- `confidence`
- `ambiguity`

No free-text reasoning, operation, patient-data permission, answer mode, tool call, or reply field is permitted.

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

| Intent | Model target | Backend-derived route semantics |
| --- | --- | --- |
| meta_greeting | conversation | deterministic local |
| meta_identity | none | deterministic local |
| meta_capabilities | none | deterministic local |
| conversation_recall | conversation | deterministic local recall |
| patient_data_read | patient target | read-only deterministic patient-data route |
| patient_data_summary | patient target | deterministic patient-data summary when a bounded authority exists; otherwise clarify/fallback |
| general_health_education | none | conversational candidate, no patient-data authority |
| clinician_prep | none | conversational candidate, no patient-data authority |
| casual_conversation | conversation | conversational candidate, no patient-data authority |
| emotional_support | conversation | conversational candidate, no patient-data authority |
| unknown | none | clarify |

`operation`, `needs_patient_data` and `answer_mode` are deliberately **not model outputs**. IAMINA derives those semantics from the validated intent and target.

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
- measured strict-runtime latency samples plus semantic-batch latency before UI implementation.

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
12. An intent or backend route decision never grants external model egress. Any downstream narrator must pass its own independent purpose/consent/processor/payload authorization before network use.

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

## Independent adversarial review — pre-freeze findings

The pre-freeze review challenged the candidate from four directions:

1. **Privacy residue** — an existing email-boundary regex failed when an email address was immediately followed by sentence punctuation. The DLP, pseudonymizer and anonymization gateway were aligned and regression-tested.
2. **Authority confusion** — a conversational or patient-data intent could be misread as permission for downstream external egress. V1 now states explicitly that intent routing never grants egress; every later external narrator requires its own independent authorization.
3. **False-positive patient reads** — negative benchmark cases now cover health terms used in emotional support, generic education, capabilities and clinician-prep requests where the user explicitly says not to open their record.
4. **Structured-output benchmark harness** — strict JSON Schema unit calls work, but multi-case strict-schema batching introduced a vendor/harness failure that does not exist in the real runtime. Final certification therefore separates concerns: one quota-aware JSON Object Mode batch measures semantic quality across all non-safety cases; because JSON Object Mode is not schema-typed, the evaluation harness may normalize a numeric confidence string such as `"0.97"` to `0.97`, counts every such coercion, then validates the normalized item through `IntentEnvelope.from_json`. Nonnumeric confidence strings still fail. The production/runtime parser remains type-strict and performs no coercion. Two unitary strict JSON Schema calls exercise the real runtime contract at the unchanged 384-token ceiling. Total external calls: 3 maximum.

No runtime patient path is wired by this candidate PR. Changed-files inspection excludes the chat API, `conversation.py`, and the clinical engine.

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


## Freeze record — 2026-10-04

Owner approval: **APPROVED — FREEZE**.

Frozen against certification commit `40a3c668e96da8070f87f6f38942a4fd99506c48` after reconciliation with `main@20b838ab0579fc2862c3131a66cf737060b48f73` through integration merge `b49f58fa42cbc9195d628426f90e60e19fa50418`.

Pre-freeze evidence:

- deterministic/local certification: green in run `37230784641`;
- Companion real-chat E2E: green in run `37230787529`;
- exhaustive multilingual certification: run `37231553138` green on exact HEAD `40a3c668e96da8070f87f6f38942a4fd99506c48`;
- exhaustive matrix: 125 cases across FR, EN, Arabic, Darija Latin and Darija Arabic;
- route accuracy: 100%;
- intent accuracy: 100%;
- target accuracy: 100%;
- safety interception: 100%;
- unsafe patient-data authorizations: 0;
- schema errors: 0;
- strict-runtime errors: 0;
- batch failures: 0;
- failed cases: 0;
- artifact: `intent-envelope-exhaustive`, artifact ID `11314530753`, SHA-256 `7b9d71b1d40ab868c3caf7fdfaf5b27ca52353954aa61731c201d8e67234045f`.

Freeze means the V1 contract and invariants above are locked. It does **not** authorize production runtime wiring, patient-data egress, PR-to-production merge, or Vercel deployment. Those remain separate gates.
