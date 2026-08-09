# IAmina — Clinical Data and Safety Plan

> **Status:** CURRENT SAFETY/DATA CONTRACT
>
> This file replaces the older implementation backlog that mixed product scope, clinical guidance, detector ideas, and treatment-oriented recommendations.
>
> IAmina is a **diabetes companion**. It does not diagnose, prescribe, calculate medication doses, or optimize treatment.

## 1. Clinical authority model

IAmina must keep four layers distinct:

1. **Observed / patient-entered data**  
   Glucose readings, timestamps, meals/context, imported device/lab data, patient-entered treatment context.

2. **Deterministic calculated metrics**  
   Metrics produced by validated formulas/queries from eligible data.

3. **Deterministic detected patterns / safety rules**  
   Rule-based outputs with explicit evidence requirements and test coverage.

4. **Narrative presentation**  
   Human-readable wording produced from approved structured results. A generative model may help verbalize; it does not become the source of clinical truth.

Every patient-facing output should be traceable to one of these layers.

## 2. Product safety boundary

### Allowed

IAmina may:

- help patients record and organize diabetes-related data;
- display validated metrics and trends;
- surface deterministic patterns when evidence requirements are met;
- explain results in accessible language;
- encourage appropriate professional follow-up;
- provide pre-approved safety information and emergency routing.

### Not allowed without a separate explicit product/regulatory decision

IAmina must not:

- diagnose a disease or complication;
- prescribe medication;
- recommend or calculate an insulin/medication dose;
- tell a patient to start, stop, increase, or decrease treatment;
- claim that a model prediction replaces laboratory/clinical assessment;
- use an LLM as the authority for emergency classification.

## 3. Data-quality contract

Every metric/pattern must define:

- required input fields;
- minimum data sufficiency;
- accepted sources;
- time window;
- unit normalization;
- missing-data behavior;
- confidence/eligibility state;
- deterministic fallback when evidence is insufficient;
- source/version of the clinical definition;
- tests for edge cases and invalid data.

Do not hide insufficient data behind confident prose.

### Nutrition-derived observations

Nutrition values are deterministic derived data, not treatment authority. A patient-facing number requires source/version provenance, compatible food identity/preparation and an explicit portion basis. If those requirements are not met, numeric nutrition must fail closed. Patient-entered portion observations may be stored, but derived carbohydrate values remain recalculable from the versioned catalogue and must not be treated as immutable clinical facts. Uncertainty must remain visible when the source supports only a range. Nutrition-derived output must not be converted into an insulin dose, treatment adjustment, diagnosis or autonomous recommendation.

## 4. Metrics

Current/representative diabetes analytics include metrics such as:

- Time in Range;
- glucose mean/distribution metrics;
- GMI estimation where eligible;
- coefficient of variation;
- AGP percentile representation;
- GRI and other implemented diabetes analytics.

Rules:

- KPI authority remains SQL-first where ADR-0007 applies.
- Units are normalized before calculation and unexpected normalization failure must fail closed on protected clinical routes.
- Confidence/eligibility must be explicit when a metric requires sufficient data density/duration.
- A narrative model may explain a metric but must not recalculate or override it.
- Clinical thresholds/formulas must be versioned, cited in implementation documentation/tests, and reviewed when standards change.
- A metric must not be presented outside the population/data modality for which its normative definition is valid.
- PostgreSQL-specific analytical SQL requires PostgreSQL validation; SQLite fallback success alone is not certification.

## 5. Pattern detection

A detector must be treated as a deterministic product rule, not as free-form AI interpretation.

Each detector requires:

- a precise rule specification;
- minimum evidence criteria;
- positive and negative fixtures;
- unit and time-zone handling;
- false-positive analysis;
- treatment-context-safe wording;
- locale safety parity for every enabled patient language/dialect.

Do not add treatment-adjustment logic to pattern detectors.

## 6. Treatment and insulin data

IAmina may store patient-entered treatment/insulin context when needed for logging and interpretation. In Journal, an insulin quantity is an **observed historical fact**: the amount the patient reports was already administered. It is not a recommendation, target, correction factor or optimization output.

Durable insulin-data requirements:

- absence of a reported dose remains null rather than being fabricated as `0`;
- decimal patient-entered quantities must not be silently rounded in create, edit, history or sync;
- negative administered-dose input is invalid;
- editing an insulin quantity must not rewrite unrelated meal/context observations;
- offline reconciliation may update the same patient's log through its stable `client_uuid`, but cross-patient UUID ownership must fail closed;
- no preset, score, calculator, suggested unit or treatment-adjustment logic may be inferred from logged insulin data.

That data must not be used to generate autonomous dose recommendations or treatment changes.

