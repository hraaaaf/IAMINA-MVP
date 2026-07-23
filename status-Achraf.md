# IAmina — Current Status for Achraf

### Last updated

2026-06-17 13:30

### Current branch

`feat/p3-module-registry`

### Golden rule

**Never push to GitHub until Achraf has manually tested and explicitly approved.**

---

### Current repo state

**Latest local commit:** `eee9255` — `docs: document medical safety env flags`

**Modified files (10):**
- `.github/workflows/ci.yml`
- `backend/ai/api/v1/ai.py`
- `backend/amina/settings.py`
- `backend/companion/conversation.py`
- `backend/companion/narrator.py`
- `backend/companion/reactor.py`
- `backend/companion/thinker.py`
- `backend/core/llm_gateway.py`
- `backend/diabetes/services/clinical/correlations.py`
- `backend/diabetes/services/clinical/prediction.py`

**Untracked files (5):**
- `AGENTS.md`
- `backend/core/medical_safety.py`
- `backend/core/tests/test_medical_safety.py`
- `backend/diabetes/tests/test_correlations_prediction.py`
- `flutter_sdk/`

**There are uncommitted changes.** Do not push until reviewed.

---

### Completed micro-tasks

1. **Checked whether .env is tracked.**
   - Result: `.env` and `backend/.env` are NOT tracked.
   - They are correctly ignored by `.gitignore` (line 28).
   - No credential leak risk in version control.

2. **Added medical safety flags to env examples.**
   - Added to both `.env.example` and `backend/.env.example`.
   - Flags documented with safe defaults (`false`):
     - `MEDICAL_PILOT_MODE=false`
     - `LLM_MEDICAL_STREAMING=false`
     - `ALLOW_INSULIN_ADVICE=false`
     - `ALLOW_DIAGNOSIS=false`
   - Committed locally as `eee9255`.

3. **Added missing medical safety tests.**
   - File: `backend/core/tests/test_medical_safety.py`
   - Added tests for: bolus, insuline rapide, prends X unités, ar-MA block message, empty input, None input, and forbidden pattern count guard.
   - Result: 15 passed in 1.12s.
   - No production behavior was changed.

4. **Added no-prescription output filtering to doctor brief.**
   - File: `backend/ai/api/v1/ai.py`
   - Endpoint: `GET /api/v1/ai/doctor-brief`
   - Filter applied to: `narrative`, `key_insight`, `doctor_brief`
   - Response schema preserved.
   - Test run: `backend/core/tests/test_medical_safety.py`
   - Result: 15 passed in 1.76s.
   - Remaining gap: no focused endpoint test exists for doctor-brief filtering.

---

### Important safety findings

- **TriageVitalMiddleware** exists and is registered in `settings.py` MIDDLEWARE.
- **UnitGuardMiddleware** exists and is registered in `settings.py` MIDDLEWARE.
- **Crisis classifier** (`safety/crisis.py`) handles suicidal ideation deterministically.
- **medical_safety.py** exists with 10 forbidden regex patterns.
- **apply_no_prescription_policy()** is actively used in 3 companion output paths + doctor brief endpoint.
- **Doctor brief output** is now protected by `apply_no_prescription_policy()`.
- This reduces the risk of prescription-like wording being returned in doctor-facing summaries.
- **medical safety flags** exist in settings but `insulin_advice_allowed()`, `diagnosis_allowed()`, and `medical_pilot_mode_enabled()` are **not consumed by any production code** — they are dead code.
- **medical_safety.py** now has stronger test coverage.
- **NoPrescriptionPolicy** behavior is now better protected against accidental regression.
- **No git push must happen before Achraf validates the app.**

---

### Current blockers / risks

- Some LLM calls still bypass `core/llm_gateway.py` (4 allowlisted callsites in `ai.py`, `summary.py`, `engine.py`, `pulper.py`).
- Consent is recorded but not enforced at the LLM gateway level.
- CNDP readiness docs do not exist yet.
- Data export endpoint is not implemented.
- There are many modified/untracked files that must be reviewed before any push.
- Doctor brief still does not go through the full LLM gateway; only output filtering was added.

---

### Next recommended single task

Launch IAmina locally for smoke test before adding more hardening changes.

---

### Do not do yet

- Do not push to GitHub.
- Do not launch pilot.
- Do not refactor LLM gateway.
- Do not add new product features.
- Do not change frontend.
- Do not change medical behavior until tests are stronger.
