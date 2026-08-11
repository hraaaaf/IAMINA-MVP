# IAmina — Current Architecture

> **Status:** CURRENT ARCHITECTURE CONTRACT
>
> This document separates **as-built reality** from **target direction**. It must not present planned migrations as already complete.
>
> Forward work: `docs/ROADMAP.md`  
> Decision history: `docs/adr/` + `docs/architecture/ARCHITECTURE-TIMELINE.md`

## 1. Product architecture in one sentence

IAmina is a **Flutter + Django modular monolith for one live diabetes companion**, with existing chassis/module seams, deterministic clinical/safety logic, offline-first data capture, a server-enforced AI egress authorization boundary, and legacy provider/auth integrations being migrated toward a MENA-focused sovereignty architecture.

The existence of platform seams does **not** mean IAmina is currently a multi-condition platform.

## 2. Product boundaries

### Live now

- One condition: diabetes.
- Flutter client for web/mobile.
- Django + django-ninja backend.
- Diabetes-specific clinical data, KPI logic, pattern detection, and companion context.
- Shared core contracts, safety registry/middleware, account/auth infrastructure, observability, and retention instrumentation.
- Legacy Firebase authentication bridge.
- Provider-specific AI/STT/vision/document adapters still exist.
- A central `core.ai_egress` boundary now authorizes live external model/media operations by patient, purpose, modality, and server-side consent.
- IAmina has an executable truth-provenance and capability/authority contract: generative models may narrate approved data but are not clinical decision authorities.
- CI blocks new direct external AI callsites that omit the central authorization assertion.

### Target direction

- MENA country-by-country/locale-by-locale rollout.
- Django-native identity as sovereignty-critical source of truth.
- Complete outbound AI/media policy contract with explicit payload allowlists, minimization/redaction, granular media consent, processor/subprocessor metadata, residency/retention/no-training terms, and timeout/failure policy.
- Provider-agnostic text/STT/vision architecture selected independently by benchmark.
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
- IAmina truth-provenance and capability/authority contracts;
- AI/media egress authorization policy;
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

Detailed implementation history remains available in git history and the immutable ADR/timeline record; obsolete forward plans are not kept as active-looking documents.

## 5. Safety decision flow

The current authority order is:

```text
patient input
  → deterministic preprocessing / normalization
  → deterministic emergency and safety gates
  → diabetes/domain analysis
  → approved structured result
  → optional external AI/media task
       → capability/authority check where routed through the shared LLM gateway
       → patient/purpose/modality egress scope
       → server-side consent authorization
       → payload minimization/redaction where implemented
       → provider call
  → output safety policy
  → patient UI
```

Generative AI must never be the authority for:

- whether an emergency is recognized;
- diagnosis;
- prescription;
- treatment/dose optimization;
- whether a model inference becomes patient truth;
- whether a prohibited payload may leave the system.

### P0-A safety boundary changes now as-built

- Cookie/session-authenticated API writes are no longer protected by a blanket `/api/` CSRF exemption.
- Bearer-token/bootstrap paths retain the narrow exemptions they require.
- Unit normalization covers legacy and registry-mounted module routes, including `/api/v1/diabetes/...`.
- Unexpected unit-normalization failures are fail-closed.
- Authoritative deterministic triage classification belongs to shared `core` safety ownership; compatibility shims may remain for historical imports, but core safety must not depend on the diabetes module.

### P0.2 truth and capability boundary now as-built

- `TruthRecord` distinguishes observed facts, explicit patient claims, deterministic derivations, preferences, conversational state and model inference.
- Model inference and conversational state cannot be persisted as patient clinical fact or used as deterministic clinical input merely because a model produced or repeated them.
- Explicit patient claims retain their provenance but may feed approved deterministic triage/domain logic; using a claim as input does not validate a diagnosis.
- The capability matrix permits generative explanation/summarization of approved data and clinician-question preparation, while emergency classification remains deterministic-only.
- Diagnosis, prescription, dose calculation, treatment optimization/change, model-inference promotion and autonomous clinical-record writes are disabled capabilities.
- `GatewayLLM` fails closed on a forbidden generative capability before provider egress.
- `doctor-brief` now uses the capability-aware gateway while preserving its structured JSON response contract.
- One legacy structured diabetes insight formatter still calls the provider abstraction directly after egress authorization; this bounded exception is tracked in `docs/TECHDEBT.md` and does not authorize diagnosis/prescription/treatment behavior.

## 6. AI / model boundary

### Current state after P0-B and P0.2

