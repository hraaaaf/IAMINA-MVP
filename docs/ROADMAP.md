# IAmina — Roadmap

> Last updated: 2026-07-23 (MENA, sovereignty and LLM data-egress strategic reset)
> Stack: Flutter (web + iOS + Android) · Django Ninja · Django-native auth target (Firebase legacy during migration) · SQLite → PostgreSQL
>
> **This file is the single forward tracker.** `docs/architecture/platform-transformation-plan.md`
> (the P0–P8 chassis detour) is now archived/reference — its completed work lives here as Phases 18–26.

---

## ▶ Next Up — the working backlog

> **Pick top-down. One item = one small branch off `dev` = one small PR** (see CONTRIBUTING).
> The numbered Phases below are the detailed record; *this* is the live pick-list. The phase
> numbers are historical — forward-critical work (14–16) predates the chassis detour (18–26),
> so don't read the numbers as priority. Read this list as priority.
### Strategic reset — MENA sovereignty (founder decision, 2026-07-23)

The target is now the **MENA region**, while keeping **diabetes as the only live condition**.
The product must ask each user for one or more languages/dialects and may use location only to
**suggest** relevant choices; location must never silently determine language, dialect, clinical
content, emergency resources, or consent. The baseline choices are French, Modern Standard Arabic
and English, extended by a country-specific dialect catalogue validated by native reviewers.

The target identity stack is **Django-native authentication**. Firebase remains legacy infrastructure
only until an explicit account-preserving migration is designed, tested and executed. The target AI
model is provider-agnostic: IAmina's deterministic engine decides; text models only verbalize an
approved structured result. STT and vision may use different providers or local/on-device models.

**P0 ordering for this reset:**

1. **P0-MENA-1 — stop uncontrolled model data egress.** Inventory every text, stream, reasoning,
   STT, vision and document-extraction call; route them through one enforceable outbound boundary;
   default-deny fields and media; require purpose, consent, minimization, redaction, retention and
   subprocessor metadata; add a CI rule preventing direct provider imports/calls outside that boundary.
2. **P0-MENA-2 — define the locale and safety contract.** Model country/region, UI languages,
   response language, script/transliteration preference and dialects separately. Add deterministic
   fallback to MSA/English/French, RTL coverage, units/time zone, country-specific emergency resources,
   and native-speaker parity tests for every safety rule before enabling a locale.
3. **P0-MENA-3 — migrate sovereignty-critical authentication.** Specify Django account lifecycle,
   session/token strategy, verification, password reset, abuse controls, account recovery and deletion;
   map existing Firebase identities; migrate without duplicate/lost accounts; replace Flutter Firebase
   dependencies and token handling only after rollback and account-reconciliation tests exist.
4. **P0-MENA-4 — benchmark the multimodal stack.** Evaluate text, STT and vision independently on
   privacy/data residency, contractual no-training/no-retention terms, MENA language/dialect quality,
   latency, availability and cost per active patient. No provider cutover is approved before this benchmark.

**Data-egress acceptance gate:** no model provider receives name, email, phone, Django/Firebase UID,
national identifier, date of birth, address, raw conversation history, raw clinical logs, or unrelated
health data. Raw audio/images are blocked by default because external STT/vision necessarily discloses
their contents; each allowed media flow needs explicit consent, a documented processor, strict retention,
and proof that only the minimum required media is transmitted.

**The critical path is now:** close uncontrolled model egress → define MENA locale/safety contract → migrate auth sovereignty → benchmark multimodal providers → deploy → measure D90 → decide.
Nothing else tells us whether this is a business.

> **Scope discipline — protect the MVP.** "MVP up and running" = a **deployed, safety-equivalent
> MENA pilot** in a founder-selected first country/cohort, in **~30 real patients'** hands and **measuring
> retention.** A country or dialect cannot enter the pilot until its locale, emergency-resource, privacy and
> native-review gates pass. Only items required for *that* are in **NOW**. Everything else (hardening, refactors, quality) is deliberately deferred to
> **SOON** or **TECHDEBT** — do not pull it forward. (Source for the new items below: the Fable
> assessment, `docs/assessments/2026-06-12-*`.)

### NOW — secure the MENA foundation, then ship a measurable MVP
0. **Step 0 — the app runs reproducibly on every dev machine (Docker dev env).** `docker compose up`
   boots backend + Postgres + Redis identically on macOS/Windows (dev override: runserver, port 8001,
   demo seed). Fixes the per-OS launcher drift, Redis-not-started, and the Python-version drift in one
   move (the container pins 3.12). *Frontend still runs on host — install Flutter via `mise` (`.tool-versions`).
   This is the precondition for everything below.*
