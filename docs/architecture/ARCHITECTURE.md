# IAmina — Current Architecture

> **Status:** CURRENT ARCHITECTURE CONTRACT
>
> This document separates **as-built reality** from **target direction**. It must not present planned migrations as already complete.
>
> Forward work: `docs/ROADMAP.md`  
> Decision history: `docs/adr/` + `docs/architecture/ARCHITECTURE-TIMELINE.md`

## 1. Product architecture in one sentence

IAmina is a **Flutter + Django modular monolith for one live diabetes companion**, with existing chassis/module seams, deterministic clinical/safety logic, offline-first data capture, Django-owned auth/token flows with guarded legacy migration compatibility, and a server-enforced AI/data-egress governance boundary for external model/media operations.

The existence of platform seams does **not** mean IAmina is currently a multi-condition platform.

## 2. Product boundaries

### Live now

- One condition: diabetes.
- Flutter client for web/mobile.
- Django + django-ninja backend.
- Diabetes-specific clinical data, KPI logic, pattern detection, and companion context.
- Shared core contracts, safety registry/middleware, account/auth infrastructure, observability, and retention instrumentation.
- Django-owned registration/login/logout, signed IAMINA bearer-token flows, revocation and password lifecycle; controlled Firebase migration/link/unlink compatibility remains until the zero-Firebase gate legitimately passes.
- Provider-specific AI/STT/vision/document adapters still exist behind governed egress boundaries.
- The completed `core.ai_egress` / P0-MENA-1 boundary governs live external model/media operations by authenticated patient, purpose, modality, consent, payload minimization/allowlisting and applicable provider/processor policy.
- IAmina has an executable truth-provenance and capability/authority contract: generative models may narrate approved data but are not clinical decision authorities.
- CI blocks new direct external AI callsites that omit the central authorization assertion.

### Target direction

- MENA country-by-country/locale-by-locale rollout.
- Retire remaining Firebase compatibility only after account-preserving reconciliation/rollback requirements and the permanent zero-Firebase audit gate pass.
- Keep outbound AI/media policy provider-agnostic while completing external processor/residency/legal approvals for the pilot.
- Select text/STT/vision providers independently by the prepared live benchmark rather than adapter availability.
- No second condition until the Retention Gate passes.

## 3. Layer model

### 3.1 Flutter application

Responsibilities:

- patient-facing UX;
- onboarding/profile;
- diabetes logging and journal;
- dashboard/analytics presentation;
- truthful mobile Dashboard action routing;
- local medication-event and in-app reminder persistence in Drift v10;
- companion conversation UI;
- offline-first Drift persistence and sync;
- locale/script/RTL presentation;
- auth/session client behavior.

Rules:

- Flutter is the only product frontend.
- No business-critical safety rule may exist only in the client.
- Medication-event capture is patient-entered historical data, not prescribing/dose authority.
- In-app reminder persistence must not be presented as operating-system notification delivery unless that integration is actually enabled.
- Mockup parity must not introduce fabricated patient data, unread-notification state or unsupported clinical capability.
- Location may suggest locale settings but must not silently choose clinical/safety behavior.

### 3.2 Django API / shared core

Shared core responsibilities include:

- account/identity contracts;
- Django-owned auth/token surface plus controlled legacy identity migration compatibility;
- safety middleware/registries;
- canonical deterministic patient-facing emergency response composition;
- shared module contracts;
- IAmina truth-provenance and capability/authority contracts;
- AI/media egress authorization and payload-governance policy;
- unstructured generative clinical-context evidence minimization;
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
- diabetes-specific API surfaces and domain behavior;
- recomputable longitudinal `ClinicalObservationState` for approved deterministic personal-response observations;
- separate `ProactiveInsightState` workflow/delivery state derived from those observations, including bounded non-urgent prioritization and attention-budget bookkeeping.

The Clinical Twin remains the clinical observation truth boundary. Proactive workflow state may decide **what to surface and when** within its approved authority, but it cannot create clinical truth, diagnose, prescribe, optimize treatment, calculate doses or take over deterministic emergency routing. The current `personal_response` source is constrained to monitoring or clinician-discussion preparation and cannot persist an escalated state.

Destructive mutation of clinically contributive source Journal rows is serialized against canonical Clinical Twin refresh. Persisted derived observation state is purged/rebuilt only from surviving authoritative source rows, while normal sparse refresh remains a distinct longitudinal-history behavior. Patient export/account deletion/retention govern the derived Clinical Twin state, and subordinate proactive workflow state cannot outlive deletion of its source observation.

