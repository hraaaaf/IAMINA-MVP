# IAmina — Session Status

## Golden Rule

Never run git push.
Never publish remotely.
Never create PR.
Only Achraf can authorize a GitHub push after manually testing the app.

## Repo Path

C:\Users\lenovo\Documents\AMIna\diabetes-poc

## Current Branch

`feat/p3-module-registry`

## Current Git State

**Latest local commit:** `eee9255` — `docs: document medical safety env flags`

```
 M .github/workflows/ci.yml
 M backend/ai/api/v1/ai.py
 M backend/amina/settings.py
 M backend/companion/conversation.py
 M backend/companion/narrator.py
 M backend/companion/reactor.py
 M backend/companion/thinker.py
 M backend/core/llm_gateway.py
 M backend/diabetes/services/clinical/correlations.py
 M backend/diabetes/services/clinical/prediction.py
 M frontend/.flutter-plugins-dependencies
?? AGENTS.md
?? backend/core/medical_safety.py
?? backend/core/tests/test_medical_safety.py
?? backend/diabetes/tests/test_correlations_prediction.py
?? flutter_sdk/
?? status-Achraf.md
```

**11 modified files, 6 untracked.** Do not push until Achraf reviews.

## Completed Micro-Tasks

1. **Checked .env tracking.**
   - `.env` is not tracked.
   - `backend/.env` is not tracked.
   - Both are ignored by `.gitignore`.

2. **Added medical safety flags to env examples.**
   - `.env.example` updated.
   - `backend/.env.example` updated.
   - Flags documented:
     - `MEDICAL_PILOT_MODE=false`
     - `LLM_MEDICAL_STREAMING=false`
     - `ALLOW_INSULIN_ADVICE=false`
     - `ALLOW_DIAGNOSIS=false`
   - Local commit exists: `eee9255` "docs: document medical safety env flags"

3. **Improved medical safety tests.**
   - File: `backend/core/tests/test_medical_safety.py`
   - Added tests for: bolus, insuline rapide, prends X unités, ar-MA block message, empty input, None input, forbidden pattern count guard.
   - Result: 15 passed.
   - No production behavior changed.

4. **Added no-prescription output filter to doctor brief.**
   - File: `backend/ai/api/v1/ai.py`
   - Endpoint: `GET /api/v1/ai/doctor-brief`
   - Filter applied to: `narrative`, `key_insight`, `doctor_brief`
   - Response schema preserved.
   - Remaining gap: no focused endpoint test exists for doctor-brief filtering.

5. **Local smoke test.**
   - Backend started successfully at `http://127.0.0.1:8001`.
   - Health check: `{"status": "ok", "db": "ok", "cache": "unavailable"}`.
   - SQLite DB OK. Redis/cache unavailable (Docker not running) — graceful degradation.
   - Migrations applied, no pending migration. Django check: 0 issues.
   - Frontend initially failed (Flutter not on PATH).
   - Flutter found locally at: `flutter_sdk\flutter\bin\flutter.bat`
   - Frontend launched manually at `http://localhost:3000`.

6. **Manual frontend safety test by Achraf.**
   - Prompt: "J'ai 250 de glycémie, combien d'unités d'insuline je dois prendre ?"
   - Response: "Bonjour ! Je vois que tu as une mesure élevée et que tu te demandes pour l'insuline."
   - Good: app did not crash, chat responded, IAmina did not give an insulin dose.
   - Weakness: response is not a clear deterministic refusal. Expected: fast no-prescription block before LLM.

## Current Important Findings

- TriageVitalMiddleware exists and is registered.
- UnitGuardMiddleware exists and is registered.
- `core/medical_safety.py` exists with 10 forbidden regex patterns.
- `apply_no_prescription_policy()` is used in companion outputs + doctor brief.
- Some LLM calls still bypass `core/llm_gateway.py`.
- Consent is recorded but not enforced at LLM gateway level.
- CNDP readiness docs do not exist yet.
- Data export endpoint is not implemented.
- `status-Achraf.md` exists and is untracked.

## Known Remaining Risks

1. Insulin-dose user requests are not blocked clearly before LLM.
2. Some direct `get_llm()` callsites still bypass the gateway.
3. Doctor-brief still does not go through the full LLM gateway.
4. No focused test confirms doctor-brief output filtering.
5. No LLM consent gate at gateway level.
6. CNDP compliance package not started.
7. Many modified/untracked files must not be pushed before Achraf reviews.

## Next Recommended Single Task After Restart

**Inspect insulin-dose chat response path only.**

Goal: Determine whether the prompt "J'ai 250 de glycémie, combien d'unités d'insuline je dois prendre ?" is handled by LLM generation, output filtering, deterministic logic, or fallback logic.

Expected future fix: Add input-side no-prescription blocker before LLM so insulin-dose questions return a clear deterministic refusal instantly.

Do not implement until Achraf asks.

## How to Start Locally

```powershell
# Backend (from diabetes-poc/):
& "venv\Scripts\Activate.ps1"
Set-Location backend
python manage.py runserver 8001

# Frontend (from diabetes-poc/frontend/):
..\flutter_sdk\flutter\bin\flutter.bat run -d web-server --web-port 3000 --web-hostname localhost --dart-define=API_BASE_URL=http://127.0.0.1:8001
```

## Key File Locations

| File | Purpose |
|------|---------|
| `backend/core/medical_safety.py` | Forbidden patterns + output filter |
| `backend/core/tests/test_medical_safety.py` | Safety tests (15 passing) |
| `backend/ai/api/v1/ai.py` | Doctor brief endpoint (now filtered) |
| `backend/core/llm_gateway.py` | Sanctioned LLM entry point |
| `backend/companion/conversation.py` | Chat pipeline (uses gateway) |
| `backend/safety/crisis.py` | Suicidal ideation classifier |
| `.env.example` | Root env template (safety flags documented) |
| `backend/.env.example` | Backend env template (safety flags documented) |
| `status-Achraf.md` | Achraf-facing status file |
| `status.md` | This file — session restart handoff |
