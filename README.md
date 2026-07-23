# IAmina — MENA Diabetes Companion

IAmina is a **diabetes companion designed for the MENA region**. The product combines deterministic clinical logic, longitudinal patient context, offline-first tracking, and multilingual conversation to help people understand and follow their diabetes data more consistently.

> **Current product scope:** diabetes only. IAmina is a companion, not a diagnostic or prescribing system. A second condition is explicitly gated behind real retention and payer evidence.

## Product doctrine

- **MENA-first, not translation-first.** French, Modern Standard Arabic, and English are baseline languages. Country dialects are enabled only after native review and safety-parity validation.
- **User choice beats geolocation.** Country/location may suggest language, dialect, units, time zone, and emergency resources; it must never silently decide them.
- **Deterministic engine first.** IAmina's approved clinical/safety logic decides structured outputs. Generative models may verbalize approved minimized context or perform explicitly permitted media tasks.
- **No diagnosis or prescription.** Emergency handling is deterministic and must never depend on an LLM response.
- **Sovereignty and minimization by design.** External model calls must pass through an enforceable outbound boundary with purpose, consent, minimization, redaction, retention, and processor metadata.
- **Retention before expansion.** The first proof is a safe MENA pilot and measurable D90 retention, not feature count or number of disease modules.

## Current strategic status

The repository is in a **MENA sovereignty reset** before the first real-patient pilot.

Critical path:

1. Close uncontrolled AI/model data egress.
2. Define and enforce the MENA locale + safety contract.
3. Migrate sovereignty-critical authentication from legacy Firebase dependencies to Django-native auth without losing accounts.
4. Benchmark text, STT, and vision providers independently for privacy, MENA quality, latency, availability, and cost.
5. Deploy a safety-equivalent pilot in one founder-selected MENA country/cohort.
6. Measure D90 retention, then decide whether to expand.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the live backlog and gates.

## Stack

| Layer | Current | Direction |
|---|---|---|
| Frontend | Flutter — web, iOS, Android | Keep Flutter as the only frontend |
| Backend | Django 6 + django-ninja | Keep modular monolith/chassis seams |
| Database | PostgreSQL in Docker/staging path; SQLite manual-dev fallback | PostgreSQL authoritative outside lightweight local fallback |
| Auth | Firebase bridge still present | Django-native authentication target |
| AI | Legacy provider-specific runtime still exists | Provider-agnostic, privacy-gated outbound boundary; text/STT/vision selected independently |
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
backend/core/          Shared chassis contracts, auth/account, safety, observability
backend/diabetes/      The only live disease module
frontend/              Flutter application and offline-first local data
docs/                  Product, architecture, safety, roadmap, ADRs, technical debt
```

## Canonical documentation

| Document | Authority |
|---|---|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Single forward backlog, priorities, gates, current status |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Current as-built architecture + target boundaries |
| [`docs/SPECS.md`](docs/SPECS.md) | Current product/API capability contract |
| [`docs/MEDICAL_DATA_PLAN.md`](docs/MEDICAL_DATA_PLAN.md) | Clinical-data and safety boundaries |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Engineering workflow and non-negotiable guardrails |
| [`docs/TECHDEBT.md`](docs/TECHDEBT.md) | Only unresolved technical debt |
| [`docs/MISTAKES.md`](docs/MISTAKES.md) | Reusable engineering lessons; not a status tracker |
| [`docs/adr/`](docs/adr/) | Immutable architecture decisions/history |
| [`docs/architecture/ARCHITECTURE-TIMELINE.md`](docs/architecture/ARCHITECTURE-TIMELINE.md) | Historical architecture evolution only |

Dated assessments and deleted legacy plans remain available through git history as evidence, **not forward instructions**.

## Non-negotiable safety rules

- Never bypass or reorder the deterministic emergency and unit-normalization safety gates without an explicit architecture decision.
- Never send medical emergencies to a generative model for decision-making.
- Never expose names, contact details, identifiers, raw unrelated clinical history, or unapproved media to an external model provider.
- Never add a locale/dialect to a patient pilot without native-speaker safety parity, emergency-resource validation, RTL/script coverage where applicable, and privacy/compliance readiness.
- Never commit secrets, provider keys, service-account files, or local agent permission files containing secrets.

## Development workflow

`main` is the repository's current canonical branch. Work on a short-lived feature/fix/docs branch and open a focused PR back to `main`. The live work unit must come from `docs/ROADMAP.md`.
