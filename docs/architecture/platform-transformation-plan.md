# IAmina — Platform Transformation Plan
# From Modular Monolith → Health Companion Platform (Chassis + Modules)

> **⚠️ DETOUR CLOSED (2026-06-16) — ARCHIVE / REFERENCE ONLY.**
> This was a scoped re-architecture detour (ADR-0008). Completed work (P0–P6 + P8.1) has been
> **folded into `docs/ROADMAP.md` as Phases 18–26**, which is now the single forward tracker.
> P7 (live second module) and P8.2–8.4 (3rd-party infra) remain **GATED behind the Retention
> Gate** — see ROADMAP. Do not track active work here; update ROADMAP.md instead. This file
> stays as the detailed implementation/decision record for the chassis.

> **Status:** P0–P6 + P8.1 COMPLETE — folded into ROADMAP Phases 18–26. P7/P8 gated.
> **Date:** 2026-06-04 (updated 2026-06-06)
> **Based on:** 4 deep-analysis agents (Chassis, Module Contract, Frontend, Security)
> **Target:** Architecture.jpeg v2 (chassis + first-party + 3rd party + any frontend)
> **Current baseline:** 764 tests passing, P0–P5 complete (P4.2 finished via P4.5)
>
> **P4.2 correction (2026-06-06):** P4 was originally marked done having shipped only a
> `companion_identity` param; the P4.2 deliverable (`analyze(patient_id)→DomainContext`,
> wire the direct `run_clinical_analysis` callsites) was not actually wired and `.analyze()`
> had no production callers. This was completed in **P4.5** — see the P4.5 notes in Phase 4 below
> (full record in ROADMAP Phase 22). The companion now
> consumes the single engine contract; the parallel companion-ports idea was superseded.

---

## Reading This Plan

Each phase is independently executable. Dependencies between phases are explicit.
Risk ratings: 🔴 CRITICAL · 🟠 HIGH · 🟡 MEDIUM · 🟢 LOW

**Rule:** Never start a phase before its dependencies are complete and tests pass.

---

## Standing Protocol — Context Files Update (Claude's Compass)

> **Rule:** After every phase completes and tests pass, update the following files before closing the session or merging. These files are Claude's compass — read at session start to orient every agent. A stale compass = wrong decisions.

### Files to update after each phase

| File | What to update |
|---|---|
| `diabetes-poc/CLAUDE.md` | Session State block: mark phase DONE, list commits, update remaining steps, update test count |
| `process/context/all-context.md` | Features table: move phase from `active` → `completed`; update Scan Metadata date; add any new packages to Repository Structure |
| `docs/architecture/ARCHITECTURE.md` | Migration Path table: flip phase status ✅; resolve any Expert Review condition (🔴/🟡) that the phase addressed |
| `docs/architecture/platform-transformation-plan.md` | This file: update phase header status, add commit hash, update risk register if a risk was mitigated |

### Phase-specific MD checklist

**After P0 (Spec):**
- `CLAUDE.md` → add ADR-0008 to ADR table; update Open Decisions (D90 threshold, ambiguous fields)
- `all-context.md` → add `platform-transformation` to active features
- `ARCHITECTURE.md` → mark C5, C7, C8, C11, C12 conditions resolved (if addressed)

**After P1 (Security):**
- `CLAUDE.md` → remove "Active blocker" lines for Triage, RGPD, PHI
- `ARCHITECTURE.md` → mark C1, C2, C3, C4 conditions resolved
- `docs/MISTAKES.md` → add entry for the 3 unguarded `get_llm()` callsites (or confirm already logged)

**After P2 (PatientProfile Split):**
- `all-context.md` → update Repository Structure: `core/models/patient.py` and `core/models/patient_module.py`
- `CLAUDE.md` → add PatientProfile split to Known Technical Debt completed list
- `ARCHITECTURE.md` → mark C5 condition resolved

**After P3 (Registry + Router):**
- `all-context.md` → add `core/registry.py` and `core/safety_registry.py` to structure; update ModuleRegistry status from MISSING → DONE
- `CLAUDE.md` → add module registry to Architecture section; update URL prefix table
- `ARCHITECTURE.md` → mark C2, C6 conditions resolved

**After P4 (LLM Generalization):**
- `all-context.md` → update `companion/` brain description (CompanionIdentity); add `core/llm_gateway.py` to llm/ section
- `ARCHITECTURE.md` → mark C1 condition resolved (chassis.narrate() = sole entry point)

**After P5 (Observability + Sync):**
- `all-context.md` → update observability feature entry with `module` field added
- `CLAUDE.md` → observability / retention noted as platform-ready

