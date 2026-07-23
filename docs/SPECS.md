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

The existence of an input field does not authorize IAmina to advise a dose or modify treatment.

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

## 4. Authentication

### Current

A Firebase JWT bridge exists in the current codebase and maps authenticated identities into Django users/accounts.

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

## 7. Safety contract

### Emergency handling

Emergency/high-severity recognition and routing must be deterministic and upstream of generative AI.

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

## 8. AI / model contract

### Current reality

Legacy Gemini/provider-specific call paths exist for text and some media/document flows. The system must not be documented as fully provider-agnostic until P0-MENA-1 is complete.

### Target contract

Every external text/STT/vision/document call passes one sanctioned outbound boundary with:

- purpose;
- modality;
- consent/legal basis where required;
- allowlisted payload;
- minimization/redaction;
- processor/subprocessor metadata;
- retention/training terms;
- timeout/failure/fallback policy.

Provider selection is per modality and must follow the P0-MENA-4 benchmark.

## 9. API surface — summary

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

These flows are subject to P0-MENA-1 outbound-media policy and may be disabled until approved.

### IAmina companion

Current code includes surfaces for:

- summary;
- doctor-facing brief/report-style output;
- chat;
- streaming chat;
- voice/transcription;
- image-assisted analysis where wired.

All such endpoints must obey the same deterministic safety and no-prescription boundaries.

## 10. Offline-first contract

- Flutter/Drift may persist local records before server sync.
- Sync must be idempotent via stable client identifiers.
- Server-side authority and conflict behavior must be explicit for edited/deleted records.
- Safety-sensitive decisions must not rely on stale local-only state without explicit handling.

## 11. Observability and retention

The backend contains observability/retention foundations for events and cohort metrics including D90.

Retention instrumentation is a business/product decision tool, not a clinical score.

Do not expand disease/module scope before the Retention Gate in `docs/ROADMAP.md` passes.

## 12. Specification maintenance

Update this file only for durable capability or contract changes.

Do not put here:

- sprint checklists;
- commit hashes;
- exact test counts;
- provider shopping notes;
- completed historical phase narratives;
- speculative features.

Use:

- `ROADMAP.md` for forward work;
- `ARCHITECTURE.md` for boundaries;
- ADRs for decisions;
- OpenAPI for exact endpoint schemas.
