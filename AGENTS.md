# IAmina — Codex Session Memory

## Current Branch
dev

## Quick Start
```bash
./dev.sh        # setup (first run) + backend + frontend
./run.sh        # backend only (VM / production)
```

## Session State (2026-06-07 — P6-A + P8.1 + audit port, all on dev)
- **All merged to `origin/dev`** (P4.5, P6-A, P8.1) + local audit-port commit `0dcbd44`.
- **P6-A DONE (Flutter module seam):** `frontend/lib/modules/` ModuleConfig + ModuleRegistry +
  diabetesModule; app_router + MainShell generate routes/nav from the registry (integer-index
  switch removed, MISTAKES #16); `ModulesProvider` makes nav reactive to `GET /account/modules`
  with offline fallback. Renders identically (one module). `flutter analyze` clean. Plan:
  `docs/architecture/platform_p6_flutter_multimodule_PLAN.md`. P6 A3/A6/A7 + P6-B deferred → P7.
- **P8.1 DONE (pulled forward):** `backend/.importlinter` + CI step enforce the seams.
  2 contracts: companion⊥modules (strict, KEPT), core⊥modules (KEPT via debt allow-list).
- **Audit port (`0dcbd44`):** `core/audit.py` removes the `core/account → diabetes.AuditLog`
  leak. core→diabetes debt now **2** (auth→DiabetesProfile, triage→classifier).
- **Tests:** backend 764 passed / 3 xfailed; import-linter 2 kept / 0 broken.
- **Next actionable (single-module value):** auth→DiabetesProfile lazy-creation fix (login-path,
  careful), then route diabetes engine→llm via gateway + re-enable the llm contract.
- Gated: P7 (D90 retention), P7.4 (DetectorRegistry), P7.5 (companion→core + table moves), P6-B.

## Session State (2026-06-06 — P4.5 Companion Engine Contract COMPLETE)
- **Focus: P4.5 — converge companion onto the single `analyze()→DomainContext` contract.**
  Completes the master plan's P4.2 (marked done previously but never wired). Renumbered from
  the interim "P6.5 seam" after reviewing `platform-transformation-plan.md`.
- **P4.5 DONE:** ONE module→chassis clinical contract.
  `BaseEngine.analyze(patient_id, language, days) → DomainContext` (engine fetches own data;
  old DA-03 entries/kpis signature removed) + `evaluate_alert(entry, language)`.
  `DomainContext` enriched (tone_signals, has_sufficient_data, trend, primary_label,
  patterns_detail, empty()); new `DomainAlert` contract. `core/companion/clinical.py`
  resolves the active engine via `ModuleRegistry` + caches `analyze()` (replaces
  `session_cache`, which is now an invalidation shim — fixed stale-context-after-log bug).
  companion (conversation/state/narrator/core) consumes `DomainContext`. **Kept** non-clinical
  persistence ports (SnapshotStore, ConversationStore) in `core/companion/ports.py` +
  `diabetes/companion_adapters.py`. The 3 interim clinical ports were removed.
  Branch `feat/p4.5-companion-engine-contract`: seam `c643cd4`,`1bd7757`; converge `5511195`.
  **764 passed, 3 xfailed.** Plan:
  `docs/architecture/platform_p4.5_companion_engine_contract_PLAN.md`.
- **Deviation:** `ai.py` summary/doctor-brief keep `run_clinical_analysis` (analytical
  endpoints, not the companion path) — documented in the P4.5 plan + master plan.
- **Next: P6 (Flutter multi-module). P7.5 = physically move companion/ → core/ + table moves.**
- No DB migrations in P4.5 (models stay in diabetes; relocation = P7.5).
- companion/ imports zero module code — enforced by package-wide seam guard in
  `core/tests/test_companion_ports.py`.

## Session State (2026-06-05 — P0 + P1 + P2 + P3 COMPLETE)
- **Focus cette session : implémentation P3 — Module Registry + Chassis Router.**
- **P0 DONE:** ADR-0008, DomainContext→CompanionIdentity rename, core/contracts/ (ModuleManifest, ModulePatientContext, DomainContext, CompanionIdentity), module-contract-spec.md
- **P1.1 DONE:** AppendOnlyTriageRegistry, TriageVitalMiddleware → core/middleware/, DiabetesConfig.ready() registre /api/v1/ai/chat
- **P1.2 DONE:** on_account_delete hooks, Firebase deletion, ErasureRecord model + migration 0003
- **P1.3 DONE:** PHIPseudonymizer étendu (last_name, DOB, CIN regex), PHIStrippingMiddleware, 4 callsites audités
- **P1.4 DONE:** core/llm_gateway.py narrate() — seul point d'entrée LLM sanctionné. 4 callsites restants déférés à P4 (companion layer).
- **P2 DONE:** core.BasePatientProfile + diabetes.DiabetesProfile + core.PatientModule split. SeparateDatabaseAndState migration (diabetes.0017) preserves diabetes_patientprofile table. All callsites migrated. Backward-compat alias PatientProfile = DiabetesProfile. 720+ tests passing.
- **P3 DONE:** ModuleRegistry + chassis router. core/registry.py. diabetes/manifest.py DIABETES_MANIFEST. Dynamic router loop in diabetes/api/main.py. POST /api/v1/account/modules/{name}/activate + GET /api/v1/account/modules. require_module() dependency factory. core/migrations/0007 backfill. Both triage paths registered. 731+ tests passing.
- **Tests: 731+ passed, 3 xfailed, 0 failures** (P3 adds 11 new tests in core/tests/test_p3_module_registry.py)
- **emit_inactive_events bug fix:** date.today() → timezone.localdate() (timezone consistency)
- Active blocker: Kimi `KIMI_API_KEY` pending.
- Known bug (unchanged): demo data stale after ~14 days → `setup_demo --reset` before demos (MISTAKES #22).
- Note: `export_openapi` needs `django-redis` (already in requirements.txt; venv may need `pip install -r` if it errors with "No module named 'django_redis'").

## Architecture (locked — see docs/adr/ + docs/architecture/new-architecture.md)
- Monorepo: Flutter frontend + Django Ninja backend
- **v4.0: Platform chassis + modules (APPROVED_WITH_CONDITIONS 2026-06-04). P0+P1 complete.**
  ADR-0008 written. Core contracts defined. Security foundations in place.
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
- Update "Session State" before closing
- If decision conflicts with ADR, STOP and ask
- `docs/MISTAKES.md` is mandatory — read at session start, update on new errors
- Never modify middleware order without explicit approval

## Session Workflow
1. **Start:** Read AGENTS.md + docs/MISTAKES.md + docs/ROADMAP.md
2. **Execute:** Work on assigned task only
3. **Test:** Run Django check + flutter analyze before closing
4. **Document:** Update session state, add to docs/MISTAKES.md if new error found
5. **Close:** Commit with type(scope): description format

## Commit Format
```
feat(scope): description
fix(scope): description
chore(scope): description
docs(scope): description
```