**After P6 (Flutter Multi-Module):**
- `all-context.md` → update Frontend section: Drift schema v6, module-aware GoRouter, SyncService
- `CLAUDE.md` → update Platforms, flutter test count

**After P7 (Hypertension Module):**
- `all-context.md` → add `hypertension` feature (active); update Repository Structure with `backend/hypertension/`
- `ARCHITECTURE.md` → flip `Future Module` placeholder → `Hypertension Companion (first second module)`
- `CLAUDE.md` → update Strategy section: Morocco beachhead proven, Gulf prep active

**After P8 (3rd Party Infrastructure):**
- `all-context.md` → add `docs/chassis-api-for-modules.md` pointer
- `CLAUDE.md` → add `import-linter` to CI/CD section

### Non-negotiable rule

**Never leave a phase as "done in code" without the MD update.** If a phase is complete but the compass files say otherwise, the next agent session will re-investigate completed work, second-guess decisions already made, and risk duplicating or undoing changes. The 10 minutes it takes to update these files prevents hours of confusion per future session.

---

## Current State Summary (What We Have)

| Chassis Component | Status | Gap |
|---|---|---|
| Patient identity + auth | PARTIAL | PatientProfile in diabetes/ not core/; no per-patient module enrollment |
| Sync service (offline-first) | PARTIAL | Diabetes-only batch endpoint; no module routing |
| LLM narrative engine | PARTIAL | Pipeline exists; companion/prompts.py hardcoded to diabetes persona |
| Pattern detection + nudges | PARTIAL | DetectorRegistry exists but not wired to production |
| Observability + retention | PARTIAL | track() is generic; retention SQL hardcodes diabetes events |
| Module registry | DONE | core/registry.py ModuleRegistry + diabetes/manifest.py DIABETES_MANIFEST (P3) |

| Frontend | Status |
|---|---|
| Auth JWT (Firebase) | ✅ Chassis-compatible as-is |
| Theming | ✅ Not domain-specific |
| API routes | ❌ 17 hardcoded paths, no module prefix |
| GoRouter | ❌ Flat, diabetes-named |
| Drift schema | ❌ 3 diabetes-only tables |
| SyncService | ❌ Single-module batch only |
| Module abstraction | ❌ Does not exist |

---

## Phase 0 — Spec & Decisions (No Code — 1–2 days) **Status: ✅ DONE (2026-06-05) — 705 tests**

> **Why first:** Three naming collisions and one type conflict in the current spec will cause cascading rewrites if not resolved before any code is written.

### P0.1 — Write ADR v4.0 (supersedes DA-03)

**File:** `docs/adr/ADR-0008-platform-chassis.md`

Must document:
- What triggered the reversal of DA-03 (founder decision 2026-06-04)
- The platform chassis model as the accepted architecture
- Retention Gate: second module only after D90 ≥ [FOUNDER SETS THIS] and one payer signal
- Ownership: who owns the chassis vs who owns modules

**Blocker:** No code in P1–P8 can start without this ADR.

### P0.2 — Resolve naming collision: DomainContext

**Problem:** Two things named `DomainContext`:
- `clinical/domain_context.py` → 3-field companion identity struct (companion_name, domain_description, unit)
- Architecture target → clinical output struct (the thing `analyze()` returns)

**Decision:**
- Rename `clinical/domain_context.py` `DomainContext` → `CompanionIdentity`
- Define a new `core/contracts/domain_context.py` `DomainContext` = clinical output (kpi_summary, detected_patterns, insights, pivot_text, language)
- Update all references to `DomainContext` in `diabetes/domain_config.py`, `companion/`, `session_cache.py`

### P0.3 — Resolve type conflict: patient_id

**Problem:** Architecture doc says `analyze(patient_id: UUID, language)` but Django PKs are int.
**Decision:** Use `int` (Django User.id), not UUID. Update spec in `ARCHITECTURE.md`.

### P0.4 — Write ModuleManifest spec

**File:** `docs/architecture/module-contract-spec.md`

Must define (exact types):

```python
# core/contracts/manifest.py
@dataclass(frozen=True)
class ModuleManifest:
    name: str                       # "diabetes", "hypertension"
    version: str                    # "1.0.0"
    condition: str                  # ICD-10 or free text
    url_prefix: str                 # "/diabetes" (static, no path params)
    tags: list[str]                 # OpenAPI tag group
    supported_languages: list[str]  # ["fr", "ar-MA", "ar"]
    interactive_endpoints: list[str] # ["/diabetes/ai/chat"] — for Triage gate
    acquisition_event: str          # "log_created", "bp_reading_created"
```

