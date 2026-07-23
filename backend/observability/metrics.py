"""
Application metrics — placeholder for Phase 5.

When wired this module will export Prometheus counters / histograms via
`prometheus_client`. Expected SLIs per TEAM.md (Cloud Ops):

- `request_latency_seconds{view,method,status}` — Histogram
- `llm_request_duration_seconds{provider,model}` — Histogram
- `llm_fallback_total{reason}` — Counter (timeout, bad_key, 5xx)
- `audit_log_writes_total{action}` — Counter

Metrics are registered in a DEFAULT registry; Django exposes them on
`/metrics` behind the Cloud Ops IP allowlist (Phase 5).

Nothing is emitted yet — this file exists so that Phase 5 commits can
`from observability.metrics import request_latency_seconds`
without additional plumbing churn.
"""
