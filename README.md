# IAmina — Diabetes Companion

AI-powered diabetes management app. Logs glucose, meals, insulin, and fatigue — then surfaces clinical insights via a conversational AI assistant.

**Stack:** Flutter (web + iOS + Android) · Django Ninja · Firebase Auth · Gemini 2.5 Flash · SQLite (dev) / PostgreSQL (prod)

---

## Quick Start

```bash
git clone <repo>
cd diabetes-poc
./dev.sh
```

`dev.sh` handles everything on first run (venv, deps, migrations, demo data) then starts both services:

- **Frontend** → http://localhost:3000
- **Backend API** → http://127.0.0.1:8001
- **Demo login** → `dev@iamina.app`

> Requires Flutter 3.41.7 — install via `mise install` (`.tool-versions` is pinned) or [flutter.dev](https://docs.flutter.dev/get-started/install).

---

## Architecture

```
diabetes-poc/
├── frontend/          Flutter — GoRouter 14, Drift 2.20, Provider, Firebase Auth
├── backend/           Django 6.0.3 + django-ninja — chassis + diabetes module, clinical engine, LLM
├── docs/              Architecture, roadmap, migrations, ADRs
└── dev.sh             Local dev entry point (setup + backend + frontend)
```

---

## Docs

| Doc | Purpose |
|-----|---------|
| [ONBOARDING.md](docs/ONBOARDING.md) | New dev setup guide |
| [ROADMAP.md](docs/ROADMAP.md) | Phases, milestones, current status — **single tracker** |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Git workflow, parallel-work handoff, PR/merge model, code standards |
| [architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | Current system design (chassis + modules) |
| [architecture/ARCHITECTURE-TIMELINE.md](docs/architecture/ARCHITECTURE-TIMELINE.md) | How the design evolved (v1 → ADR-0008) |
| [MIGRATIONS.md](docs/MIGRATIONS.md) | DB (SQLite→Postgres) and LLM (Gemini→Kimi) migration plans |
| [TECHDEBT.md](docs/TECHDEBT.md) | Registered tech debt with owner and priority |
| [MEDICAL_DATA_PLAN.md](docs/MEDICAL_DATA_PLAN.md) | Clinical data model, RGPD compliance |
| [SPECS.md](docs/SPECS.md) | Feature specs and API contracts |
| [docs/adr/](docs/adr/) | Architecture Decision Records (immutable) |

---

## Critical Rules

- **Never bypass** `TriageVitalMiddleware` — medical emergency gate
- **Never bypass** `UnitGuardMiddleware` — glucose unit normalization
- **KPIs are SQL-first** — never Python-computed (ADR-0007)
- **LLM input is English pivot text only** — never raw patient data
- Priority order: **Security > Integrity > Performance > Style**
