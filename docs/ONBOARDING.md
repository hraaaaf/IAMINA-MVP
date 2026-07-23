# IAmina — Developer Onboarding

IAmina is a MENA-first diabetes companion. Before changing code, read:

1. `CLAUDE.md`
2. `docs/ROADMAP.md`
3. `docs/architecture/ARCHITECTURE.md`
4. `docs/CONTRIBUTING.md`
5. `docs/MISTAKES.md`

The roadmap is the only forward tracker.

## 1. Clone

```bash
git clone <repo>
cd IAMINA-MVP
```

## 2. Install prerequisites

- Docker + Docker Compose
- Flutter version pinned by `.tool-versions`
- Git

Install the pinned Flutter toolchain through your preferred version manager, then verify:

```bash
flutter --version
docker --version
docker compose version
```

## 3. Recommended backend setup — Docker

Docker is the canonical development path for backend + PostgreSQL + Redis.

```bash
docker compose up --build
```

Seed demo data only when explicitly needed:

```bash
docker compose run --rm backend python manage.py setup_demo
```

Useful endpoints:

- API: `http://127.0.0.1:8001/api/v1/`
- Health: `http://127.0.0.1:8001/api/v1/health`
- API docs: check the configured Django Ninja docs route in the running app

Stop with:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove local volumes/data.

## 4. Frontend setup

Run Flutter on the host:

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

For Android/iOS, use the normal Flutter device workflow. iOS builds require macOS.

## 5. Environment and secrets

Copy only documented example variables into local environment files. Never commit real secrets.

Current repository reality may still include legacy Firebase/provider integrations while the MENA sovereignty reset is in progress. Treat them as **legacy runtime dependencies**, not the target architecture.

Rules:

- Keep service-account files outside the repository.
- Never place API keys in `CLAUDE.md`, `.claude/settings*.json`, shell history committed to git, test fixtures, or docs.
- Do not invent a new direct provider integration. All external AI/media calls must converge on the sanctioned outbound boundary defined by P0-MENA-1.
- Do not configure a new production AI provider before the P0-MENA-4 benchmark and privacy review.

## 6. Legacy manual path

A manual Python/SQLite path may still exist for lightweight local work, but it is **not the canonical environment** because it can diverge from PostgreSQL/Redis behavior.

Use it only when the task explicitly permits it and verify database/cache-sensitive changes in Docker before merge.

Legacy `dev.sh` / `dev.ps1` wrappers may still exist during migration. Do not update documentation to make them the primary path again.

## 7. Repository architecture

```text
backend/                 Django project and APIs
core/                    Shared contracts, safety, auth/account, observability
diabetes/                Only live disease module
frontend/                Flutter application + Drift offline store
docs/                    Canonical docs, ADRs, architecture history, assessments
```

Key principles:

- Flutter is the only frontend.
- Diabetes is the only live condition.
- Platform/chassis seams exist but do not authorize new modules before the Retention Gate.
- Firebase is legacy current-state; Django-native auth is the target.
- Provider-specific AI runtime is legacy current-state; provider-agnostic privacy-gated egress is the target.

## 8. Before starting work

```bash
git checkout main
git pull origin main
git checkout -b feature/short-description
```

Then select exactly one current unit from `docs/ROADMAP.md` or one clearly scoped maintenance task.

Do not use old phase numbers or archived plans to choose work.

## 9. Safety-sensitive areas

Do not change these casually:

- deterministic emergency/triage flow;
- unit normalization;
- outbound AI/provider boundary and PHI minimization;
- account deletion/consent;
- locale/dialect safety rules;
- SQL-first KPI calculations;
- offline sync idempotency.

Any change to these requires focused tests and explicit PR notes.

## 10. Validation baseline

```bash
python backend/manage.py check
python -m pytest

cd frontend
flutter analyze
flutter test
```

Use the containerized environment for PostgreSQL/Redis-sensitive behavior.

## 11. Documentation rules

Update documentation only when you change a durable truth:

- roadmap priority/gate → `docs/ROADMAP.md`
- architecture boundary → `docs/architecture/ARCHITECTURE.md` and ADR if decision-level
- current feature/API contract → `docs/SPECS.md`
- unresolved debt → `docs/TECHDEBT.md`
- reusable lesson → `docs/MISTAKES.md`

Do not append session state to `CLAUDE.md` and do not create competing status files.