1. **Phase 14 — deploy backend to staging** — host (Railway/Render/VPS) + PostgreSQL + Redis + domain + SSL + smoke test. *Prelaunch blocker.*
2. **P0-MENA-1 through P0-MENA-4** — data-egress boundary, locale/safety contract, Django-auth migration, then multimodal benchmark. *Prelaunch blockers.*
3. **Phase 16 — turn on the retention dashboard against real users** (infra already built).
4. **Founder — set the D90 go/stop threshold** (provisional 25% is fine; a real gate beats a placeholder).
5. **Pilot locale implementation** — implement the selected first-country language/dialect set, user confirmation, RTL, units, time zone, TTS/STT mapping, emergency resources and deterministic safety-equivalence tests. Additional countries remain disabled until they pass the same gate.
6. **Pilot recruitment** — select the first MENA country/cohort, then recruit ~30 real patients through a clinically supervised channel (founder — see Business / Validation). Starts the only clock that matters.

### Pilot Safety Hardening — before first real patient

> Emergency hardening checklist. These items must be complete or explicitly deferred before recruiting a real patient.
> Status source: local hardening session, pending Achraf review and final app verification.

#### DONE locally / pending review

* [x] `.env` and `backend/.env` confirmed gitignored.
* [x] Medical safety flags documented in env examples:
  `MEDICAL_PILOT_MODE`, `LLM_MEDICAL_STREAMING`, `ALLOW_INSULIN_ADVICE`, `ALLOW_DIAGNOSIS`.
* [x] `core/medical_safety.py` strengthened with no-prescription output policy and insulin-dose input detection.
* [x] Medical safety tests expanded to cover output patterns and insulin-dose input detection.
* [x] `GET /api/v1/ai/doctor-brief` output filtered with `apply_no_prescription_policy()`.
* [x] Companion chat now blocks insulin-dose requests before LLM call.
* [x] Local smoke test passed:
  backend health OK, SQLite OK, frontend launched locally.
* [x] Manual safety test confirmed no insulin dose was returned.

#### P0 before pilot

* [ ] Re-test insulin-dose blocker in frontend after restart and confirm deterministic refusal latency.
* [ ] Add focused companion test proving insulin-dose blocker avoids LLM call.
* [ ] Add focused doctor-brief endpoint test proving output filtering is applied.
* [ ] Route remaining direct `get_llm()` callsites through `core/llm_gateway.py` or explicitly document why they remain isolated.
* [ ] Enforce AI/LLM consent at gateway level before provider calls.
* [ ] Add LLM timeout / streaming timeout protection.
* [ ] Add frontend timeout/error UX for LLM failures.
* [ ] Create CNDP readiness pack under `docs/compliance/`.
* [ ] Create consent matrix and subprocessor list.
* [ ] Document LLM data processing and cross-border transfer assumptions.
* [ ] Implement data export endpoint.
* [ ] Define data retention policy and deletion schedule.
* [ ] Define incident response / escalation procedure.
* [ ] Route emergency events to a monitored pilot channel or explicitly choose self-care-only mode.
* [ ] Create 30-patient pilot checklist: recruitment, onboarding, monitoring, escalation, exit criteria.

#### Not for this phase

* No public launch.
* No real patient pilot.
* No GitHub push before Achraf manual verification.
* No new product modules.
* No gateway refactor unless covered by a focused hardening task.

> **⚠️ Hard safety gate — must clear before a single real patient (see CONTRIBUTING → Guardrails):**
> (a) **close the existing Darija orthographic-variant suicidal-ideation `xfail`** and require an equivalent native corpus/review gate for every newly enabled language or dialect;
> (b) **route ClinicalLogger emergency events to a monitored alert channel** (today they fire into an unread log).

### SOON — harden before public/GA (parallelizable, NOT blocking the MVP)
- **Security debt:** login rate-limiting (TECHDEBT TD-014) + MFA for staff (TD-012) — before *public* exposure (not the closed pilot).
- **Phase 8 — Flutter widget/integration tests** (backend ~70%; frontend is the gap).
- **Retire `dev.sh`/`dev.ps1`** once the Docker dev env (NOW Step 0) is validated on both OSes → thin wrappers or delete; update README/ONBOARDING.
- **Multimodal provider benchmark → provider selection** (text, STT and vision evaluated separately; privacy and cost gates apply before cutover).
- **Platform seam debt** (single-module value): auth→DiabetesProfile lazy creation; route engine→llm via gateway + re-enable the llm import-linter contract.
- **P5.4** — move analytics endpoint → `core/api/v1/` (cosmetic).

### 💼 Business / Validation — founder-owned, runs in parallel, does NOT block dev
> The dev MVP and these can proceed at once. Tracked here so the GTM gaps are visible; log outputs in `docs/` like ADRs. (Fable business review, 5.7/10 — "the business has not started.")
- [ ] **One-page monetization memo** — pricing hypothesis per channel + LLM cost-per-active-patient + 3 named pharma/clinic/insurer targets.
- [ ] **One-page competitive landscape** — mySugr, Droobi, GluCare, generic LLM chat → "why IAmina wins across selected MENA language/dialect cohorts."
- [ ] **5 market conversations** — 3 endocrinologists/pharmacists (distribution) + 2 pharma patient-support managers (payer); logged.
- [ ] **Re-source the `[unverified]` market figures** in the Fable business assessment before any external/investor use.