### P0.5 — Write ModulePatientContext spec

```python
# core/contracts/patient_context.py
@dataclass(frozen=True)
class ModulePatientContext:
    patient_id: int
    language: str
    region: str
    consent_flags: dict[str, bool]  # {"ai_consent": True, "data_sharing": False}
    # NEVER: User object, PatientProfile ORM, firebase_uid
```

### P0.6 — Classify PatientProfile ambiguous fields

**Ambiguous fields requiring founder decision:**
- `premium_valid_until` → global (chassis) or per-module?
- `gender`, `date_of_birth`, `weight`, `height` → chassis identity or diabetes module?

**Recommendation:** Move all 4 biometrics to chassis (relevant to all future modules). Keep `premium_valid_until` global.

### P0.7 — Fix D90 retention threshold

Set a concrete go/stop number in `docs/ROADMAP.md` and `CLAUDE.md`. Without this, P7+ (second module) has no gate.

---

## Phase 1 — Security Foundations 🔴 (Before Any New Module) **Status: ✅ DONE (2026-06-05) — 705 tests**

> **Why second:** Two CRITICAL patient-safety bugs exist today. They must be fixed before a second module route is added, or a hypertensive crisis message goes to the LLM with no safety intercept.

### P1.1 — Triage Path Registry 🔴 CRITICAL (patient safety)

**Problem:** `_TRIAGE_PATHS = ("/api/v1/ai/chat",)` hardcoded in `diabetes/middleware/triage_vital.py:90`. New module routes bypass the emergency gate.

**Implementation:**

1. Create `backend/core/safety_registry.py` — append-only `TriageRegistry`:

```python
class AppendOnlyTriageRegistry:
    def __init__(self):
        self._paths: list[str] = []
        self._keyword_sets: list[frozenset[str]] = []
    def register_path(self, path: str) -> None:
        self._paths.append(path)
    def register_keywords(self, kws: frozenset[str]) -> None:
        self._keyword_sets.append(kws)
    # No __setitem__ — append-only to prevent malicious .clear()

TRIAGE_REGISTRY = AppendOnlyTriageRegistry()
```

2. Move `TriageVitalMiddleware` from `diabetes/middleware/` → `core/middleware/triage_vital.py`
3. Remove `_TRIAGE_PATHS` constant from the middleware — read from `TRIAGE_REGISTRY._paths` at init
4. In `diabetes/apps.py`, add `ready()`:

```python
def ready(self):
    from core.safety_registry import TRIAGE_REGISTRY
    TRIAGE_REGISTRY.register_path("/api/v1/diabetes/ai/chat")
    TRIAGE_REGISTRY.register_keywords(frozenset([...glucose keywords...]))
```

5. Update `settings.py` MIDDLEWARE: `diabetes.middleware.triage_vital` → `core.middleware.triage_vital`
6. Add CI system check: assert both clinical middlewares are in required order

**Tests to add:** 3 tests — (a) new module path bypasses without registration, (b) registered path gets intercepted, (c) registry is append-only

### P1.2 — RGPD on_account_delete Hook + Firebase Deletion 🟠 HIGH

**Problem:** `DELETE /account` only deletes diabetes data. Firebase Auth account survives. No hook for future modules.

**Implementation:**

1. Create `backend/core/account_hooks.py` with `AppendOnlyRegistry` + `register_account_delete_hook()` + `run_account_delete_hooks(patient_id, firebase_uid)`
2. Create `core/models/erasure_record.py` — `ErasureRecord` model (patient_id_snapshot, hook_failures JSON, completed_at)
3. Add migration for `ErasureRecord`
4. Update `core/api/v1/account.py` `delete_account()`:
   - Call `run_account_delete_hooks(patient_id, firebase_uid)` before `user.delete()`
   - Call `firebase_admin.auth.delete_user(firebase_uid)` (with try/except + log)
   - Create `ErasureRecord` after deletion
5. Register diabetes cleanup in `diabetes/apps.py ready()`:

```python
def ready(self):
    from core.account_hooks import register_account_delete_hook
    from diabetes.services.session_cache import invalidate
    register_account_delete_hook(lambda pid, uid: invalidate(pid))
```

### P1.3 — Expand PHIPseudonymizer 🟠 HIGH

**Problem:** Strips only `first_name`. Last name, DOB, national ID pass through to LLM.

**Implementation:**

