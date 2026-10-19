# IAmina — MENA Diabetes Companion

IAmina is a **diabetes companion designed for Morocco and the six Gulf Cooperation Council (GCC) countries**—Saudi Arabia, the United Arab Emirates, Qatar, Bahrain, Kuwait and Oman—within a broader MENA-first product vision. The product combines deterministic clinical logic, longitudinal patient context, offline-first tracking, and multilingual conversation to help people understand and follow their diabetes data more consistently. The seven-country pilot is a **target**, not an authorized or completed launch.

> **Current product scope:** diabetes only. IAmina is a companion, not a diagnostic or prescribing system. It helps the patient understand, follow and prepare; it does not replace the physician. A second condition is explicitly gated behind real retention and payer evidence.
>
> **Status distinction (2026-10-15):** the product and privacy decisions below are **intended pilot requirements**, not assertions about the current implementation. The repository still contains Django/PostgreSQL patient-data APIs, offline synchronization pathways and external-service adapters. These must be disabled, replaced, isolated or technically proven compatible with the chosen pilot before any real-patient use.

## Intended pilot and regulatory onboarding (2026-10-15)

The founder's onboarding established the following **target decisions** for CNDP/GCC preparation; none represents a regulatory approval, a launched feature or runtime evidence:

- **Territories and launch:** simultaneous intended launch in **Morocco, Saudi Arabia, UAE, Qatar, Bahrain, Kuwait and Oman**, conditional on separate country-specific privacy, health-data, child-protection and, where applicable, medical-software assessments/approvals. A Moroccan CNDP filing does not cover the GCC.
- **Future operator:** a **company to be incorporated in Morocco**. No incorporated entity, registration number, registered address or legally appointed controller is evidenced yet. These must be established before completing official controller fields.
- **Users:** **adults and minors**, using IAmina **directly and independently**. Age-appropriate clinical safeguards, parental/guardian authorization and legal-capacity rules remain to be specified and cleared in each territory; this is not approval for unsupervised minor deployment.
- **Medical-data residency:** **on the user's own device only**, without medical-record cloud synchronization or remotely held medical history, as an intended pilot design. Local device security, loss/recovery, OS backups, exports, CGM data sources, logs, crash reporting, communications, metadata and infrastructure must be inventoried and verified before claiming this behavior. This requirement is **not yet proven by the current Django/PostgreSQL/offline-sync implementation**.
- **Requested first-pilot functionality (subject to feasibility and safety/legal gates):** manual glucose logging and local trend views; read-only CGM connectivity; voice entry and interactions; meal photos and medical-document handling; personalized reports and PDF exports; reminders/notifications; and usage statistics/technical diagnostics. These are **requested scope**, not statements that all features work or are approved. A feature requiring transmission of health data to a third party conflicts with the local-only goal until explicitly redesigned or re-scoped.
- **Generative LLM constraint:** the model may only help produce **generic, non-patient text/templates**. It must receive **no patient measurements, clinical context, messages, identifying or patient-correlatable metadata**. Patient-specific selection/calculation and assembly into reports or replies must occur within governed, non-generative IAmina processing without re-sending personalized output to a model. Full end-to-end egress tests—including prompts, SDKs, headers, URLs, IP/session correlation, tracing and provider logs—remain **required; zero patient-data egress is not yet independently proven**.
- **Proposed retention:** on-device medical records persist until the patient requests deletion, **subject to applicable legal retention requirements**. This does not settle separate periods for security logs, technical data, OS backups, exports, or minors' records; secure deletion and restore design remain to be verified.
- **Provisional privacy correspondence:** `lafabriquedapollon@gmail.com` (founder-provided, not verified as an active rights-handling service or a designated DPO). A formal controller and a validated rights-request process remain pending.