### ⛔ GATED — do NOT start until the Retention Gate passes (D90 ≥ threshold + one payer signal)
- Phase 25 (P7 hypertension module) · Phase 26 (P8.2–8.4 third-party infra) · P6-B (URL namespacing).

---

## Product Strategy (reset 2026-07-23)

**The product:** a MENA diabetes **companion** (not a medical-device app — no diagnosis or treatment, for now). One condition: diabetes. IAmina's deterministic engine decides; external models may only render an approved, minimized result or perform an explicitly permitted media task.

**The market:** MENA is the target region. French, Modern Standard Arabic and English form the baseline; country dialects are user-selected from location-informed suggestions. Country rollout remains gated by safety-language parity, emergency-resource accuracy, privacy/compliance readiness and native-speaker validation.

**The metric that decides everything:** **90-day retention.** Diabetes apps churn 70–80%+. The companion design is the one thing that could beat that — unproven until measured. See the **Retention Gate** below.

**Not doing (deliberately):** worldwide language coverage, a *live* second condition, or a 3rd-party plugin marketplace. MENA expansion does not authorize a second disease module or broad platform scope before the Retention Gate passes.

---

## Architecture Decisions (locked)

**DA-01 — Flutter is the only frontend.**
Django templates and views are fully removed. All UI is Flutter (web + mobile). Backend exposes `/api/*` (Ninja) and `/admin/` only.

**DA-02 — Target stack.**
- Backend: Django 6.0.3 + django-ninja + PostgreSQL + Redis
- Frontend: Flutter — GoRouter 14, Drift 2.20, Provider
- AI: Gemini 2.5 Flash is current legacy runtime; target is a provider-agnostic, privacy-gated text/STT/vision stack selected by the P0-MENA-4 benchmark
- Communication: JSON/HTTPS + SSE for streaming

**DA-03 — Modular monolith with extension seams, NOT a platform.** (2026-06-03)
Ship ONE condition (diabetes) with cheap seams (`BaseEngine` ABC, `BasePatientProfile`) so a second condition is a future refactor, not a rewrite. Do NOT build platform machinery (plugin API, `EngineRegistry` dispatch, webhooks, multi-tenancy) — premature pre-revenue. Redirect that budget into observability/retention instrumentation. Full record: `docs/architecture/ARCHITECTURE-TIMELINE.md`. Supersedes the v2.x/v3.0 multi-capsule platform direction (kept as historical context, not build targets).

> **⚠️ SUPERSEDED (2026-06-04) by ADR-0008.** The founder reversed DA-03: the platform **chassis**
> (module registry, contracts, PatientProfile split, import-linter) WAS built — see Phases 18–26 and
> `docs/architecture/platform-transformation-plan.md` (now archived/reference). DA-03's *strategic*
> core still holds: **one condition live, retention-first, no second module until the gate passes.**
> What changed: the cheap seams became real seams. What did NOT change: nothing past the Retention
> Gate (P7 / Phase 25+) gets built.

See `docs/adr/` and `docs/architecture/ARCHITECTURE-TIMELINE.md` for full decision records.

---

## Retention Gate (the go/stop decision)

Do NOT build condition #2 or any platform machinery until **both** are true:

1. **90-day retention** ≥ go threshold _(set explicitly — e.g. ≥ 25% D90 cohort; founder to confirm)_.
2. **One named payer signal** — Gulf consumer traction, a pharma adherence pilot, or an insurer LOI.

Until then, extensibility is a one-line future slide, not a build target. Adding conditions multiplies surface area without solving who-pays.

---

## Current Status

```
Phase 1   Security hardening              ✅ complete
Phase 2   LLM pipeline unification        ✅ complete
Phase 3   Django HTML purge               ✅ complete
Phase 4   SQL analytics                   ✅ complete
Phase 5   Flutter bug fixes               ✅ complete (Kimi key pending)
Phase 6   Clinical Shield                 ✅ complete
Phase 6b  Sprint 2–4 (memory/RGPD/UX)    ✅ complete
Phase 6c  Clinical Engine P0/P1/P2        ✅ complete
Phase 7   DevOps / Docker                 ⏸️ on hold (staging runbook pending)
Phase 8   Tests                           🟡 in progress (764 backend / 3 xfailed, ~70%; frontend TBD)
Phase 9   RGPD compliance                 ✅ complete
Phase 10  Performance                     ✅ complete
Phase 11  Saisie intelligente             ✅ complete
Phase 12  Document Pulper                 ✅ complete
Phase 13  IAmina Conscience               ✅ complete (deep memory + state engine + thinking)
Phase 14  Déploiement staging             🔴 not started ← PRELAUNCH BLOCKER
Phase 15  Firebase iOS/Android            🔴 not started ← PRELAUNCH BLOCKER
Phase 16  Observability / Retention       🟡 infra ✅ built — measurement blocked on deploy+users
Phase 17  Extension seams (v3.1)          ✅ expanded into Phases 18–26 (platform chassis, ADR-0008)
Phase 18  P0 Spec & contracts             ✅ complete
Phase 19  P1 Security foundations         ✅ complete
Phase 20  P2 PatientProfile split         ✅ complete
Phase 21  P3 Module registry + router     ✅ complete
Phase 22  P4/P4.5 LLM generalization      ✅ complete (P4.3 → Phase 25)
Phase 23  P5 Observability+sync general.  🟡 P5.1–5.3 done · P5.4 (analytics→core/) not done
Phase 24  P6 Flutter multi-module         🟡 A done · B deferred → Phase 25
Phase 25  P7 Hypertension module          ⛔ GATED (Retention Gate + payer signal)
Phase 26  P8 3rd-party infra              🟡 P8.1 done (import-linter) · rest gated
```

