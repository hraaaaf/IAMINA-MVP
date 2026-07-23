"""
Project-wide middleware — scaffold for Phase 5 of AMINA_MVP_PLAN.md.

Modules:
- `request_id` — correlates logs / metrics per HTTP request.
- (to come) `audit_log` — writes to the AuditLog model on sensitive
  actions.
- (to come) `firebase_auth` — verifies Firebase ID tokens on
  `/api/v1/*`.

Nothing here is installed in `MIDDLEWARE` yet. Activation happens in
later Phase 5 and Phase 3 commits.
"""