1. Extend `llm/pseudonymizer.py` to accept `last_name`, `date_of_birth` (as string), and apply regex for national ID patterns (Moroccan CIN: 1–2 letters + 5–6 digits)
2. Add `PHIStrippingMiddleware(BaseLLMMiddleware)` — defense-in-depth backstop that raises `PHILeakError` if a name-pattern regex fires on system/user prompt before forwarding
3. Fix `stream()` and `think()` in `LLMPipeline` to run at minimum the `PHIStrippingMiddleware`
4. Fix 3 unguarded callsites:
   - `ai/api/v1/ai.py:270` — add pseudonymizer before `llm.complete()`
   - `pulper.py:211` — per PHI-NOTE: add structured PHI stripping on extracted text
   - `diabetes/services/clinical/engine.py:651` — inspect and fix if PHI present in prompts

### P1.4 — chassis.narrate() Entry Point 🟠 HIGH

**Problem:** Modules currently import `get_llm()` directly. No enforcement. PHI bypass risk.

**Implementation:**

1. Create `backend/core/llm_gateway.py`:

```python
def narrate(
    patient_context: ModulePatientContext,
    domain_context: DomainContext,    # clinical output from module
    companion_identity: CompanionIdentity,  # renamed from DomainContext
    language: str,
) -> str:
    """The ONLY sanctioned LLM call surface. Applies pseudonymization internally."""
    llm = LLMPipeline(get_llm(), [PHIStrippingMiddleware(), LoggingMiddleware()])
    system = _build_system_prompt(companion_identity, language)
    user = _build_user_prompt(domain_context, patient_context)
    pseudonymizer = PHIPseudonymizer()
    pseudonymizer.calibrate(patient_context.patient_id)
    system = pseudonymizer.mask(system)
    user = pseudonymizer.mask(user)
    response = llm.complete(system, user)
    return pseudonymizer.unmask(response.content)
```

2. Add CI bandit rule: flag any `from llm.factory import get_llm` import outside `core/llm_gateway.py` and `llm/` itself

---

## Phase 2 — PatientProfile Split 🟠 HIGH RISK

**Status: ✅ DONE (2026-06-05) — 720 tests**

> **Prerequisites:** P0 complete (field classification decided), P1 complete (auth hooks updated)
> **Risk:** Highest migration risk in the entire plan. Requires SeparateDatabaseAndState.

### P2.1 — Create core/models/patient.py (BasePatientProfile)

Fields that move to chassis:
- `patient` (OneToOneField to User) — becomes the chassis identity anchor
- `firebase_uid` — unique, indexed
- `preferred_language`
- `ai_consent_given_at`
- `premium_valid_until`
- `created_at`, `updated_at`
- `gender`, `date_of_birth`, `weight`, `height` (if P0.6 decision: chassis)

### P2.2 — Migration (SeparateDatabaseAndState required)

Steps:
1. `core/migrations/0003_basepatientprofile.py` — CREATE TABLE `core_basepatientprofile`
2. Data migration — COPY all identity-field rows from `diabetes_patientprofile` to `core_basepatientprofile`
3. `diabetes/migrations/XXXX_patientprofile_to_extension.py` — make `PatientProfile` a OneToOneField extension of `BasePatientProfile` using `SeparateDatabaseAndState`
4. Reverse migration must be written and tested before merging

**Tests required before merge:**
- Run full 692-test suite on a fresh SQLite (--reuse-db=false)
- Run dry-run migration on a test PostgreSQL dump

### P2.3 — Update all import paths

Files that import `PatientProfile.firebase_uid`, `.preferred_language`, `.ai_consent_given_at`:
- `core/api/v1/auth.py` — `_resolve_user`, `_ensure_profile`: create `BasePatientProfile` only; `DiabetesProfile` created lazily by diabetes module
- `core/api/v1/account.py` — consent endpoints: update FK path
- `ai/api/v1/ai.py` — language lookup
- `ai/api/v1/voice.py` — language hints
- `core/middleware/triage_vital.py` — `_patient_region()`, `_patient_lang()` (after P1.1 move)
- All 11 test files that construct `PatientProfile` with mixed fields

### P2.4 — Add PatientModule junction table

```python
# core/models/patient_module.py
class PatientModule(models.Model):
    patient = models.ForeignKey(BasePatientProfile, on_delete=CASCADE)
    module_name = models.CharField(max_length=64)  # "diabetes", "hypertension"
    activated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("patient", "module_name")]
```

---

## Phase 3 — Module Registry + Chassis Router 🟡 MEDIUM **Status: ✅ DONE (2026-06-05) — 731+ tests**

> **Prerequisites:** P0, P1, P2 complete

### P3.1 — ModuleManifest + ModuleRegistry

**File:** `backend/core/registry.py`

