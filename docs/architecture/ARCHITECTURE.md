# IAmina — Current Architecture

> **Status:** CURRENT ARCHITECTURE CONTRACT
>
> This document separates **as-built reality** from **target direction**. It must not present planned migrations as already complete.
>
> Forward work: `docs/ROADMAP.md`  
> Decision history: `docs/adr/` + `docs/architecture/ARCHITECTURE-TIMELINE.md`

## 1. Product architecture in one sentence

IAmina is a **Flutter + Django modular monolith for one live diabetes companion**, with existing chassis/module seams, deterministic clinical/safety logic, offline-first data capture, and legacy provider/auth integrations being migrated toward a MENA-focused sovereignty architecture.

The existence of platform seams does **not** mean IAmina is currently a multi-condition platform.

## 2. Product boundaries

### Live now

- One condition: diabetes.
- Flutter client for web/mobile.
- Django + django-ninja backend.
- Diabetes-specific clinical data, KPI logic, pattern detection, and companion context.
- Shared core contracts, safety registry/middleware, account/auth infrastructure, observability, and retention instrumentation.
- Legacy Firebase authentication bridge.
- Legacy provider-specific AI/STT/vision/document call paths still exist.

### Target direction

- MENA country-by-country/locale-by-locale rollout.
- Django-native identity as sovereignty-critical source of truth.
- One enforceable outbound AI/media boundary.
- Provider-agnostic text/STT/vision architecture selected independently by benchmark.
- Explicit consent, minimization, redaction, retention, and processor metadata for outbound calls.
- No second condition until the Retention Gate passes.

## 3. Layer model

### 3.1 Flutter application

Responsibilities:

- patient-facing UX;
- onboarding/profile;
- diabetes logging and journal;
- dashboard/analytics presentation;
- companion conversation UI;
- offline-first Drift persistence and sync;
- locale/script/RTL presentation;
- auth/session client behavior.

Rules:

- Flutter is the only product frontend.
- No business-critical safety rule may exist only in the client.
- Location may suggest locale settings but must not silently choose clinical/safety behavior.

### 3.2 Django API / shared core

Shared core responsibilities include:

- account/identity contracts;
- authentication bridge/current auth surface;
- safety middleware/registries;
- shared module contracts;
- outbound AI/media policy boundary target;
- observability and retention instrumentation;
- account deletion/consent hooks;
- cross-cutting operational controls.

The core must not absorb diabetes-specific clinical logic merely to look more “platform-like.”

### 3.3 Diabetes module

The diabetes module owns:

- diabetes-specific patient profile extension;
- glucose/CGM/log data;
- diabetes KPI queries and analytics;
- diabetes clinical/pattern rules;
- diabetes-specific structured context;
- diabetes-specific API surfaces and domain behavior.

It must consume shared contracts without creating hidden reverse dependencies from core back into diabetes.

### 3.4 External services

Potential external categories:

- text generation;
- STT;
- vision/OCR/document extraction;
- authentication legacy dependencies;
- storage/hosting/observability processors.

No external AI/media provider is trusted by default. Provider selection and payload eligibility are separate decisions.

## 4. Chassis/module seams — what ADR-0008 means today

ADR-0008 introduced real extension seams, including concepts such as module manifests/contracts, patient identity separation, registry/router integration, and import-boundary enforcement.

These seams are **technical optionality**, not a product mandate to add diseases.

Current rule:

> Keep the seams healthy enough that future expansion is possible, but spend no roadmap budget on a second condition or broad plugin ecosystem before retention + payer evidence.

Detailed historical implementation plans belong in `platform-transformation-plan.md` and git history, not in this active architecture contract.

## 5. Safety decision flow

The intended authority order is:

```text
patient input
  → deterministic preprocessing / normalization
  → deterministic emergency and safety gates
  → diabetes/domain analysis
  → approved structured result
  → optional minimized AI verbalization/media task
  → output safety policy
  → patient UI
```

Generative AI must never be the authority for:

- whether an emergency is recognized;
- diagnosis;
- prescription;
- treatment/dose optimization;
- whether a prohibited payload may leave the system.

## 6. AI / model boundary

### Current state

The codebase still contains legacy provider-specific integrations and more than one type of model call path. Do **not** document the system as fully provider-agnostic or fully egress-controlled until P0-MENA-1 is complete.

### Target state

All external text/STT/vision/document calls must pass an enforceable boundary that records or enforces:

- purpose;
- modality;
- user consent/legal basis where required;
- allowed fields/media;
- minimization/redaction;
- provider + processor/subprocessor;
- retention/training terms;
- timeout/failure policy;
- audit/observability metadata that does not itself leak sensitive content.

Direct provider imports/calls outside sanctioned infrastructure should fail CI.

## 7. Data-egress policy

Default-deny for external model providers.

Do not send by default:

- names or contact information;
- internal/external account identifiers;
- national identifiers;
- full date of birth/address;
- raw unrelated conversation history;
- raw unrelated clinical logs;
- unrelated health data.

Raw audio/images may disclose sensitive information even without explicit text fields, so media transmission requires a separately approved flow.

## 8. Authentication

### Current

Firebase-based identity/token handling remains present as legacy infrastructure.

### Target

Django-native authentication/identity becomes sovereignty-critical source of truth with explicit lifecycle for:

- account creation/invite;
- verification;
- sessions/tokens;
- password reset/recovery;
- abuse controls/rate limiting;
- deletion/export;
- staff/professional strong authentication.

Migration must preserve account identity and provide reconciliation + rollback before Firebase dependencies are removed.

## 9. Locale architecture

Locale is not one `language` field.

Model separately:

- country/region;
- UI language(s);
- preferred response language;
- dialect(s);
- script/transliteration preference;
- unit system;
- time zone;
- emergency-resource jurisdiction.

Location may prefill suggestions only.

A locale/dialect is disabled for patient pilot until it has:

- deterministic fallback behavior;
- native-speaker safety review;
- high-severity safety parity tests;
- mixed-language/transliteration coverage where relevant;
- validated emergency resources;
- RTL/script UX coverage where relevant;
- privacy/compliance readiness.

## 10. Data and analytics

- PostgreSQL is the authoritative target outside lightweight local fallback.
- Redis is used for cache/ephemeral coordination where configured.
- Drift provides offline-first local persistence on Flutter.
- `client_uuid` is the sync idempotency key and must not be repurposed.
- KPI calculations covered by ADR-0007 remain SQL-first.
- Clinical data ownership stays inside the diabetes domain unless a clearly shared concept is proven.

## 11. Key invariants

| Invariant | Reason |
|---|---|
| Deterministic emergency gate before generative AI | Patient safety |
| Unit normalization before clinical/AI logic | Data integrity |
| No diagnosis/prescription/treatment optimization | Product/regulatory boundary |
| One sanctioned outbound provider boundary | Privacy + sovereignty |
| Default-deny sensitive outbound data/media | Data minimization |
| SQL-first KPI authority where ADR-0007 applies | Single analytical source of truth |
| `client_uuid` preserved | Offline sync idempotency |
| Native safety parity before locale enablement | MENA safety equivalence |
| No second condition before Retention Gate | Product discipline |

## 12. Documentation authority

- `docs/ROADMAP.md` — what happens next.
- This file — current architecture + target boundaries.
- `docs/SPECS.md` — current capability/API contract.
- `docs/adr/` — immutable decisions.
- `ARCHITECTURE-TIMELINE.md` — historical evolution.
- `platform-transformation-plan.md` — archived implementation record only.

Do not copy historical phase status or test counts into this document.
