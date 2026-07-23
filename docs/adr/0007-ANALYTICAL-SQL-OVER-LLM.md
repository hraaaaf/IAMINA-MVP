# ADR 0007 — Analytical SQL over LLM for Clinical Metrics

**Date:** 2026-04-24  
**Status:** Accepted  
**Deciders:** Staff SWE (Antigravity), Medical Advisor, Data/AI Engineer  

---

## Context

Phase 2 implemented KPI calculation (TIR, GMI, CV) directly in the Python view layer
(`ai.py`) using in-memory loops over the ORM queryset, and then fed raw numerical
arrays directly to the LLM.

Two fundamental problems were identified:

1. **LLM arithmetic is unreliable.** Language models are probabilistic; asking them to
   compute averages or percentages over time-series data introduces non-deterministic
   errors that are clinically unacceptable. A patient receiving an incorrect HbA1c
   estimate is a medical liability.

2. **Token cost.** Sending a list of 200 glucose readings to Gemini consumes
   ~500-800 tokens per call. At scale (1 000 DAU × 3 calls/day), this becomes
   economically unsustainable and introduces latency.

## Decision

All clinical metric computation (TIR, GMI, CV, TAR, TBR, average) is moved into
**PostgreSQL SQL functions** executed via `django.db.connection.cursor()`.

The LLM receives only a compressed English text summary of the pre-computed results.
It never sees raw data arrays. Its sole role is **interpretation and narrative generation**.

## Architecture: Three-Layer Pipeline

```
Patient Data (PostgreSQL)
         │
         ▼
┌─────────────────────────┐
│  sql_analytics.py       │  ← Layer 1: Pure SQL math (TIR, GMI, CV, TAR, TBR)
│  compute_kpis()         │    Returns: AnalyticalKPIs dataclass (immutable)
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  clinical/engine.py     │  ← Layer 2: Python pattern detection
│  run_clinical_analysis()│    (Dawn Phenomenon, Somogyi, Stress, Sleep…)
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  semantic_compressor.py │  ← Layer 3: KPIs + Patterns → English pivot text
│  compress()             │    Token reduction: ~90% vs. raw array approach
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM (Gemini 2.5 Flash) │  ← Interprets pre-computed data, generates response
│  English pivot input    │    Output: Patient language (FR | ar-MA)
└─────────────────────────┘
```

## Clinical Shield (Parallel Layer)

```
POST /api/v1/ai/chat
         │
         ▼
┌─────────────────────────┐
│  UnitGuardMiddleware    │  ← Glucose unit normalisation (mg/dL ↔ g/L ↔ mmol/L)
│  unit_guard.py          │    Rejects physiologically implausible values (HTTP 422)
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  TriageVitalMiddleware  │  ← Emergency keyword detection (FR + Darija)
│  triage_vital.py        │    Bypasses LLM → returns fixed emergency response
└─────────────────────────┘
         │
         ▼
       (LLM pipeline if no emergency detected)
```

## Consequences

### Positive
- **Accuracy:** SQL aggregates are deterministic and exact. Zero risk of LLM arithmetic error.
- **Cost:** ~90% token reduction per call (summary vs. raw arrays).
- **Safety:** Unit Guard prevents mg/dL/g/L confusion at the API boundary.
- **Latency:** KPI computation moves from LLM inference time (~2s) to SQL query time (<50ms).
- **Auditability:** Every KPI can be reproduced by re-running the SQL on historical data.

### Negative / Trade-offs
- **SQLite incompatibility:** `STDDEV_SAMP` is a PostgreSQL function. Developers running
  SQLite locally will get a fallback empty KPI object. This is acceptable; the dev
  environment should use PostgreSQL (see `docker-compose.yml` once created in Phase 4 infra).
- **Complexity:** Adds two new service files. Compensated by the unit-test coverage on
  `sql_analytics.py` (covered in Phase 6 test suite).

## Alternatives Rejected

| Alternative | Reason rejected |
|---|---|
| LLM computes KPIs from raw data | Arithmetic unreliable, high cost, high latency |
| Python calculates all KPIs | Bypasses DB optimiser, expensive for large datasets |
| TimescaleDB continuous aggregates | Excluded from MVP scope (Phase 10+) |

## Files Created

| File | Role |
|---|---|
| `backend/diabetes/services/clinical/sql_analytics.py` | SQL KPI engine |
| `backend/diabetes/services/clinical/semantic_compressor.py` | English Pivot Layer |
| `backend/diabetes/middleware/unit_guard.py` | Unit Guard (Clinical Shield) |
| `backend/diabetes/middleware/triage_vital.py` | Triage Vital (Clinical Shield) |
| `backend/ai/api/v1/ai.py` | AI endpoints (summary, chat, stream, image) |

> Paths updated 2026-06-03: `tracking/` → `diabetes/`, `amina/middleware/` → `diabetes/middleware/`, `tracking/api/` → `ai/api/` (post chassis rename).
