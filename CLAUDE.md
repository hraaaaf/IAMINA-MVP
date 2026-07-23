# IAmina — Claude Code Session Memory

## Current Branch
dev

## Quick Start
```bash
./dev.sh        # setup (first run) + backend + frontend
./run.sh        # backend only (VM / production)
```

## Session State (2026-06-16)
> **Phase status lives in `docs/ROADMAP.md` (Phases 18–26) — the single tracker. Don't duplicate it here.**
> History of the chassis detour: `docs/architecture/ARCHITECTURE-TIMELINE.md`. Detailed build
> record: `docs/architecture/platform-transformation-plan.md` (archived).
- **Branch:** `dev` is the integration branch; latest chassis work (P6-A + P8.1 + audit port) merged at `d96ae44`.
- **Tests:** backend 764 passed / 3 xfailed; import-linter 2 kept / 0 broken.
- **Next actionable (single-module value):** auth→DiabetesProfile lazy-creation fix (login-path,
  careful), then route diabetes engine→llm via `core/llm_gateway` + re-enable the llm import-linter
  contract. (ROADMAP → "Platform seam debt".)
- **Gated:** P7 (D90 retention), P7.4 DetectorRegistry, P7.5 (companion→core + table moves), P6-B URL namespacing.
- **Active blocker:** Kimi `KIMI_API_KEY` pending (blocks the Gemini→Kimi LLM cutover).
- **Known bug:** demo data stale after ~14 days → `setup_demo --reset` before demos (MISTAKES #22).
- **Note:** `export_openapi` needs `django-redis` (in requirements.txt; `pip install -r` if it errors "No module named 'django_redis'").

## Architecture (locked — see docs/adr/ + docs/architecture/ARCHITECTURE.md)
- Monorepo: Flutter frontend + Django Ninja backend
- **Platform chassis + modules (ADR-0008, 2026-06-04). Chassis built: P0–P6 + P8.1 merged on `dev`.**
  One live module (diabetes); second module gated behind the Retention Gate (ROADMAP Phase 25).
- **Strategy: Darija/Arabic diabetes companion (not medical-device). Morocco = beachhead,
  Gulf + pharma B2B = monetization. #1 metric = 90-day retention** (Phase 16 = top priority).
- Backend: Django 6.0.3 + django-ninja + Firebase Admin SDK
- Frontend: Flutter/Dart — GoRouter 14, Drift 2.20, Provider
- Auth: Firebase Auth (JWT) → Django custom backend
- DB dev: SQLite | DB prod: PostgreSQL
- LLM current: Gemini 2.5 Flash (active)
- LLM target: Kimi 2.5 Moonshot (Phase 5 — pending API key)
- Platforms: PWA + iOS + Android (Windows not configured)
- **core/contracts/:** ModuleManifest, ModulePatientContext, DomainContext, CompanionIdentity
- **core/registry.py:** ModuleRegistry + RegisteredModule — chassis module registry (P3)
- **core/llm_gateway.py:** narrate() — sole sanctioned LLM entry point
- **core/safety_registry.py:** AppendOnlyTriageRegistry + TRIAGE_REGISTRY singleton
- **core/middleware/triage_vital.py:** TriageVitalMiddleware (moved from diabetes/middleware/)
- **diabetes/manifest.py:** DIABETES_MANIFEST frozen dataclass (P3)

## Critical — Never Touch Without Explicit Order
- `TriageVitalMiddleware` — medical emergency gate, never bypass
- `UnitGuardMiddleware` — glucose unit normalization, upstream of all AI logic
- `client_uuid` on `LogEntry` — offline sync idempotency
- `BasePatientProfile.firebase_uid` — bridge Firebase Auth ↔ Django User (P2: moved from PatientProfile to chassis)

## Conventions (enforced)
- KPIs: SQL-first, never Python-computed (ADR-0007)
- LLM input: English Pivot Text only, never raw patient data
- Offline-first: Drift local → batch sync via SyncService
- Error handling: `except Exception → log → FallbackProvider` (static template); `QuotaExhaustedProvider` when Gemini daily cap hit
- Medical urgency: fixed pre-validated response, never routed to LLM
- Priority order: Security > Integrity > Performance > Style
- Code principles: SOLID, DRY, KISS — no premature abstraction

## Known Technical Debt
### Blocking deployment
- [x] firebase-credentials.json exposed in repo (REVOKED)
- [x] SECRET_KEY hardcoded default → now raises ValueError
- [x] CORS_ALLOWED_ORIGINS unrestricted → validation added
- [x] Demo credentials hardcoded → now String.fromEnvironment
- [x] .env duplicated → consolidated to project root

### Next sprint
- [x] Flutter API URL hardcoded → String.fromEnvironment('API_BASE_URL')
- [x] Drift MigrationStrategy added (schemaVersion 3, v1→v2→v3)
- [x] Edit + delete log entries (swipe-to-delete, tap-to-edit)
- [x] mmol/L conversion on save
- [x] SSE streaming chat
- [x] IAminaMemorySnapshot — DB persistence for IAmina memory
- [x] AuditLog + RGPD endpoints (consent, DELETE /account)
- [x] AGP real percentiles (PERCENTILE_CONT PG / Python linear interpolation SQLite)
- [x] Gemini rate-guard → QuotaExhaustedProvider → Kimi failover
- [x] Sprint 4 Flutter: IAmina post-save sheet, sleep/fatigue, date picker, danger dialog
- [x] Dashboard UX: seed guard (kDebugMode), dead links wired, touch targets 44px
- [x] P0/P1 clinical engine fixes: insulin prescription removed, CV→ADA 36%, Somogyi≥2, Moroccan foods, top_culprit Counter
- [x] P2-A: Darija (ar-MA) fallback strings all 8 clinical detectors
- [x] P2-B: GMI confidence tiers (high/medium/low/null) + visual badges frontend
- [x] P2-C: AGP real CustomPainter (p5/p25/p50/p75/p95 bands) replacing fl_chart LineChart
- [x] Dockerize backend (Dockerfile + gunicorn)
- [x] docker-compose.yml (Django + Postgres + Redis)
- [x] CI/CD (GitHub Actions: ruff, pytest, flutter analyze) + bandit SAST
- [x] Increase Test Coverage (Target: 70%, Current: ~70% — 232 tests, sql_analytics fully covered)
- [x] S4 — core/observability/ events + ClinicalLogger + emit_inactive_events (672 tests)
- [x] S5 — GET /api/v1/analytics/overview retention dashboard (staff-only)
- [x] P0 — Spec & Decisions (ADR-0008, contracts, rename) — 705 tests
- [x] P1 — Security Foundations (triage registry, RGPD hooks, PHI, gateway) — 705 tests
- [x] P2 — PatientProfile split (BasePatientProfile + DiabetesProfile + PatientModule) — 720 tests
- [x] P3 — Module Registry + Chassis Router (ModuleRegistry, DIABETES_MANIFEST, dynamic routes, activation endpoint) — 731+ tests
- [x] P4.5 — Companion on single analyze()→DomainContext (completes P4.2): enriched DomainContext + DomainAlert, core/companion/clinical.py engine resolver+cache, session_cache retired; companion/ has zero module imports — 764 tests
- [ ] Kimi activation (blocked: API key)
- [x] Dashboard: NavigationBar (ShellRoute) — sidebar + bottom nav redesigned, /ajouter full-screen
- [x] Add Log: express mode (3 taps) vs detailed mode — AnimatedContainer expand toggle

### Refactor
- [x] Dashboard context.watch → context.read
- [x] API Client 401 refresh + 5xx backoff
- [x] KPI deduplication (SQL-only endpoint)
- [x] Firebase mobile config scaffold (stubs)
- [ ] Firebase iOS/Android: real values from Firebase Console
- [ ] Django admin: confirm removal timeline
- [x] S1 — BaseEngine ABC seam in core/engine/base.py (DA-03, faible risque)
- [x] S2 — LLMPipeline + LoggingMiddleware + PHI gaps fix (DA-03, risque moyen)
- [x] S3 — Move account/auth/health endpoints → core/api/v1/ (DA-03, faible risque)

## Open Decisions
- Firebase mobile config: when will firebase_options.dart be configured for iOS/Android?
- Django admin: no timeline set — confirm before deploying
- D90 retention threshold: non fixé (placeholder ≥25% dans ROADMAP) — à confirmer quand données réelles disponibles
- [x] PatientProfile split (P2 DONE): core.BasePatientProfile (chassis identity) + diabetes.DiabetesProfile (module extension) + core.PatientModule (junction table). Backward-compat alias PatientProfile = DiabetesProfile removed in P3.

## Rules
- Read this file at start of every session
- **`docs/ROADMAP.md` is the single backlog + status tracker** — pick the next unstarted unit from it; never duplicate its phase status here
- **Replace** the "Session State" block before closing — never append a new one (that's how it drifted to 3 stacked blocks)
- Handoff lives in git (branch + PR + ROADMAP checkboxes), not a separate status file — see `docs/CONTRIBUTING.md` → "Working in parallel"
- If decision conflicts with ADR, STOP and ask
- `docs/MISTAKES.md` is mandatory — read at session start, update on new errors
- Never modify middleware order without explicit approval

## Session Workflow
1. **Start:** Read CLAUDE.md + docs/MISTAKES.md + docs/ROADMAP.md; `git checkout dev && git pull`
2. **Execute:** One unit from ROADMAP → one short-lived branch off `dev` → one small PR
3. **Test:** Run Django check + flutter analyze before closing
4. **Document (2 steps):** tick the ROADMAP checkbox(es); refresh (replace) this file's Session State block
5. **Close:** Commit with type(scope): description format

## Commit Format
```
feat(scope): description
fix(scope): description
chore(scope): description
docs(scope): description
```