> **The platform CHASSIS was built** (Phases 18–26, ADR-0008) as a scoped, gated detour — registry,
> contracts, profile split, import-linter. **What stays SHELVED:** a live second module (Phase 25 / P7),
> the 3rd-party marketplace (P8.2–8.4), multi-tenancy. The v2.x/v3.0 multi-capsule docs remain
> historical context, not targets. The real forward path is now **Phase 14 deploy → users →
> measure D90 (Phase 16 infra ready) → set the threshold** — not more extensibility machinery.

---

## Phase 1 — Security ✅

- [x] Revoke exposed Gemini key, rotate to `.env`
- [x] `SECRET_KEY` raises `ValueError` if absent (no hardcoded default)
- [x] `ALLOWED_HOSTS` explicit list, no `*`
- [x] `CORS_ALLOWED_ORIGINS` restricted to explicit origins
- [x] Demo credentials moved to `String.fromEnvironment` (no hardcoded values)
- [x] `.env` structure consolidated to project root (backend/.env removed)
- [x] `PHIPseudonymizer` hardened with word-boundary regex

---

## Phase 2 — LLM Pipeline ✅

- [x] Remove dead `_call_llm_for_chat()` and `_fallback_chat_reply()` duplicates
- [x] Migrate `summary.py` from Anthropic → Gemini, remove `anthropic` dep
- [x] Remove `google-generativeai==0.8.*`, keep only `google-genai`
- [x] Unified chat pipeline via `ai_chat.generate_ai_response`
- [x] `FallbackProvider` as static last resort (no API key needed)

---

## Phase 3 — Django HTML Purge ✅

- [x] Remove `tracking/views/`, `backend/templates/`, `backend/static/`
- [x] Remove `tailwind.config.js` and Tailwind binary
- [x] Clean `amina/urls.py` to API + admin routes only
- [x] Remove `whitenoise`, `django.contrib.humanize`, `django.contrib.messages`

---

## Phase 4 — SQL Analytics ✅

- [x] Migrate dev DB SQLite → PostgreSQL (infrastructure ready)
- [x] Enable `STDDEV_SAMP` and `CV%` in `sql_analytics.py` (PostgreSQL only)
- [x] Remove redundant KPI calculations in `engine.py` (already in `sql_analytics`)
- [x] `sql_analytics.compute_kpis()` becomes single source of truth for all KPIs

---

## Phase 5 — Flutter Bug Fixes ✅

- [x] `dashboard_screen.dart`: `context.watch` → `context.read` for non-reactive calls
- [x] `sync_service.dart`: null guard on `fatigueLevel`
- [x] `api_client.dart`: `API_BASE_URL` via `--dart-define` (no hardcoded URL)
- [x] `api_client.dart`: 401 token refresh + 5xx exponential backoff
- [x] Drift `MigrationStrategy` added (schema v1→v2→v3)
- [x] Edit + delete log entries (swipe-to-delete, tap-to-edit)
- [x] mmol/L conversion on save
- [x] SSE streaming chat (Django `StreamingHttpResponse` + Flutter `Stream<String>`)
- [ ] Kimi 2.5 activation (blocked: API key not obtained)

---

## Phase 6 — Clinical Shield ✅

- [x] `"mort"` pattern → `r"\bmort\b"` (prevent false positives on "mortalité")
- [x] Output filter on LLM responses (not just input)
- [x] Rate limiter: max 20 AI requests / patient / hour
- [x] Medical disclaimer on every AI response (legal requirement)

## Phase 6b — Sprint 2–4 (Memory / RGPD / UX) ✅

- [x] `IAminaMemorySnapshot` — DB fallback when cache cold (2-level persistence)
- [x] `_trim_history()` — compressed older-messages summary (budget 3000 chars)
- [x] `compute_trend()` — week-over-week TIR delta + direction
- [x] `detect_postmeal_spike()` — 8th clinical detector (+60 mg/dL within 2h of meal)
- [x] AGP real percentiles: `PERCENTILE_CONT` (PG) / Python linear interpolation (SQLite)
- [x] `GuardedGeminiProvider` + `QuotaExhaustedProvider` — daily cap with user-facing message
- [x] Kimi failover chain in LLM factory
- [x] Sprint 4 Flutter: `_IaminaPostSaveSheet`, `_sleepQuality`/`_fatigueLevel`, date picker, danger dialog, `PopScope`
- [x] Dashboard UX: seed guard (`kDebugMode` only), dead links wired, touch targets 44px