```python
class ModuleRegistry:
    _modules: dict[str, "RegisteredModule"] = {}

    @classmethod
    def register(cls, manifest: ModuleManifest, engine_class, router: Router):
        cls._modules[manifest.name] = RegisteredModule(manifest, engine_class, router)

    @classmethod
    def get(cls, name: str) -> "RegisteredModule":
        return cls._modules[name]

    @classmethod
    def all(cls) -> list["RegisteredModule"]:
        return list(cls._modules.values())
```

### P3.2 — Dynamic router registration via AppConfig.ready()

Replace static imports in `diabetes/api/main.py` with registry-driven mount:

```python
# diabetes/apps.py
class DiabetesConfig(AppConfig):
    def ready(self):
        from core.registry import ModuleRegistry
        from diabetes.api.v1 import diabetes_router
        from diabetes.services.clinical.engine import DiabetesEngine
        from diabetes.manifest import DIABETES_MANIFEST
        ModuleRegistry.register(DIABETES_MANIFEST, DiabetesEngine, diabetes_router)
```

```python
# diabetes/api/main.py — simplified
from core.registry import ModuleRegistry

for module in ModuleRegistry.all():
    api.add_router(
        module.manifest.url_prefix,
        module.router,
        auth=_auth,
        tags=module.manifest.tags,
    )
```

### P3.3 — Per-patient module routing

Add API endpoint: `POST /api/v1/account/modules/{module_name}/activate`
The chassis router checks `PatientModule.objects.filter(patient=..., module_name=..., is_active=True)` before forwarding to the module. Module endpoints return 404 if the patient hasn't activated the module.

### P3.4 — Update URL namespacing

**Current:** `/api/v1/logs`, `/api/v1/ai/chat`
**Target:** `/api/v1/diabetes/logs`, `/api/v1/diabetes/ai/chat`

This is a breaking change for the Flutter client — must be coordinated with Phase 6 (frontend).

---

## Phase 4 — LLM Narrative Engine Generalization 🟡 MEDIUM **Status: ✅ P4.1 (in P4) + P4.2 (in P4.5); ⏸ P4.3 DEFERRED → P7 (764 tests)**

> **P4.3 (wire DetectorRegistry to production) is DEFERRED to P7** (decision 2026-06-06).
> `clinical/registry.py` exists but `run_clinical_analysis()` uses a plain detector list.
> With a single module the registry buys nothing (same detectors, same output) — wiring it
> now is premature abstraction (violates KISS / DA-03). It will be wired as part of P7 when
> hypertension provides a real second detector set that validates the registry's shape. See
> P7.4. (Alternative if P7 slips indefinitely: delete `clinical/registry.py` as dead code.)
>
> **P4.2 was completed in P4.5** (see the P4.5 notes in Phase 4 below; full record in ROADMAP Phase 22):
> `BaseEngine.analyze(patient_id, language, days) → DomainContext` (engine fetches own
> data); companion runtime + `narrate()` consume the same enriched `DomainContext` via
> `core/companion/clinical.py`; `session_cache` build path retired (invalidation shim only).
> **Deviation:** `ai/api/v1/ai.py` summary/doctor-brief keep `run_clinical_analysis` — they
> are analytical endpoints (std_dev/gmi_confidence/AGP/daily_averages) not on the companion
> path; documented in the P4.5 plan.

> **Prerequisites:** P0 (CompanionIdentity rename, DomainContext redefined), P1.4 (chassis.narrate())

### P4.1 — Generalize companion/prompts.py

Replace hardcoded "Tu es IAmina, compagnon bienveillant pour patient diabétique" with:

```python
def build_system_prompt(identity: CompanionIdentity, language: str) -> str:
    return SYSTEM_TEMPLATE.format(
        companion_name=identity.companion_name,
        domain_description=identity.domain_description,
        language=language,
    )
```

Update `DIABETES_COMPANION_IDENTITY` in `diabetes/domain_config.py` to be the concrete `CompanionIdentity` for diabetes.

### P4.2 — Generalize analyze() signature

Update `BaseEngine.analyze()`:

```python
@abstractmethod
def analyze(self, patient_id: int, language: str = "fr") -> DomainContext:
    """Module fetches its own data internally given patient_id."""
```

Update `DiabetesEngine.analyze()`:
```python
def analyze(self, patient_id: int, language: str = "fr") -> DomainContext:
    entries = LogEntry.objects.filter(patient_id=patient_id).order_by("-logged_at")[:90]
    kpis = compute_kpis(entries)
    report = run_clinical_analysis(entries, kpis, language)
    return DomainContext.from_clinical_report(report, language)
```

Wire all 3 callsites (`session_cache.py:79`, `ai.py:174`, `ai.py:266`) to use `DiabetesEngine.analyze()` instead of calling `run_clinical_analysis()` directly.