These statements feed the restricted [CNDP + GCC preparation register](https://app.notion.com/p/3fa77c66336281298cd6deeba0879ac1), the dated [web local-only egress audit](docs/security/2026-10-19-cndp-web-local-only-transport-audit.md), and the pre-real-patient **P5-6B / issue #320** gate. See `docs/ROADMAP.md` and `docs/architecture/ARCHITECTURE.md` for the **as-built** architecture and its unresolved compliance/technical gates. No CNDP/GCC authorization, independent medical clearance, or patient-production release is claimed.

## Product doctrine

- **Companion, never physician replacement.** IAmina may observe, compare, explain and propose safe non-prescriptive next steps; the qualified clinician remains the medical decision authority.
- **MENA-first, not translation-first.** French, Modern Standard Arabic, and English are baseline languages. The technical English baseline is complete across the 16 active patient-facing surfaces; country dialects still require native review and safety-parity validation.
- **User choice beats geolocation.** Country/location may suggest language, dialect, units, time zone, and emergency resources; it must never silently decide them.
- **Deterministic engine first.** IAmina's approved clinical/safety logic decides structured outputs. **Target LLM rule:** generic text only, with no patient data or correlatable context sent to the LLM; personalized response/report assembly must be deterministic within IAmina. Existing generative narration/media adapters and minimized-context permissions in code/contracts are **not proof** that this stricter rule is already enforced.
- **No diagnosis or prescription.** IAmina does not diagnose, prescribe, calculate doses, optimize/change treatment or present itself as a medical consultation. Emergency handling is deterministic and must never depend on an LLM response.
- **Suggestions stay non-prescriptive.** Personalized suggestions are limited to understanding data, monitoring, collecting missing context, approved education, preparing clinician discussion and follow-up recording.
- **Sovereignty and minimization by design.** The existing P0-MENA-1 server-side egress boundary enforces patient/purpose/modality authorization, allowlists, consent and processor policy. The new **no-patient-data-to-LLM** and **medical-data-on-device-only** pilot targets are stricter and require separate end-to-end code, integration, and network verification; consent or de-identification alone does not satisfy them.
- **Retention before expansion.** The first proof is a safe MENA pilot and measurable D90 retention, not feature count or number of disease modules.

## Current strategic status

The repository is in a **MENA pilot-hardening phase** before the first real-patient cohort. The companion-intelligence product lane is closed through P3-EVALS. **Gate A — Secure Core is certified at 10.0/10** after issue #30 completed reachable Git-history remediation and independent fresh-clone verification. The **technical English baseline is now complete across 16/16 active patient-facing surfaces**, including explicit English selection, persistence, FR/EN/AR runtime-key parity, locale-aware formatting and app-shell/platform copy. This does not waive the remaining restricted native-language, safety, compliance or deployment approvals. The remaining critical path is native-language review, restricted compliance/deployment approvals and deferred live provider benchmarking.

### Recently closed foundations

- **Gate A — Secure Core:** certified at **10.0/10**. The former reachable Git-history failure was remediated under issue #30 by rewriting all reachable branch history, requiring clean tracked-tree/full-history scans before force-update, and independently re-verifying from a fresh clone afterward. Evidence: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md` and `docs/assessments/2026-08-14-security-30-history-rewrite-certification.md`.
- **P0-MENA-2 English baseline:** technical active-surface English coverage is **16/16 = 100%**. English is explicitly selectable and persistable; FR/EN/AR runtime ARB keys are parity-gated; known French hardcoded-copy gaps, forced French date formatting, AI Summary static copy, import/document-import copy, dashboard companion context, global fallback and iOS permission prompts were remediated. Evidence: `docs/assessments/2026-08-14-english-baseline-completeness-certification.md`. The restricted native/clinical/safety-owner approvals remain open and continue to hold P0-MENA-2 at its existing roadmap status.
- **P0-A — API safety boundaries:** cookie/session API writes retain CSRF protection; unit normalization covers legacy + namespaced module routes and fails closed; deterministic triage authority sits on the shared safety side of the architecture boundary.
- **P0-MENA-1 — AI/data egress governance:** live external AI/media operations require patient + purpose + modality scope, server-side consent, explicit minimization/allowlists and governed processor policy at real egress time; CI prevents bypassing the sanctioned boundary.
- **P0-MENA-3 — Sovereign authentication migration:** Django-owned registration/login/logout and IAMINA bearer-token flows are implemented with guarded Firebase migration/reconciliation paths retained until the zero-Firebase operational gate is legitimately satisfied.
- **P2-CLINICAL-TWIN — Longitudinal Observation Memory:** approved deterministic `personal_response` observations have a recomputable longitudinal lifecycle with governed provenance, data-erasure reconciliation and patient export/retention compatibility.
- **P2-PROACTIVE — Prioritization + Insight Lifecycle:** approved Clinical Twin observations feed a bounded, auditable non-urgent proactive workflow; the current source cannot escalate, change treatment or gain generative clinical authority.
- **P2-COMPANION-0..8 + P3-HORIZON + P3-EVALS:** the companion-intelligence lane is closed. P3-EVALS completed explicit human PASS ALL review across longitudinal, negative, false-positive and boundary dimensions; canonical closeout is merged and post-merge certified.
- **Consultation Brief Contract v1:** PR #143 delivered a certified restricted consultation-support sub-contract. It remains part of the closed P2-COMPANION consultation capability; it does not define IAmina as a doctor or doctor-facing product.

### Still open on the critical path

1. **Pilot security blocker #30 is closed:** reachable Git history was rewritten and independently fresh-clone verified. Continue with restricted linguistic, compliance/deployment and provider-evidence gates.
2. Complete P0-MENA-2 native-language safety review, including remaining Darija high-severity variants and multimodal/transliteration parity. The English technical baseline is closed; this item now refers only to the remaining restricted human-language/safety approvals.
3. Reconcile the local-only medical-data pilot target against actual backend/sync/CGM/voice/photo/telemetry paths; obtain applicable CNDP and **each GCC country's** health-data, minors', and any actual cross-border/processor approvals before a simultaneous seven-country pilot.
4. Run the deferred live text, STT and vision/OCR provider benchmarks and approve cutover only from evidence.
5. Run the real-patient pilot go/no-go only after the safety/compliance gates are legitimately closed.
6. Measure D90 retention, safety and clinical usefulness, then decide whether to expand.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the live backlog and gates and [`docs/COMPANION_INTELLIGENCE_CONTRACT.md`](docs/COMPANION_INTELLIGENCE_CONTRACT.md) for the product/authority ceiling.

## Stack

| Layer | Current | Direction |
|---|---|---|
| Frontend | Flutter — web, iOS, Android | Keep Flutter as the only frontend |
| Backend | Django 6 + django-ninja | Keep modular monolith/chassis seams |
| Database | PostgreSQL in Docker/staging path; SQLite manual-dev fallback | PostgreSQL authoritative outside lightweight local fallback |
| Auth | Django-owned auth/token flows with controlled Firebase migration/reconciliation compatibility still present | Remove remaining Firebase dependencies only after the permanent zero-Firebase audit gate passes |
| AI | Provider-specific adapters behind a central governed egress authorization/minimization boundary | Keep provider-agnostic policy authority and evidence-based provider selection |
| Local state | Drift / SQLite, with existing backend/sync paths | **Target:** medical records stay only on the patient's device; any remote medical sync must be removed or verifiably disabled for the pilot, with safe backup/recovery addressed |

## Quick start

### Recommended: Docker backend

```bash
git clone <repo>
cd IAMINA-MVP
cp .env.example .env
docker compose up --build

docker compose run --rm backend python manage.py setup_demo
```

Backend API: `http://127.0.0.1:8001/api/v1/`

Frontend runs on the host with the pinned Flutter version:

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

### Single cross-platform host launcher

Windows and macOS use the same launcher source:

```bash
# Windows
python IAMINA.py

# macOS
python3 IAMINA.py
```

The launcher starts the backend on `http://127.0.0.1:8008` and the Flutter web frontend on `http://localhost:8009`, validates the pinned Flutter version, waits for both services to respond, then opens the browser. Local readiness probes bypass ambient proxy settings and child process trees are cleaned up on exit. Docker remains the canonical backend integration path before merge.

A single file type cannot guarantee native double-click execution on both operating systems. `IAMINA.py` is the only canonical host launcher; native packaged shortcuts may be generated later from this source if guaranteed desktop double-click becomes a release requirement.

## Repository map

```text
backend/               Django project and APIs
backend/core/          Shared chassis contracts, auth/account, safety, AI egress policy, observability
backend/diabetes/      The only live disease module
frontend/              Flutter application and offline-first local data
docs/                  Product, architecture, safety, roadmap, ADRs, technical debt
```

## Canonical documentation

| Document | Authority |
|---|---|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Single forward backlog, priorities, gates, current closeout state |
| [`docs/COMPANION_INTELLIGENCE_CONTRACT.md`](docs/COMPANION_INTELLIGENCE_CONTRACT.md) | Companion product identity, authority ceiling, allowed suggestion classes and P2-COMPANION sequence |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Current as-built architecture + target boundaries |
| [`docs/SPECS.md`](docs/SPECS.md) | Current product/API capability contract |
| [`docs/MEDICAL_DATA_PLAN.md`](docs/MEDICAL_DATA_PLAN.md) | Clinical-data and safety boundaries |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Engineering workflow, guardrails, mandatory docs closeout |
| [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) | Canonical developer prerequisites, toolchain sources of truth, and launcher requirements |
| [`docs/TECHDEBT.md`](docs/TECHDEBT.md) | Only unresolved technical debt |
| [`docs/MISTAKES.md`](docs/MISTAKES.md) | Reusable engineering lessons; not a status tracker |
| [`docs/adr/`](docs/adr/) | Immutable architecture decisions/history |
| [`docs/architecture/ARCHITECTURE-TIMELINE.md`](docs/architecture/ARCHITECTURE-TIMELINE.md) | Historical architecture evolution only |

Dated assessments and deleted legacy plans remain available through git history as evidence, **not forward instructions**.

## Non-negotiable safety rules

- Never present IAmina as a physician, medical consultation or replacement for qualified professional care.
- Never allow a personalized suggestion to become diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Never bypass or reorder deterministic emergency and unit-normalization safety gates without an explicit architecture decision.
- Never weaken cookie/session CSRF protection with a blanket API exemption.
- Never send medical emergencies to a generative model for decision-making.
- Never call an external model/media provider outside the sanctioned egress authorization boundary.
- **Pilot target:** never send patient measurements, clinical context, user messages, personal identifiers or correlatable metadata to an external LLM; use generic wording only and deterministic local/first-party patient-specific assembly. **Not yet proven for all current runtime paths.**
- Never expose names, contact details, identifiers, raw unrelated clinical history, or unapproved media to an external model provider.
- Never add a locale/dialect to a patient pilot without native-speaker safety parity, emergency-resource validation, RTL/script coverage where applicable, and privacy/compliance readiness.
- Never commit secrets, provider keys, service-account files, or local agent permission files containing secrets.

## Development workflow

`main` is canonical. Use a short-lived branch and focused PR to `main`. Each live work unit is tracked from `docs/ROADMAP.md`; do not execute historical deleted roadmaps from memory.

Before merge:

```bash
cd backend && ruff check . && pytest --tb=short -q
cd ../frontend && flutter analyze --no-fatal-infos && flutter test --no-pub
```

Architecture/safety-sensitive PRs must also run their repository-specific contract tests. GitHub CI is the final merge authority.