## Phase 6c — Clinical Engine P0/P1/P2 ✅

- [x] P0: Insulin prescription removed from `detect_food_sensitivity` fallback action (safety)
- [x] P0: CV threshold corrected to ADA 36% (`sd/mean×100 > 36`, was flat `sd > 50`)
- [x] P1: Somogyi threshold raised to ≥ 2 rebounds (was ≥ 1)
- [x] P1: Moroccan food vocabulary added (harira, msemen, rfissa, pastilla, etc.)
- [x] P1: `top_culprit` fixed to use `Counter.most_common(1)` (was positional index)
- [x] P2-A: Darija (ar-MA) fallback strings for all 8 clinical detectors
- [x] P2-B: GMI confidence tiers (high/medium/low/null) + visual badges in Flutter
- [x] P2-C: AGP CustomPainter — real p5/p25/p50/p75/p95 bands (fl_chart LineChart removed)
- [x] IAmina JSON key mismatch fixed (`"response"` alias → `"reply"`, `strip_fences()`)
- [x] Gemini Flash Lite → Flash for reliable JSON schema following
- [x] Navigation fixes: sidebar `_navigate()` remapped, `/ajouter` full-screen, profile in bottom nav
- [x] `ApiClient` default port corrected (8001 → 8000)

---

## Phase 7 — DevOps ⏸️ on hold

> Staging runbook + GitHub Secrets documentation en attente de décision avec l'associé.

- [x] `Dockerfile` for backend (Python 3.12, gunicorn, non-root, multi-stage)
- [x] `docker-compose.yml` with django + postgresql + redis + healthchecks
- [x] `.github/workflows/ci.yml`: ruff + django test + flutter analyze + Bandit SAST
- [x] `GET /api/v1/health` liveness probe (DB + cache status, 503 when DB down)
- [x] `SECURE_SSL_REDIRECT = not DEBUG` in production
- [ ] GitHub Secrets documentation (`.env.example` with all required vars) ← **en attente**
- [ ] Staging deploy runbook ← **en attente**

### Docker as the standard local dev environment (planned — retire `dev.sh`/`dev.ps1`)

> **Why:** today there are two hand-maintained per-OS launchers (`dev.sh` macOS, `dev.ps1`
> Windows) that have already **drifted** — `dev.ps1` auto-starts Redis + kills stale backends,
> `dev.sh` does neither — so the two devs get different local environments. The Docker infra
> already exists (backend `Dockerfile` + `docker-compose.yml`: db+redis+backend, hot-reload,
> healthchecks). Promoting `docker compose` to the single dev path kills the drift and makes
> dev≈prod (exercises PG-only SQL). Frontend stays on host (`flutter run`). **Not started — do
> not change the launchers until this is validated on both OSes.**

- [ ] `docker-compose.override.yml` for dev (runserver, align port, demo-seed convenience)
- [ ] Align backend port — compose = `8000`, current launchers + frontend `API_BASE_URL` = `8001`
- [ ] Mount Firebase creds into the container (`FIREBASE_CREDENTIALS_PATH` → mounted path)
- [ ] Document first-run: `docker compose up --build` + `docker compose run backend python manage.py setup_demo`
- [ ] DB parity: dev moves SQLite → Postgres (demo seed + migrations run in-container)
- [ ] Validate full loop (backend-in-Docker ↔ Flutter-on-host) on **macOS and Windows**
- [ ] Retire `dev.sh` + `dev.ps1` → thin wrappers or delete; update README/ONBOARDING/CONTRIBUTING to the single path
- Also reconcile the tooling version mismatch found 2026-06-16: `.tool-versions` (Flutter 3.41.7 / Python 3.10.4) vs CI (Flutter 3.41.0 / Python 3.12)

---

## Phase 8 — Tests 🟡

Current: 764 backend tests passing / 3 xfailed (~70% coverage). Frontend minimal.

- [x] 764 backend tests (clinical engine, LLM factory, deep memory, state engine, thinking, chassis/platform)
- [x] LLM calls mocked — fast suite, no quota consumption
- [x] `sql_analytics.py` fully covered
- [ ] `ClinicalShield` tests (false positives, true positives, edge cases)
- [ ] Flutter widget tests for `AminaChatView` with mocked `ApiClient`
- [ ] Flutter integration tests for navigation
- [ ] Target: ≥ 70% backend ✅, ≥ 60% frontend 🔴

---

## Phase 9 — RGPD Compliance ✅

- [x] Right to erasure (RGPD Article 17): `DELETE /api/v1/account` with confirmation
- [x] Explicit AI consent endpoints: `GET/POST/DELETE /api/v1/account/consent`
- [x] `ai_consent_given_at` timestamp on PatientProfile (Art. 7)
- [x] `AuditLog` model — immutable, SET_NULL on user delete, IP hashed (SHA-256)
- [x] Consent gate in Flutter: `ConsentScreen` + `ConsentService` + GoRouter redirect
- [x] "Withdraw AI consent" in ProfileScreen danger zone
- [ ] Data retention policy: auto-purge logs > 1 year ← nice-to-have, non-bloquant

