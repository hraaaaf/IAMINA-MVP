# IAmina — MENA Diabetes Companion

IAmina is a **diabetes companion designed for the MENA region**. The product combines deterministic clinical logic, longitudinal patient context, offline-first tracking, and multilingual conversation to help people understand and follow their diabetes data more consistently.

> **Current product scope:** diabetes only. IAmina is a companion, not a diagnostic or prescribing system. A second condition is explicitly gated behind real retention and payer evidence.

## Product doctrine

- **MENA-first, not translation-first.** French, Modern Standard Arabic, and English are baseline languages. Country dialects are enabled only after native review and safety-parity validation.
- **User choice beats geolocation.** Country/location may suggest language, dialect, units, time zone, and emergency resources; it must never silently decide them.
- **Deterministic engine first.** IAmina's approved clinical/safety logic decides structured outputs. Generative models may verbalize approved minimized context or perform explicitly permitted media tasks.
- **No diagnosis or prescription.** Emergency handling is deterministic and must never depend on an LLM response.
- **Sovereignty and minimization by design.** External model calls require the completed P0-MENA-1 server-side patient/purpose/modality authorization, payload minimization/allowlists, consent and processor-policy boundaries.
- **Retention before expansion.** The first proof is a safe MENA pilot and measurable D90 retention, not feature count or number of disease modules.

## Current strategic status

The repository is in a **clinical-intelligence + MENA pilot-hardening phase** before the first real-patient cohort.

### Recently closed foundations

- **P0-A — API safety boundaries:** cookie/session API writes retain CSRF protection; unit normalization covers legacy + namespaced module routes and fails closed; deterministic triage authority sits on the shared safety side of the architecture boundary.
- **P0-MENA-1 — AI/data egress governance:** live external AI/media operations require patient + purpose + modality scope, server-side consent, explicit minimization/allowlists and governed processor policy at real egress time; CI prevents bypassing the sanctioned boundary.
- **P0-MENA-3 — Sovereign authentication migration:** Django-owned registration/login/logout and IAMINA bearer-token flows are implemented with guarded Firebase migration/reconciliation paths retained until the zero-Firebase operational gate is legitimately satisfied.
- **P2-CLINICAL-TWIN — Longitudinal Observation Memory:** approved deterministic `personal_response` observations have a recomputable longitudinal lifecycle with governed provenance, data-erasure reconciliation and patient export/retention compatibility.
- **P2-PROACTIVE — Prioritization + Insight Lifecycle:** approved Clinical Twin observations feed a bounded, auditable non-urgent proactive workflow; the current source cannot escalate, change treatment or gain generative clinical authority.

### Still open on the critical path

1. Build **P2-DOCTOR — Consultation Intelligence** on top of the certified Clinical Twin + proactive foundation.
2. Complete P0-MENA-2 native-language safety review, including remaining Darija high-severity variants and multimodal/transliteration parity.
3. Complete restricted pilot consent, processor/subprocessor, privacy/CNDP and Morocco residency/cross-border approvals.
4. Remediate or explicitly supersede the pilot-blocking reachable Git-history secret finding tracked by issue #30 before a real-patient go/no-go.
5. Run the deferred live text, STT and vision/OCR provider benchmarks and approve cutover only from evidence.
6. Run the real-patient pilot go/no-go only after the safety/compliance gates are legitimately closed.
7. Measure D90 retention, safety and clinical usefulness, then decide whether to expand.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the live backlog and gates.

## Stack

| Layer | Current | Direction |
|---|---|---|
| Frontend | Flutter — web, iOS, Android | Keep Flutter as the only frontend |
| Backend | Django 6 + django-ninja | Keep modular monolith/chassis seams |
| Database | PostgreSQL in Docker/staging path; SQLite manual-dev fallback | PostgreSQL authoritative outside lightweight local fallback |
| Auth | Django-owned auth/token flows with controlled Firebase migration/reconciliation compatibility still present | Remove remaining Firebase dependencies only after the permanent zero-Firebase audit gate passes |
| AI | Provider-specific adapters behind a central governed egress authorization/minimization boundary | Keep provider-agnostic policy authority and evidence-based provider selection |
| Local state | Drift / SQLite | Offline-first sync retained |

## Quick start

### Recommended: Docker backend

```bash
git clone <repo>
cd IAMINA-MVP
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

Legacy `dev.sh` / `dev.ps1` launchers remain during migration but are **not the canonical development path**.

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
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Current as-built architecture + target boundaries |
| [`docs/SPECS.md`](docs/SPECS.md) | Current product/API capability contract |
| [`docs/MEDICAL_DATA_PLAN.md`](docs/MEDICAL_DATA_PLAN.md) | Clinical-data and safety boundaries |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Engineering workflow, guardrails, mandatory docs closeout |
| [`docs/TECHDEBT.md`](docs/TECHDEBT.md) | Only unresolved technical debt |
| [`docs/MISTAKES.md`](docs/MISTAKES.md) | Reusable engineering lessons; not a status tracker |
| [`docs/adr/`](docs/adr/) | Immutable architecture decisions/history |
| [`docs/architecture/ARCHITECTURE-TIMELINE.md`](docs/architecture/ARCHITECTURE-TIMELINE.md) | Historical architecture evolution only |

Dated assessments and deleted legacy plans remain available through git history as evidence, **not forward instructions**.

## Non-negotiable safety rules

- Never bypass or reorder deterministic emergency and unit-normalization safety gates without an explicit architecture decision.
- Never weaken cookie/session CSRF protection with a blanket API exemption.
- Never send medical emergencies to a generative model for decision-making.
- Never call an external model/media provider outside the sanctioned egress authorization boundary.
- Never expose names, contact details, identifiers, raw unrelated clinical history, or unapproved media to an external model provider.
- Never add a locale/dialect to a patient pilot without native-speaker safety parity, emergency-resource validation, RTL/script coverage where applicable, and privacy/compliance readiness.
- Never commit secrets, provider keys, service-account files, or local agent permission files containing secrets.

## Development workflow

`main` is the repository's canonical branch. Work on a short-lived feature/fix/docs branch and open a focused PR back to `main`. The live work unit must come from `docs/ROADMAP.md`.

**Every merged phase/task ends with a documentation closeout before the next roadmap unit starts.** At minimum inspect/update the roadmap, then architecture/specs/domain contracts/technical debt only where the merged truth changed.
