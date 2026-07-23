"""
Observability primitives — scaffold for Phase 5 of AMINA_MVP_PLAN.md.

Nothing in this package is wired into the Django app yet. The goal of
this scaffold is to give subsequent commits a stable import path to
land real implementations against (and to give the AI ops agent the
shape of the artefacts it should read / write).

Modules:
- `logging` — JSON structured logger + request_id correlation key.
- `metrics` — Prometheus counters / histograms (SLIs).

When wired, both are consumed by `amina/middleware/request_id.py`
and surfaced on `/metrics` (Phase 5).
"""