---

## Phase 10 — Performance ✅

- [x] Redis cache for KPIs — `_kpi_cache_key()` + `invalidate_kpi_cache()` (TTL 5 min)
- [x] API pagination for logs — `GET /api/v1/logs?page=1&page_size=50`
- [x] Session cache for IAmina context — `get_session_context()` (TTL 30 min, 1 SQL/session)
- [ ] CDN for Flutter Web assets ← non-bloquant
- [ ] TimescaleDB evaluation for CGM data (1440 pts/day) ← futur

---

## Phase 11 — Saisie intelligente ✅

> iOS + Android (Flutter natif). Web : OCR via Gemini Vision uniquement (ML Kit exclu).

### 11-A — Mode express (3 taps) ✅
- [x] `bool _expressMode = true` par défaut dans `add_log_sheet.dart`
- [x] En mode express : glycémie + moment uniquement → Save
- [x] Bouton `"+ Détails"` animé (AnimatedContainer) → déplie insuline / aliments / santé
- [x] Desktop (≥720px) → mode détaillé direct

### 11-B — OCR lecteur de glycémie ✅
- [x] `image_picker` + `google_mlkit_text_recognition` dans `pubspec.yaml`
- [x] Bouton caméra dans `_buildGlucoseCard`
- [x] ML Kit on-device (offline) + regex extraction → pré-remplit champ glycémie
- [x] Gemini Vision fallback pour web (`POST /api/v1/ai/analyze-glucometer-image`)

### 11-C — Reconnaissance repas par photo ✅
- [x] Bouton caméra/galerie dans la section aliments (`_runMealAnalysis()`)
- [x] Backend : `POST /api/v1/ai/analyze-meal-image` (Gemini Vision)
- [x] Flutter : pré-sélectionne les chips `_selectedFoods` depuis la réponse JSON
- [x] Fallback si aucun aliment reconnu → message manuel

---

## Phase 12 — Document Pulper ✅

- [x] `POST /api/v1/documents/ingest` — ingestion PDF, DOCX, image, spreadsheet
- [x] Extractors : `pdf` (pdfplumber), `docx` (python-docx), `image` (pytesseract), `spreadsheet` (openpyxl)
- [x] `LabReport` model + `GET /api/v1/documents/` — liste des rapports du patient
- [x] Confirmation flow : `POST /api/v1/documents/confirm/{batch_id}`
- [x] Flutter : `file_picker` + `DocumentModels` + UI d'import
- [x] `DocumentShield` — validation type + taille (15 MB max)
- [x] LLM parsing via `_parse_with_llm()` (factory-aware)

---

## Phase 13 — IAmina Conscience ✅

> IAmina passe de réactive à consciente : mémoire longue, état intérieur, raisonnement caché.

- [x] `IAminaDeepMemory` — mémoire long terme (Redis + DB, TTL 90j)
  - sensibilités alimentaires apprises par EMA depuis les logs
  - streak de logs + record personnel
  - stade relationnel : new → building → trusted → companion
  - événements épisodiques (urgences, jalons)
- [x] `IAminaState` — état intérieur calculé O(1) à chaque appel
  - satisfaction, concern_level, engagement
  - clinical_mood, next_intention, self_note
  - injecté dans le prompt système via `SYSTEM_WITH_STATE`
- [x] Thinking mode (Gemini natif, 2048 tokens)
  - `think_before_reply()` — raisonnement caché avant réponse
  - activé sur messages émotionnels ou concern_level > 0.4
  - jamais affiché au patient, loggé en DEBUG
- [x] Darija Arabic script enforced (حروف عربية, Latin interdit)
- [x] Détection Darija étendue (40+ mots-clés latin transliteration)
- [x] Real Gemini streaming SSE (tokens natifs, plus de time.sleep)
- [x] `reply_language` propagé backend → Flutter TTS
- [x] Suivi proactif — check-in automatique si concern détecté en session précédente
- [x] Migration DB `0016_add_deep_memory`
- [x] 99 nouveaux tests (deep_memory: 26, state: 51, thinking: 22)

---

## Phase 14 — Déploiement staging 🔴

> Bloqué par Phase 7 (runbook) + décision infra avec l'associé.

- [ ] Choisir hébergeur backend (Railway / Render / VPS)
- [ ] Configurer PostgreSQL production + variables d'env
- [ ] Configurer Redis production
- [ ] Build Flutter Web + déploiement CDN
- [ ] Domaine + SSL
- [ ] Smoke test end-to-end sur staging

---

## Phase 15 — Firebase device configuration ⛔ SUPERSEDED (2026-07-23)

> Do not invest further in Firebase device configuration. Firebase remains operational legacy only
> while P0-MENA-3 designs and validates an account-preserving migration to Django-native auth.

