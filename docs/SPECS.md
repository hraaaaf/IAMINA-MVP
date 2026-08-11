# IAmina — Product and API Specifications

> **Purpose:** describe current user-facing capability and durable API/product contracts.
>
> **Not a roadmap:** planned work belongs in `docs/ROADMAP.md`.  
> **API source of truth:** generated OpenAPI + running code. This file summarizes intent and stable surfaces.

## 1. Product scope

IAmina is a **MENA-first diabetes companion**.

Current product boundaries:

- diabetes is the only live condition;
- no diagnosis;
- no prescription;
- no treatment/dose optimization;
- deterministic clinical/safety logic remains authoritative;
- generative AI is optional narration/media assistance, not clinical authority;
- country/dialect rollout is gated by safety parity and privacy/compliance readiness.

## 2. Client

Flutter is the only product frontend.

Core capabilities already represented in the application include:

- patient authentication/session flow;
- onboarding/profile;
- diabetes type/treatment context;
- unit preference;
- glucose logging;
- meal/context logging;
- insulin quantity logging as patient-entered data;
- exercise/sleep/stress/fatigue/illness context;
- offline-first Drift persistence + batch sync;
- edit/delete journal entries;
- dashboard KPIs and AGP-style visualization;
- IAmina companion/chat surfaces;
- document/import and image/audio-assisted flows where currently wired.

### Metabolic-event logging contract

The add-log surface records **observed or patient-entered facts**. It does not convert a single reading, meal category or entered insulin quantity into autonomous clinical advice.

Current invariants:

- no glucose value is fabricated before the patient enters one;
- a single non-low reading is not labeled as being inside a personal target unless an authoritative personalized target contract exists;
- low-glucose entry safety distinguishes `<54 mg/dL` from `54–69 mg/dL` deterministically before persistence;
- meal logging does not manufacture carbohydrate grams, exact glycaemic-index values or a meal-impact score from categorical food metadata;
- insulin on this surface is the quantity the patient says was already taken, not a suggested, scored or optimized dose;
- saving a log does not automatically request a generative clinical verdict about that reading;
- `client_uuid` remains the offline-sync idempotency key.

Media-assisted meal/glucose capture and voice-assisted notes may exist elsewhere in the codebase, but they are not a license to bypass the outbound AI/media authorization contract. If re-exposed on metabolic-event capture, the user must retain confirmation/correction control and any external egress must pass the sanctioned patient/purpose/modality/consent and minimization boundary.

The existence of an input field does not authorize IAmina to advise a dose or modify treatment.

### Context intelligence v2 contract

- illness, unusual stress, physical activity and poor sleep are optional patient-entered observations;
- absence of a context selection means unknown/not reported and must not be converted into `no`, `good` or `ok`;
- Add Log exposes context progressively rather than repeatedly asking all context questions;
- Edit Log may correct these observations without rewriting unrelated meal, time or insulin facts;
- offline sync transmits only explicitly recorded context; legacy explicit fatigue remains compatible, while unreported fatigue does not become fabricated `ok`;
- Journal history may display a context only when it was actually recorded;
- context data does not authorize causal inference, clinical scoring, treatment optimization or insulin-dose advice.

### Ramadan mode v2 contract

- Ramadan is an optional profile-level period configured explicitly by the patient; the product does not infer it from country, calendar, location, time of day or meal timing;
- the period is valid only as both a start date and an end date with `start <= end`; missing, partial or inverted periods fail closed;
- an event whose logged date falls inside the configured period uses the meal vocabulary **Suhoor / Iftar / Snack / Other**; events outside it retain the standard meal vocabulary;
- no Ramadan meal is preselected, and selecting or displaying Suhoor/Iftar does not imply that the patient fasted or completed a fast;
- the profile period is context only: it does not change glucose thresholds, calculate medication/insulin doses, optimize treatment, diagnose, or generate autonomous treatment advice;
- Django persistence adds nullable profile dates through migration `0023`; Drift v8→v9 adds the same nullable local profile dates without rewriting existing Journal rows or their `client_uuid` values;
- local Ramadan persistence is update-only: if no local medical profile exists, configuring Ramadan must not create one or materialize default diabetes type, treatment, unit or glucose-target values; existing clinical profile fields must remain unchanged when the Ramadan period is updated;
- save feedback distinguishes local+server success, local-only persistence, server-only persistence and total failure instead of claiming a storage state that did not occur;
- the legacy per-log `ramadan_mode` field is preserved for compatibility and is not retrospectively promoted into authoritative fasting evidence;
- FR/EN/AR localization is supported for this capability, with Arabic governed by the application's RTL contract.