### P4.3 — Wire DetectorRegistry to production ⏸ DEFERRED → P7

`run_clinical_analysis()` currently uses a plain list. Registering the 10 diabetes detectors
to `DetectorRegistry` (`clinical/registry.py`) and calling `DetectorRegistry.run_all()` has
**no single-module value** — it's the same detectors with added indirection. Deferred to P7
(see P7.4), when a second condition's detector set proves the registry's shape; do it then
or delete the registry. Not done now to avoid premature abstraction.

---

## Phase 5 — Observability + Sync Generalization 🟢 LOW RISK

> **Prerequisites:** P3 (module names established)

### P5.1 — Module-namespaced event types

Add `module` field to `ObservabilityEvent`:
```python
module = models.CharField(max_length=64, default="diabetes")
```
Migration: additive column with default, zero downtime. Backfill existing records with `"diabetes"`.

Update `track()` to accept optional `module` param (default `"diabetes"`).

### P5.2 — Parameterize retention SQL

```python
def compute_retention_metrics(
    acquisition_event: str = "log_created",
    funnel_events: list[str] | None = None,
    module: str | None = None,
) -> RetentionMetrics:
```

Default behavior unchanged. Each module can call with its own `acquisition_event`.

### P5.3 — Chassis-level sync router

Add `module` field to the batch sync payload schema:

```python
class BatchSyncSchema(Schema):
    module: str = "diabetes"
    entries: list[LogEntryCreateSchema]
```

The chassis router dispatches based on `module` to the registered module's batch ingest handler. Backward-compatible: if `module` is missing, defaults to `"diabetes"`.

### P5.4 — Move analytics endpoint to core/api/v1/

Move `diabetes/api/v1/analytics.py` → `core/api/v1/analytics.py`. Update mount in main.py. This is a URL change (`/api/v1/analytics/overview` stays the same — no breaking change).

---

## Phase 6 — Flutter Multi-Module Frontend 🟠 HIGH

> **Prerequisites:** P3.4 (URL namespacing decided)
> **Note:** Must be coordinated with backend URL change in P3.4. Deploy backend first with both old + new URLs (deprecation period), then migrate Flutter, then remove old URLs.

### P6.1 — API route module prefix (17 paths)

Introduce a `ModuleApiClient` abstraction:

```dart
class ModuleApiClient {
  final String modulePrefix; // "diabetes"
  final ApiClient _client;

  ModuleApiClient(this.modulePrefix, this._client);

  String path(String endpoint) => '/api/v1/$modulePrefix$endpoint';
}
```

Replace all 17 hardcoded paths to use `moduleClient.path(...)`. The 5 raw `http` calls (SSE, multipart) also need updating.

### P6.2 — GoRouter module namespacing

Add module prefix to all non-chassis routes:
- `/dashboard` → `/diabetes/dashboard`
- `/journal` → `/diabetes/journal`
- `/ajouter` → `/diabetes/ajouter`

Chassis routes unchanged: `/login`, `/consent`, `/onboarding`.

Add `initialLocation` logic that picks the module dashboard based on `PatientModule` active list (fetched at startup).

### P6.3 — Drift schema additions

Add schema version 6:
- New table: `PatientModules` — tracks which modules are active per patient (mirrors backend `PatientModule`)
- Keep all existing tables unchanged — additive only

### P6.4 — SyncService module-aware routing

```dart
class SyncService {
  Future<void> syncAll() async {
    await _syncModule('diabetes', db.getPendingLogs());
    // future: await _syncModule('hypertension', db.getPendingBPReadings());
  }
}
```

### P6.5 — MainShell module switcher

Replace hardcoded 5-tab `switch(index)` with a dynamic navigation bar built from active modules:
- Each active module contributes its nav destinations
- Module switcher at top level (if >1 module active)
- Falls back to current single-module UX if only diabetes active

### P6.6 — PatientProfileData scope fix

Split `PatientProfileData` global stream into:
- `BasePatientData` (chassis: language, consent) — stays global
- `DiabetesProfileData` (module: targets, unit preference) — scoped to diabetes screens

---

## Phase 7 — Hypertension Module (First Second Module) 🟡 MEDIUM

> **Prerequisites:** ALL of P0–P6 complete + D90 Retention Gate passed
> **This phase proves the platform works. Do not start early.**

### P7.1 — hypertension/ Django app scaffold