Requests asking IAmina to decide or adjust dosing/treatment must follow deterministic refusal/safety behavior and appropriate professional follow-up guidance defined by the product safety policy.

## 7. Emergency / high-severity safety

Emergency handling is a deterministic pre-model gate.

Requirements:

- no generative model is required to decide whether the emergency path triggers;
- authoritative deterministic triage logic belongs on the shared safety side of the architecture boundary, not behind a disease-module dependency;
- enabled languages/dialects must have safety-equivalent coverage;
- mixed-language and transliterated input must be tested where relevant;
- country-specific emergency resources must be validated before locale launch;
- emergency events must follow the operating model in the roadmap, including monitored escalation where required.

## 8. Input/unit safety

Clinical inputs must reach domain/AI logic only after deterministic normalization and validation.

Current invariant after P0-A:

- protected legacy and registry-mounted module routes are covered by the unit guard;
- namespaced routes such as `/api/v1/diabetes/...` must not bypass normalization;
- unexpected normalization failures are fail-closed rather than allowing unvalidated clinical payloads to continue.

## 9. MENA locale safety

Clinical meaning and safety must remain equivalent across enabled locales.

For every pilot language/dialect:

- native-speaker review is required;
- dangerous ambiguity and common orthographic variants must be covered by the safety corpus;
- MSA/English/French deterministic fallback behavior must be defined;
- RTL/script rendering must be validated where applicable;
- location may suggest locale choices but never silently determines them.

A translation being linguistically correct is not sufficient; the safety intent must remain equivalent.

## 10. AI/model use with clinical data

### Current enforced authorization layer

P0-B introduced a central server-side AI egress authorization boundary for currently wired live external operations.

Before a real external model/media call, the system requires:

- an authenticated patient scope;
- a registered purpose;
- an authorized modality;
- server-side patient AI consent.

The following conditions deny egress by default:

- no active egress scope;
- missing consent record or no consent;
- unknown purpose;
- undeclared/unauthorized modality.

This authorization is intentionally evaluated at real egress time so deterministic emergency/safety handling remains available even when a patient declines AI.

### Data minimization contract still being completed

Authorization alone does **not** prove that every outbound payload is sufficiently minimized.

External models may receive only the minimum approved payload for an explicit purpose. Do not send by default:

- direct identity/contact fields;
- internal/external user identifiers;
- raw unrelated history;
- raw unrelated clinical logs;
- unrelated health data.

Raw audio/images/documents require stronger treatment because sensitive content can be embedded in the media itself.

Remaining P0 obligations include:

- explicit field/payload allowlists by purpose;
- uniformly enforced minimization/redaction;
- purpose/modality-granular raw-media consent where required;
- processor/subprocessor and residency metadata;
- retention/no-training terms;
- timeout/failure/fallback policy.

CI must prevent new live direct provider callsites from bypassing the sanctioned authorization boundary.

## 11. Clinical feature acceptance checklist

Before enabling a new metric, detector, or patient-facing clinical insight:

- [ ] deterministic definition exists;
- [ ] source/version is documented;
- [ ] data sufficiency and modality eligibility are explicit;
- [ ] unit/time handling is tested;
- [ ] PostgreSQL behavior is tested when production SQL differs from SQLite fallback;
- [ ] no diagnosis/prescription/treatment-optimization boundary is crossed;
- [ ] positive + negative + edge-case tests exist;
- [ ] patient wording is safe for relevant treatment contexts;
- [ ] every enabled locale has safety-equivalent reviewed wording/tests;
- [ ] outbound AI usage, if any, passes patient/purpose/modality/consent authorization;
- [ ] outbound AI payload, if any, is explicitly minimized/allowlisted for that purpose;
- [ ] fallback behavior is deterministic when AI/provider services fail.

## 12. Documentation closeout rule

After a merged clinical/safety task:

1. update `docs/ROADMAP.md` with the actual closeout state;
2. update this file only if the clinical/data/safety contract changed;
3. update `docs/SPECS.md` if a durable capability changed;
4. update `docs/architecture/ARCHITECTURE.md` if an as-built boundary changed;
5. remove or rewrite resolved debt in `docs/TECHDEBT.md`.

A code merge is not a complete closeout while canonical documentation still describes the previous behavior.

## 13. Backlog ownership

This file is not a feature backlog.

- New implementation work → `docs/ROADMAP.md`.
- Current capability → `docs/SPECS.md`.
- Architecture boundary → `docs/architecture/ARCHITECTURE.md`.
- Unresolved technical compromise → `docs/TECHDEBT.md`.

Do not reintroduce standalone clinical milestone lists here; they drift from the roadmap and can accidentally turn speculative guidance into apparent product requirements.