### Personal metabolic response contract

- personal-response patterns are deterministic derived observations recalculated from authoritative synchronized source logs; they are not persisted as clinical facts;
- a context pattern may use only explicitly recorded positive states; historical `no`, `good` or `ok` values must not be treated as a negative/control cohort because older schemas may have materialized defaults;
- a meal pattern requires an explicit `post_meal` measurement context plus an explicit meal type;
- demo rows are excluded and patient scope is derived from the authenticated server identity, never a client-supplied patient identifier;
- the analysis window is bounded to 90 days and the UI/API disclose that only server-synchronized logs are analyzed;
- pattern eligibility requires at least 3 matching observations across at least 2 distinct days; insufficient repetition fails closed instead of producing a pattern;
- each pattern may expose observation count, distinct-day count, its median glucose and the median of all eligible synchronized readings in the same window; no causal delta or predicted glucose is produced;
- `limited` / `moderate` / `strong` describe only product repeatability/evidence density. They are not a probability, p-value, statistical significance test, diagnosis or clinical confidence score;
- the patient-facing surface must state that association does not establish cause and must not guide treatment or dosing;
- no pattern detector may produce treatment optimization, insulin-dose advice, diagnosis or autonomous clinical recommendation;
- the Journal shows one strongest pattern by default and makes secondary patterns explicitly expandable so longitudinal context does not crowd out the primary history task.


### Post-save experience contract

- a successful Add Log write transitions to a persistent factual receipt only after the local Drift insertion has completed successfully;
- the receipt may restate only the facts from that saved entry: glucose, timestamp and explicitly entered measurement context, meal, already-taken insulin and additional context observations;
- local persistence is described narrowly as saved on the device; this receipt does not imply server synchronization, external backup or provider processing;
- one saved reading must not trigger a good/bad glucose verdict, personal-target claim, prediction, causal explanation, AI analysis, diagnosis, treatment optimization or insulin-dose advice;
- P2-JOURNAL-8 longitudinal personal-response patterns remain separate from the immediate receipt and retain their own minimum-evidence contract;
- after successful insertion, the previous draft is cleared before another entry is started so prior meal/context/insulin facts cannot be silently reused;
- the user can explicitly view the saved entry in Journal, start another reading, or finish; on compact screens those actions remain persistently reachable while receipt detail may scroll;
- FR/EN/AR copy follows the application localization contract and numeric insulin values remain LTR under Arabic RTL.

### Insulin logging v2 contract

- `insulin_units` is patient-entered historical fact: the quantity the patient reports having already administered;
- the field is nullable and decimal-preserving across create, edit, history and sync; the client does not coerce an absent dose to `0`;
- the patient-facing client treats blank or zero input as no administered dose, while negative API input is invalid;
- no preset units, increment/decrement stepper, dose score, calculator, correction suggestion or treatment optimization is exposed by Journal;
- editing the insulin value must preserve unrelated meal/context data and legacy Ramadan state;
- batch synchronization treats a later snapshot with the same `client_uuid` and same patient as an idempotent update, not a silent no-op; a `client_uuid` owned by another patient must fail closed;
- no insulin log may be transformed into autonomous dosing advice.

### Nutrition Data v2 contract

- patient-facing numeric carbohydrate information requires an explicit versioned source and a defensible food/preparation match;
- unsupported foods remain loggable while numeric nutrition fails closed;
- patient-confirmed natural portions or grams are stored as observations, while derived nutrition is recalculated from the versioned catalogue rather than persisted as immutable truth;
- each persisted portion must reference a selected structured meal item; duplicate or orphan portion records are rejected at the API boundary;
- natural household portions are never silently converted to grams unless a compatible source-backed weight exists;
- uncertainty is shown as a range when the authoritative source set supports a range rather than a defensible exact value;
- Arabic numeric ranges preserve low-to-high order under RTL;
- nutrition output does not produce glycaemic-index scoring, meal-impact scoring, treatment changes or insulin-dose recommendations.

Current curated source/provenance details live in `docs/NUTRITION_DATA_SOURCES.md`.

## 3. Locale contract

### Current legacy representation