- [ ] Freeze new Firebase coupling; inventory backend, Flutter, tests, account deletion and identity-field dependencies
- [ ] Define Django-native authentication and abuse-control contract
- [ ] Build identity mapping, reconciliation, rollback and account recovery test plan
- [ ] Migrate existing users without duplicate or inaccessible accounts
- [ ] Remove Firebase SDK/configuration only after production reconciliation succeeds

---

## Phase 16 — Observability / Retention 🟡 infra built — measurement blocked on deploy + users

> The metric that decides whether this is a business. The instrumentation now EXISTS
> (`core/observability/`); what's missing is real users to measure and a go/stop number.
> See `docs/architecture/ARCHITECTURE-TIMELINE.md`.

- [x] `core/observability/events.py` — `track(event, patient_id, module, **props)`, no PHI in props (S4)
- [x] Instrument events: `LOG_CREATED`, `SESSION_START`, `CHAT_MESSAGE`, `STREAK_CONTINUED`, `STREAK_BROKEN`, `INACTIVE_7D` (S4)
- [x] `core/observability/logging.py` — `ClinicalLogger` (analysis / emergency / llm_call / middleware_intercept)
- [x] Retention SQL: D1 / D7 / D30 / D90 cohort (`retention_sql.py`) + `GET /api/v1/analytics/overview` staff dashboard (S5)
- [x] Drop-off funnel (`funnel_*` counts) + companion engagement (`chat_per_active_patient`) — in `retention_sql.py`
- [ ] **Run it against real cohorts** ← blocked on Phase 14 deploy + live users
- [ ] Set the explicit go/stop D90 threshold (founder decision) ← see Open Decisions

---

## Phase 17 — Extension seams (v3.1) ✅ → superseded by the platform chassis

> The original "cheap seam, not the factory" plan. ADR-0008 (2026-06-04) reversed scope and
> built the full chassis instead. The Phase 17 items below were all delivered (or subsumed) by
> the platform detour — tracked in detail as **Phases 18–26**. Kept here for traceability.