```
backend/hypertension/
  __init__.py
  apps.py            # HypertensionConfig with ready() → ModuleRegistry.register(...)
  manifest.py        # HYPERTENSION_MANIFEST
  models/
    entry.py         # BPReading (systolic, diastolic, pulse, client_uuid, patient FK)
    profile.py       # HypertensionProfile (systolic_target, diastolic_target)
  api/v1/
    logs.py          # POST/GET /hypertension/readings
    kpis.py          # systolic/diastolic percentiles, pulse trend
    ai.py            # POST /hypertension/ai/chat (registered with Triage gate)
  services/clinical/
    engine.py        # HypertensionEngine(BaseEngine)
    sql_analytics.py # BP SQL KPIs
    detectors/       # detect_white_coat, detect_nocturnal_dip, etc.
  migrations/
  tests/
```

### P7.2 — HypertensionEngine implements contract

```python
class HypertensionEngine(BaseEngine):
    def analyze(self, patient_id: int, language: str = "fr") -> DomainContext:
        readings = BPReading.objects.filter(patient_id=patient_id).order_by("-logged_at")[:90]
        kpis = compute_bp_kpis(readings)
        patterns = DetectorRegistry.run_all(readings)
        return DomainContext(kpi_summary=kpis, detected_patterns=patterns, language=language)
```

### P7.3 — Flutter Hypertension screens

New feature folder: `frontend/lib/features/hypertension/`
- `HypertensionDashboardScreen`
- `BPJournalScreen`
- `AddBPScreen`

Wired into module switcher via `PatientModules` active list.

### P7.4 — Wire DetectorRegistry to production (the deferred P4.3) 🟢 LOW

> **Why here:** P4.3 was deferred to P7 — the registry only earns its keep once a *second*
> module needs to register detectors it doesn't own. Building hypertension is that moment.

1. Register the 10 diabetes detectors with `DetectorRegistry` in `diabetes/apps.py ready()`
   and the hypertension detectors in `hypertension/apps.py ready()`.
2. Switch `run_clinical_analysis()` (diabetes) and `HypertensionEngine.analyze()` from
   plain detector lists to `DetectorRegistry.run_all(...)`, scoped per module.
3. Verify diabetes output is unchanged (same detectors, same order) — pure refactor.

> Note: P7.2's example signature is illustrative — the real contract is the P4.5 one:
> `analyze(patient_id, language, days) → DomainContext` with the enriched fields
> (`has_sufficient_data`, `tone_signals`, `trend`, `primary_label`, `patterns_detail`).
> If P7 is not started, the fallback is to delete `clinical/registry.py` as dead code.

---

## Phase 8 — 3rd Party Module Infrastructure 🟢 LOW PRIORITY

> **Prerequisites:** P7 complete (platform proven with 2 first-party modules)
> **Do not build this until at least one pharma or dev partner is confirmed.**

### P8.1 — import-linter CI enforcement ✅ DONE (pulled forward 2026-06-07)

> **Pulled forward** ahead of the rest of P8: it locks in the P4.5/P6 seams now and
> has full single-module value (unlike the rest of P8/P7). Config: `backend/.importlinter`;
> wired into `.github/workflows/ci.yml` (step "Architecture boundaries").

Enforced contracts (ratchet model — strict on new code, existing debt allow-listed):
- ✅ `companion/` cannot import any condition module — KEPT clean (the P4.5 seam).
- ✅ `core/` cannot import any condition module — KEPT via a debt allow-list (2 left, was 3):
  - ✅ FIXED: `core.api.v1.account -> diabetes.models.AuditLog` → now via `core/audit.py` port (`0dcbd44`).
  - `core.api.v1.auth -> diabetes.models` (DEBT: lazy DiabetesProfile creation)
  - `core.middleware.triage_vital -> diabetes.middleware.triage_classification`
    (DEBT: module-register the classifier; safety-critical, explicit-approval-only)
- ⏸ "modules must not import `llm/` directly" — NOT yet enforced: noisy (legitimate
  indirect use via the companion runtime) and needs the `diabetes…engine -> llm.factory`
  call routed through the gateway first. Re-add once that's done.
- (`diabetes` ⊥ `hypertension` lands automatically when hypertension exists — P7.)

### P8.2 — Module submission review checklist

File: `docs/third-party-module-review-checklist.md`
- No direct `get_llm()` import
- Uses `PatientScopedManager` for all patient data queries
- Implements `on_account_delete(patient_id)` hook
- Registers all interactive endpoints in `ModuleManifest.interactive_endpoints`
- No FK to another module's models
- No direct `from diabetes.models import ...`

### P8.3 — PatientScopedManager base class

```python
# core/querysets.py
class PatientScopedManager(models.Manager):
    def for_patient(self, patient_id: int) -> models.QuerySet:
        return self.get_queryset().filter(patient_id=patient_id)
```