The codebase contains existing language handling such as French, Arabic, and Moroccan Darija paths.

### Target MENA contract

The product must model separately:

- country/region;
- UI language(s);
- response language;
- dialect(s);
- script/transliteration preference;
- units;
- time zone;
- emergency-resource jurisdiction.

Location may suggest choices only. User confirmation is required for language/dialect behavior.

No locale/dialect is enabled for a real-patient pilot until it passes:

- native-speaker review;
- deterministic safety parity;
- mixed-language/transliteration testing where relevant;
- RTL/script UX coverage where relevant;
- validated emergency resources;
- privacy/compliance readiness.

## 4. Authentication and API write security

### Current

A Firebase JWT bridge exists in the current codebase and maps authenticated identities into Django users/accounts.

P0-A hardened API write security:

- cookie/session-authenticated API writes are not covered by a blanket `/api/` CSRF exemption;
- narrow Bearer/bootstrap exemptions remain where required;
- protected clinical routes use fail-closed unit normalization across legacy and namespaced module paths.

### Target

Django-native authentication becomes the sovereignty-critical source of truth under P0-MENA-3.

Do not remove Firebase dependencies until account-preserving migration, reconciliation, and rollback are proven.

## 5. Diabetes data contract

The diabetes domain owns diabetes-specific clinical data and analytics.

Representative data includes:

- glucose readings;
- logging timestamp/source;
- meal context/items;
- patient-entered insulin quantity where applicable;
- exercise/sleep/stress/fatigue/illness context;
- diabetes-specific profile fields;
- imported CGM/document/lab-derived data where supported.

`client_uuid` remains the offline-sync idempotency key.

## 6. Analytics contract

Representative diabetes analytics include:

- Time in Range;
- GMI estimation with confidence handling;
- coefficient of variation;
- AGP percentile visualization/data;
- GRI and other currently implemented diabetes metrics/patterns.

Where ADR-0007 applies, KPI authority is SQL-first.

Analytics must distinguish between:

- measured/imported data;
- deterministic calculated metrics;
- detected patterns;
- AI-generated wording.

A narrative model must never silently become the source of truth for a numeric KPI or clinical rule.

Durable analytics requirements:

- formulas/thresholds must have a documented normative source/version;
- metric eligibility and data-sufficiency rules must be explicit;
- a metric must not be exposed outside the data modality/population supported by its definition;
- production-authoritative PostgreSQL SQL must be validated on PostgreSQL, not inferred from SQLite fallback success.

## 7. IAmina truth and capability contract

The chassis uses explicit provenance classes for information consumed or remembered by IAmina:

- `OBSERVED_FACT` — measured/imported/explicitly recorded observation from an authoritative product source;
- `USER_CLAIM` — information explicitly reported by the patient and retained as a claim rather than silently validated;
- `DETERMINISTIC_DERIVATION` — KPI/pattern/result produced by approved deterministic logic;
- `PREFERENCE` — explicit product preference;
- `CONVERSATIONAL_STATE` — transient dialogue/relationship state;
- `MODEL_INFERENCE` — hypothesis/interpretation produced by a generative model.

Persistence/authority invariants:

- model inference and conversational state must not become patient clinical facts;
- model inference must not enter deterministic clinical decision logic;
- patient claims may feed approved deterministic triage/domain logic while remaining explicitly claims;
- deterministic derivations should be recomputed from source truth rather than promoted to immutable patient facts;
- explicit user-claim/preference writes require user confirmation.

Generative models are allowed to explain/summarize approved data, verbalize already-detected deterministic patterns and help prepare questions for a clinician. They are not allowed to classify emergencies, diagnose, prescribe, calculate doses, optimize/change treatment, promote model inference to patient fact or write clinical records autonomously.

`GatewayLLM` enforces the generative capability check before provider egress. `doctor-brief` uses `SUMMARIZE_APPROVED_DATA`, and the structured diabetes insight formatter uses `SURFACE_DETERMINISTIC_PATTERN`; both preserve their existing structured response/fallback contracts behind the shared capability-aware gateway.

Detailed semantics: `docs/AMINA_TRUTH_CAPABILITY_CONTRACT.md`.

## 8. Safety contract

### Emergency handling

Emergency/high-severity recognition and routing must be deterministic and upstream of generative AI.

Authoritative deterministic triage belongs to shared safety/core ownership rather than a reverse dependency from core into the diabetes module.