P2-COMPANION-1 adds a diabetes-owned `CompanionReviewAnchor` workflow checkpoint plus immutable observation snapshots for deterministic longitudinal comparison. The anchor does not create clinical truth: it copies only already-governed Clinical Twin state at a server-generated explicit companion-review event. Capture/comparison share the canonical patient-row serialization lock. Explicit source erasure/replacement deletes affected patient anchors before Clinical Twin rebuild because historical snapshots may encode erased source evidence. No app-open/read event, client timestamp, conversation state or model output may become a review anchor. The comparison layer may classify only `new`, `persisting`, descriptive `improving`, governed `resolved` or `unknown`; missing evidence fails closed. This state is patient-owned application data and remains under portability/deletion/retention governance.

The inherited PR #143 `consultation-brief.v1` contract remains a downstream restricted P2-COMPANION-5 consultation-support sub-contract, not a new truth store and not IAmina's product identity. It accepts only bounded immutable observed facts plus evidence-registry-governed deterministic derivations and keeps model narration subordinate to approved structured fields. The P2-COMPANION-1 review anchor is explicitly a patient companion-review checkpoint; it must not be relabeled as a clinician consultation checkpoint. Consultation assembly, endpoint replacement and clinician-facing/patient-preparation UX remain later separately certified work.

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
       → unstructured generative-context evidence minimization where applicable
       → patient/purpose/modality egress scope
       → server-side consent authorization
       → purpose-specific payload minimization/allowlisting
       → governed provider/processor policy
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

### P0.6 emergency response authority now as-built

- Deterministic emergency classification remains owned by shared `core.input_safety`; P0.6 does not change clinical thresholds or triage classes.
- `core.emergency_response` is the single patient-facing emergency response composer used by triage POST interception, the urgent SSE response boundary, and direct `IAmina.chat` / `IAmina.stream_chat` orchestration.
- Country-specific medical emergency contacts continue to come only from the versioned shared emergency-resource registry; missing, unconfirmed, unknown or stale jurisdiction fails closed without inventing a number.
- The former `core.middleware.triage_vital -> diabetes.middleware.triage_classification` import-linter exemption is removed because shared core no longer needs that reverse dependency.
- Generative models have no emergency classification or emergency response-composition authority.

### P0.2/P0.3 truth and capability boundary now as-built

- `TruthRecord` distinguishes observed facts, explicit patient claims, deterministic derivations, preferences, conversational state and model inference.
- Model inference and conversational state cannot be persisted as patient clinical fact or used as deterministic clinical input merely because a model produced or repeated them.
- Explicit patient claims retain their provenance but may feed approved deterministic triage/domain logic; using a claim as input does not validate a diagnosis.
- The capability matrix permits generative explanation/summarization of approved data and clinician-question preparation, while emergency classification remains deterministic-only.
- Diagnosis, prescription, dose calculation, treatment optimization/change, model-inference promotion and autonomous clinical-record writes are disabled capabilities.
- `GatewayLLM` fails closed on a forbidden generative capability before provider egress.
- `doctor-brief` uses the capability-aware gateway with `SUMMARIZE_APPROVED_DATA` while preserving its structured JSON response contract.
- The diabetes structured insight formatter uses the same gateway with `SURFACE_DETERMINISTIC_PATTERN`, preserving its existing JSON parsing, fallback and patient-visible sanitation behavior.

### P0.7 generative clinical-context evidence boundary now as-built

- Internal detector/pattern identifiers remain deterministic implementation metadata; they are not themselves evidence that an unstructured generative model may interpret as a clinical finding.
- Diabetes chat context supplies approved descriptive observation evidence and explicit limitations instead of raw detector codes.
- The generic `narrate()` prompt no longer appends `DomainContext.detected_patterns` as a free-text `Patterns:` block.
- Main chat memory, legacy cached pivot shapes and hidden Thinking Mode are covered by a marker-scoped last-mile evidence-minimization boundary before provider-bound text leaves the shared gateway.
- Thinking Mode consumes the current condition-agnostic `DomainContext` tone/primary signals and no longer depends on legacy/nonexistent pattern-code attributes.
- The P0.5A structured `SURFACE_DETERMINISTIC_PATTERN` correlation contract is separate: its internal code token may remain inside that structured formatter because patient-visible authority is independently neutralized at its final sanitizer boundary.
- P0.7 does not recalibrate detectors, change clinical thresholds, grant diagnosis/causality/treatment authority, or modify the P0.6 emergency path.

## 6. AI / model boundary

### Current state after P0-MENA-1, P0.2, P0.3 and P0.7

`core.ai_egress` is the central governance boundary for currently wired live external model/media operations.

It requires before real egress:

- valid authenticated patient scope;
- registered purpose;
- declared/allowed modality;
- server-side consent from the patient profile;
- purpose-specific payload allowlisting/minimization;
- applicable raw-media policy/consent;
- governed provider/processor policy.

Default-deny conditions include:

- no egress scope;
- missing patient consent record/consent;
- unknown purpose;
- modality not authorized for that purpose;
- payload outside the sanctioned purpose contract;
- provider/path outside governed policy.

The boundary is intentionally **lazy**: entering a request scope does not itself require AI consent. Deterministic emergency/safety behavior can still complete for a patient who declined AI as long as no external provider call is attempted.

The shared text gateway additionally enforces the IAmina capability matrix before provider egress. This authority check is independent of consent/egress authorization: an allowed narrative capability can still be denied for missing egress consent, and egress consent never grants a forbidden medical capability.

For unstructured generative clinical context, the shared gateway also applies the P0.7 evidence ceiling before the existing PHI masking boundary. Raw internal detector identifiers are therefore not accepted as semantic clinical evidence merely because a legacy memory/pivot/prompt shape still contains them.

Live call paths wired through this policy include the currently inventoried text/gateway, chat, summary/doctor-brief, structured diabetes insight formatting, STT/audio, vision/OCR, and document-processing flows.

CI contains an AI-egress anti-bypass gate so new direct model/provider callsites cannot silently omit the authorization assertion. Focused IAmina contracts prevent both the AI API/doctor-brief path and the structured diabetes insight formatter from returning to direct text-provider access.

### Important remaining limitations

Completion of P0-MENA-1 is an implementation/governance boundary, not a provider-selection or real-patient deployment approval.

Still open outside that runtime contract:

- restricted pilot processor/subprocessor and consent approval;
- Morocco residency/cross-border deployment approval;
- native-language safety parity gates;
- live P0-MENA-4 text/STT/vision benchmark and evidence-based provider selection;
- final decommission of legacy provider/auth compatibility seams only after their explicit operational gates pass.

Therefore adapter existence does not imply provider approval, and external legal/deployment readiness remains fail-closed under `docs/ROADMAP.md`.

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

Raw audio/images/documents may disclose sensitive information even without explicit text fields, so media transmission requires an approved purpose and the consent/policy level defined by the completed P0-MENA-1 contract.

## 8. Authentication

### Current

P0-MENA-3 delivered Django-owned registration/login/logout, signed expiring IAMINA bearer tokens, global token revocation, password establishment/recovery, controlled Firebase identity migration/link/unlink, collision/readiness/rollback contracts, native-first Flutter initialization and secure token storage.

The API safety hardening from P0-A continues to distinguish Bearer/bootstrap behavior from cookie/session CSRF behavior.

Legacy Firebase dependencies may remain only as controlled migration/reconciliation compatibility while the permanent operational zero-Firebase gate is not yet legitimately satisfied.

### Decommission target

Remove remaining Firebase dependencies only after account identity preservation, reconciliation and rollback are proven and:

```bash
python manage.py audit_auth_migration --require-zero-firebase
```

passes legitimately. Decommissioning must not fabricate completion merely because Django-native auth is already the primary implemented direction.

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
- Deterministic derived metrics/patterns remain derived truth and should be recomputed from authoritative source data rather than promoted to immutable patient facts. Approved `ClinicalObservationState` is a recomputable materialized lifecycle, not immutable clinical fact.

## 11. Key invariants

| Invariant | Reason |
|---|---|
| Deterministic emergency gate before generative AI | Patient safety |
| One shared patient-facing emergency response composer in core | Consistent safety behavior across POST, SSE and companion paths |
| Raw internal detector identifiers are not unstructured generative clinical evidence | Epistemic safety / authority separation |
| Unit normalization before clinical/AI logic, fail-closed on unexpected normalization failure | Data integrity |
| Cookie/session API writes retain CSRF protection | Web/API security |
| No diagnosis/prescription/treatment optimization | Product/regulatory boundary |
| Model inference never silently becomes patient fact or clinical authority | Clinical truthfulness |
| Explicit patient claims remain labeled claims even when used by deterministic triage/domain logic | Provenance integrity |
| Forbidden generative capabilities fail closed before shared-gateway provider egress | AI authority boundary |
| Every live external model/media call requires sanctioned egress authorization | Privacy + sovereignty |
| Missing scope/consent/purpose/modality authorization denies egress | Default-deny safety |
| Purpose-specific minimization/allowlisting governs external payloads | Data minimization |
| Clinical Twin derivation remains recomputable and source-erasure consistent | Data lifecycle / provenance integrity |
| Proactive workflow state cannot widen Clinical Twin authority | Clinical safety |
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