`core.ai_egress` is the central authorization layer for currently wired live external model/media operations.

It enforces before real egress:

- valid authenticated patient scope;
- registered purpose;
- declared/allowed modality;
- server-side consent from the patient profile.

Default-deny conditions include:

- no egress scope;
- missing patient consent record/consent;
- unknown purpose;
- modality not authorized for that purpose.

The boundary is intentionally **lazy**: entering a request scope does not itself require AI consent. Deterministic emergency/safety behavior can still complete for a patient who declined AI as long as no external provider call is attempted.

The shared text gateway additionally enforces the IAmina capability matrix before provider egress. This authority check is independent of consent/egress authorization: an allowed narrative capability can still be denied for missing egress consent, and egress consent never grants a forbidden medical capability.

Live call paths wired through this policy include the currently inventoried text/gateway, chat, summary/doctor-brief, STT/audio, vision/OCR, and document-processing flows.

CI contains an AI-egress anti-bypass gate so new direct model/provider callsites cannot silently omit the authorization assertion. P0.2 adds a focused anti-regression contract preventing the AI API/doctor-brief path from returning to direct text-provider access.

### Important remaining limitations

P0-B does **not** mean the complete sovereignty/data-egress program is finished.

Still required under P0-MENA-1:

- structured payload/field allowlists per purpose;
- uniformly enforced minimization/redaction contracts;
- purpose/modality-granular raw-media consent where required;
- processor/subprocessor and residency metadata;
- retention/no-training terms;
- timeout/failure/fallback policy;
- final removal/isolation of provider-specific seams.

P0.2 additionally leaves two bounded follow-ups:

- remove the structured diabetes formatter capability-gateway exception tracked in `docs/TECHDEBT.md`;
- classify/migrate legacy companion-memory snapshots before treating those stores as typed clinical truth.

Therefore the system is **egress-authorized**, and shared text-gateway calls are capability-bounded, but every legacy structured-provider seam is not yet claimed as migrated.

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

Raw audio/images/documents may disclose sensitive information even without explicit text fields, so media transmission requires an approved purpose and the consent/policy level defined by P0-MENA-1.

## 8. Authentication

### Current

Firebase-based identity/token handling remains present as legacy infrastructure.

The API safety hardening from P0-A distinguishes Bearer/bootstrap behavior from cookie/session CSRF behavior; it does **not** complete the Firebase → Django sovereignty migration.

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
- Normative clinical metrics require source/version, eligibility rules, and regression fixtures; SQLite-only success is insufficient evidence for PostgreSQL-specific raw SQL.
- Deterministic derived metrics/patterns remain derived truth and should be recomputed from authoritative source data rather than promoted to immutable patient facts.

## 11. Key invariants

| Invariant | Reason |
|---|---|
| Deterministic emergency gate before generative AI | Patient safety |
| Unit normalization before clinical/AI logic, fail-closed on unexpected normalization failure | Data integrity |
| Cookie/session API writes retain CSRF protection | Web/API security |
| No diagnosis/prescription/treatment optimization | Product/regulatory boundary |
| Model inference never silently becomes patient fact or clinical authority | Clinical truthfulness |
| Explicit patient claims remain labeled claims even when used by deterministic triage/domain logic | Provenance integrity |
| Forbidden generative capabilities fail closed before shared-gateway provider egress | AI authority boundary |
| Every live external model/media call requires sanctioned egress authorization | Privacy + sovereignty |
| Missing scope/consent/purpose/modality authorization denies egress | Default-deny safety |
| Default-deny sensitive outbound data/media | Data minimization |
| SQL-first KPI authority where ADR-0007 applies | Single analytical source of truth |
| `client_uuid` preserved | Offline sync idempotency |
| Native safety parity before locale enablement | MENA safety equivalence |
| No second condition before Retention Gate | Product discipline |

## 12. Documentation authority

- `docs/ROADMAP.md` — what happens next and recent closeout state.
- This file — current architecture + target boundaries.
- `docs/SPECS.md` — current capability/API contract.
- `docs/AMINA_TRUTH_CAPABILITY_CONTRACT.md` — detailed IAmina truth/authority vocabulary.
- `docs/TECHDEBT.md` — unresolved compromise only.
- `docs/adr/` — immutable decisions.
- `ARCHITECTURE-TIMELINE.md` — historical evolution.
- Git history — deleted obsolete implementation plans and prior snapshots.

Do not copy historical phase diaries or raw test counts into this document. Update it after a merged task only when the **as-built architecture** actually changed.