### Unit normalization

Clinical input normalization is upstream of domain/AI logic on protected routes.

- legacy and `/api/v1/{module}/...` namespaced routes must not diverge in unit-safety coverage;
- unexpected normalization errors fail closed rather than passing an unvalidated clinical payload onward.

### Treatment boundary

IAmina may:

- explain logged trends in plain language;
- surface deterministic patterns/metrics;
- encourage appropriate professional follow-up;
- provide pre-approved safety information.

IAmina must not:

- diagnose a condition;
- prescribe medication;
- calculate or recommend an insulin/medication dose;
- instruct a patient to change treatment;
- use a generative model as the authority for emergency classification.

## 9. AI / model contract

### Current enforced capability after P0-B

Currently wired live external AI/model/media operations use a central server-side authorization boundary.

Before real external egress, the boundary requires:

- authenticated patient scope;
- registered purpose;
- declared/authorized modality;
- server-side patient AI consent.

The following fail closed:

- no active egress scope;
- missing consent record or no consent;
- unknown purpose;
- modality not allowed for the purpose.

The authorization is evaluated lazily at actual provider egress so deterministic emergency/safety behavior remains available when AI consent is absent, provided no external call is attempted.

For shared text-gateway calls, P0.2 adds a separate authority check: egress permission does not grant a forbidden clinical capability, and an allowed narrative capability still requires the ordinary egress/consent boundary.

Currently inventoried/wired surfaces include text/gateway narration, chat, summary/doctor brief, structured diabetes insight formatting, STT/audio, vision/OCR, and document-processing paths.

CI prevents new direct external model/provider callsites from omitting the central authorization assertion. Focused IAmina tests additionally prevent the AI API/doctor-brief and structured diabetes formatter surfaces from reverting to direct `get_llm()` access.

### Remaining target contract

The authorization layer is not yet the complete sovereignty contract. P0-MENA-1 must still enforce consistently:

- allowlisted payload fields/media per purpose;
- minimization/redaction;
- purpose/modality-granular media consent where required;
- processor/subprocessor metadata;
- residency and retention/no-training terms;
- timeout/failure/fallback policy.

Provider selection is per modality and must follow the P0-MENA-4 benchmark.

## 10. API surface — summary

Current code exposes versioned `/api/v1/` routes. Representative surfaces include:

### Account/profile

- authentication bridge/current auth endpoints;
- profile read/update;
- consent read/update/revoke;
- account deletion.

### Diabetes logs/sync

- list/create/read/update/delete logs;
- batch offline sync;
- KPI/analytics endpoints.

### Import/media

Current code includes flows for some combination of:

- LibreLink/CSV import;
- document ingest/confirm;
- image/OCR-assisted capture;
- audio transcription/voice input.

External model/media portions of these flows must pass the P0-B authorization boundary and remain subject to the unfinished P0-MENA-1 payload/media policy.

### IAmina companion

Current code includes surfaces for:

- summary;
- doctor-facing brief/report-style output;
- chat;
- streaming chat;
- voice/transcription;
- image-assisted analysis where wired.

All such endpoints must obey the same deterministic safety and no-prescription boundaries.

## 11. Offline-first contract

- Flutter/Drift may persist local records before server sync.
- Sync must be idempotent via stable client identifiers.
- Server-side authority and conflict behavior must be explicit for edited/deleted records.
- Safety-sensitive decisions must not rely on stale local-only state without explicit handling.

## 12. Observability and retention

The backend contains observability/retention foundations for events and cohort metrics including D90.

Retention instrumentation is a business/product decision tool, not a clinical score.

Do not expand disease/module scope before the Retention Gate in `docs/ROADMAP.md` passes.

## 13. Specification maintenance

Update this file only for durable capability or contract changes.

After a merged task, update this file during docs closeout **only when the current capability/API contract actually changed**.

Do not put here:

- sprint checklists;
- raw test counts;
- provider shopping notes;
- completed historical phase narratives;
- speculative features.

Use:

- `ROADMAP.md` for forward work and recent closeout state;
- `ARCHITECTURE.md` for boundaries;
- `AMINA_TRUTH_CAPABILITY_CONTRACT.md` for the detailed companion truth/authority vocabulary;
- `TECHDEBT.md` for unresolved compromise;
- ADRs for durable decisions;
- OpenAPI for exact endpoint schemas.