- [x] `BaseEngine` (ABC) — refactored to the `analyze()→DomainContext` contract (Phase 22)
- [x] Pseudonymizer as LLM-pipeline middleware → `PHIStrippingMiddleware` + `core/llm_gateway.py` (Phase 19)
- [x] Universal endpoints moved → `core/api/v1/` (`account.py`, `auth.py`, `health.py`) (S3 + Phase 21)
- [x] `BasePatientProfile` extraction (Phase 20 — done ahead of the gate as part of the chassis detour)
- [ ] URL namespacing `/api/v1/diabetes/*` — still DEFERRED (Phase 24 / P6-B, until condition #2)

---

# Platform Chassis (Phases 18–26) — the ADR-0008 detour

> **Context:** On 2026-06-04 the founder reversed DA-03 and authorized building the platform
> chassis (registry, contracts, profile split) as a scoped, gated detour. P0–P6 + P8.1 shipped
> between 06-05 and 06-07. **Phases 25–26 (live second module, 3rd-party infra) stay GATED behind
> the Retention Gate.** Original program doc (archived): `docs/architecture/platform-transformation-plan.md`.

## Phase 18 — P0 Spec & Decisions ✅ (705 tests)

> No code — resolved naming/type/spec collisions before any chassis code was written.

- [x] ADR-0008 written (founder reversal of DA-03; Retention Gate = second-module trigger)
- [x] `DomainContext` → `CompanionIdentity` rename; new `core/contracts/domain_context.py` `DomainContext` (clinical output)
- [x] `patient_id` typed `int` (Django `User.id`), not UUID
- [x] `ModuleManifest` spec — `docs/architecture/module-contract-spec.md`
- [x] `ModulePatientContext` spec (no `User`/ORM/`firebase_uid` leak)
- [x] PatientProfile field classification (biometrics → chassis, `premium_valid_until` → global)
- [ ] D90 retention go/stop threshold ← still unset (founder) — see Open Decisions

## Phase 19 — P1 Security Foundations ✅ (705 tests)

> Patient-safety + compliance gaps fixed before any second interactive route exists.

- [x] P1.1 Append-only Triage path registry (`core/safety_registry.py`); `TriageVitalMiddleware` → `core/middleware/`
- [x] P1.2 `on_account_delete` hooks + Firebase Auth deletion + `ErasureRecord` model/migration
- [x] P1.3 PHIPseudonymizer extended (last_name, DOB, Moroccan CIN regex) + `PHIStrippingMiddleware`
- [x] P1.4 `core/llm_gateway.py narrate()` — sole sanctioned LLM entry point

## Phase 20 — P2 PatientProfile Split ✅ (720 tests)

> Highest-risk migration in the program — `SeparateDatabaseAndState`.

- [x] `core.BasePatientProfile` (chassis identity: firebase_uid, language, consent, biometrics)
- [x] `diabetes.DiabetesProfile` (module extension) + `core.PatientModule` junction table
- [x] `SeparateDatabaseAndState` migration — `diabetes_patientprofile` table preserved
- [x] All callsites migrated; backward-compat alias removed in P3

## Phase 21 — P3 Module Registry + Chassis Router ✅ (731+ tests)

- [x] `core/registry.py` ModuleRegistry + RegisteredModule
- [x] `diabetes/manifest.py` DIABETES_MANIFEST (frozen dataclass)
- [x] Dynamic router mount via `AppConfig.ready()` (static index switch removed)
- [x] `POST /account/modules/{name}/activate` + `GET /account/modules` + `require_module()`
- [x] `core/migrations/0007` backfill; both triage paths registered

## Phase 22 — P4 / P4.5 LLM Narrative Generalization ✅ (764 tests)

- [x] P4.1 `companion/prompts.py` generalized via `CompanionIdentity` template
- [x] P4.2 (completed via P4.5) `BaseEngine.analyze(patient_id, language, days) → DomainContext`; companion + `narrate()` consume one enriched `DomainContext` via `core/companion/clinical.py`; `session_cache` build path retired
- [ ] P4.3 wire DetectorRegistry to production — **deferred → Phase 25 (P7.4)** (no single-module value; delete `clinical/registry.py` if P7 slips)
- Deviation: `ai/api/v1/ai.py` summary/doctor-brief keep `run_clinical_analysis` (analytical endpoints, not companion path)

## Phase 23 — P5 Observability + Sync Generalization 🟡

- [x] P5.1 `module` field on ObservabilityEvent; `track(module=...)` (default `"diabetes"`)
- [x] P5.2 `compute_retention_metrics(acquisition_event, funnel_events, module)` parameterized
- [x] P5.3 Chassis sync router dispatches by `module` (backward-compatible default)
- [ ] P5.4 move analytics endpoint → `core/api/v1/` — **NOT done**: still `diabetes/api/v1/analytics.py` (cosmetic; URL unchanged)

## Phase 24 — P6 Flutter Multi-Module Frontend 🟡 (A done · B deferred)

- [x] P6-A `frontend/lib/modules/` ModuleConfig + ModuleRegistry + diabetesModule; registry-driven routes/nav (integer-index switch removed)
- [x] P6-A `ModulesProvider` — nav reactive to `GET /account/modules` with offline fallback; `flutter analyze` clean
- [ ] P6-B URL namespacing `/api/v1/diabetes/*` + GoRouter prefixes — **deferred → Phase 25** (no single-module value, breaking change)
- [ ] P6-B Drift schema v6 PatientModules table, SyncService module routing, PatientProfileData split

## Phase 25 — P7 Hypertension Module ⛔ GATED

> First *second* module — proves the platform. **Do not start until D90 ≥ threshold AND one payer signal.**

- [ ] `hypertension/` Django app scaffold + HYPERTENSION_MANIFEST
- [ ] `HypertensionEngine(BaseEngine)` implements the `analyze()` contract
- [ ] Flutter hypertension screens wired via the module switcher
- [ ] P7.4 wire DetectorRegistry to production (the deferred P4.3) — diabetes + hypertension detectors register, `run_all()` per module
- [ ] P7.5 physically move `companion/` → `core/` + table relocations

## Phase 26 — P8 3rd-Party Module Infrastructure 🟡 (P8.1 done · rest GATED)

- [x] P8.1 import-linter CI enforcement (**pulled forward 2026-06-07**) — `backend/.importlinter` + CI step; companion⊥modules strict, core⊥modules via debt allow-list
- [ ] P8.2 module submission review checklist ← waits for confirmed pharma/dev partner
- [ ] P8.3 `PatientScopedManager` base class ← waits for partner
- [ ] P8.4 public chassis API surface doc ← waits for partner

### Platform seam debt — next single-module actionable (NOT gated)

> Remaining `core → diabetes` import-linter debt (2) + the disabled llm contract. Real value today.

- [ ] `core.api.v1.auth → diabetes.models` — lazy `DiabetesProfile` creation on the login path (careful)
- [ ] Route `diabetes…engine → llm.factory` through `core/llm_gateway`, then re-enable the modules⊥`llm/` import-linter contract
- [ ] `core.middleware.triage_vital → diabetes.middleware.triage_classification` — module-register the classifier (safety-critical, explicit-approval-only)

---

## Open Decisions

| Item | Status |
|------|--------|
| **90-day retention go threshold** | **Founder to set — gates condition #2 and all expansion** |
| **First payer channel** | Probe pharma adherence program (easiest budgeted buyer) |
| Django-native auth migration | Target approved; account/session design, Firebase identity migration and rollback remain open (P0-MENA-3) |
| Django admin removal | No timeline set |
| Multimodal provider selection | Open until P0-MENA-4 privacy/quality/cost benchmark is complete |
| PostgreSQL migration | Execute when deploying to staging (Phase 14) |
| Staging infra choice | À décider avec l'associé (Railway / Render / VPS) |
| Condition #2 (hypertension, etc.) | SHELVED until Retention Gate passes (DA-03) |