All module models that store patient data must use this manager.

### P8.4 — Public chassis API surface document

File: `docs/chassis-api-for-modules.md`
Documents everything a 3rd party module can use:
- `core.registry.ModuleRegistry.register()`
- `core.account_hooks.register_account_delete_hook()`
- `core.safety_registry.TRIAGE_REGISTRY.register_path()`
- `core.llm_gateway.narrate()`
- `core.observability.track()`
- `core.contracts.ModuleManifest`
- `core.contracts.ModulePatientContext`
- `core.contracts.DomainContext`

Everything else in `llm/`, `companion/`, `safety/` is internal — not public API.

---

## Execution Sequence Summary

```
P0 (Spec) → P1 (Security) → P2 (PatientProfile) → P3 (Registry+Router)
                                                         ↓
                                             P4 (LLM) + P5 (Obs+Sync) [parallel]
                                                         ↓
                                                     P6 (Flutter)
                                                         ↓
                                              [D90 Gate + Payer Signal]
                                                         ↓
                                                  P7 (Hypertension)
                                                         ↓
                                              [Partner confirmed]
                                                         ↓
                                                   P8 (3rd Party)
```

---

## Risk Register

| Risk | Phase | Severity | Mitigation |
|---|---|---|---|
| PatientProfile migration drops table | P2 | 🔴 | SeparateDatabaseAndState + dry-run on fresh DB before merge |
| URL namespacing breaks Flutter app | P3.4 / P6.1 | 🟠 | Deprecation period: serve both old + new URLs, migrate Flutter, remove old |
| TriageVitalMiddleware blind to new routes | P1.1 | 🔴 | Fix before any new interactive endpoint exists |
| PHI bypass via get_llm() in 3rd party | P1.4 / P8.1 | 🔴 | CI bandit rule + import-linter before accepting any 3rd party module |
| DiabetesEngine.analyze() not called in production (bypassed) | P4.2 | 🟡 | Wire all 3 callsites in one PR, run full test suite |
| Flutter PatientProfileData global stream breaks | P6.6 | 🟠 | Split stream before any module screen changes; fix 4 affected screens together |
| DomainContext naming collision | P0.2 | 🟠 | Fix in Phase 0 before any code is written |
| DetectorRegistry not wired (exists but unused) | P4.3 | 🟡 | Wire in P4; no production behaviour change |

---

## What We Keep As-Is (No Change Needed)

- `LogEntry` FK chain (`LogEntry.patient → auth.User`) — unchanged
- `client_uuid` on `LogEntry` — carries forward to all module entry models
- `LLMPipeline` + `LoggingMiddleware` — chassis-ready as built in S2
- `BaseEngine` ABC — refactored signature in P4.2, not replaced
- `track()` fire-and-forget pattern — add `module` param, otherwise unchanged
- `RetentionMetrics` compute — parameterize in P5.2, not replaced
- Firebase JWT → Django User bridge in `core/api/v1/auth.py` — unchanged
- `FallbackProvider` / `QuotaExhaustedProvider` — unchanged
- All 10 diabetes detectors — not touched until P4.3 (just wired to registry)
- `AuditLog` (RGPD) + `ObservabilityEvent` (telemetry) — both kept, ErasureRecord added
- Flutter auth (`AuthService`, `AuthInterceptor`) — already chassis-compatible
- Flutter theming — unchanged

---

## Next Immediate Actions (This Sprint)

1. ✅ **P0.1** — Write ADR-0008 (founder sets the trigger + D90 threshold)
2. ✅ **P0.2** — Rename `DomainContext` → `CompanionIdentity` in `clinical/domain_context.py` (trivial refactor, no behaviour change)
3. ✅ **P0.4 + P0.5** — Write `docs/architecture/module-contract-spec.md`
4. ✅ **P1.1** — Triage path registry (patient safety — start immediately)
5. ✅ **P1.2** — RGPD `on_account_delete` hook + Firebase deletion (compliance gap today, not just platform gap)
6. ✅ **P1.3** — PHIPseudonymizer extended (last_name, DOB, CIN regex) + PHIStrippingMiddleware
7. ✅ **P1.4** — core/llm_gateway.py narrate() — sole sanctioned LLM entry point

8. ✅ **P2** — core.BasePatientProfile + diabetes.DiabetesProfile + core.PatientModule split (720+ tests)
9. ✅ **P3** — ModuleRegistry, DIABETES_MANIFEST, dynamic router, activation endpoint, backfill migration (731+ tests)

**Next up: P4 — LLM Narrative Engine Generalization** (prerequisites: P0+P1+P2+P3 complete ✅).
