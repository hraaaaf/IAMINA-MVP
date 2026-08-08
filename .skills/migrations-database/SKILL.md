# Skill — Database & Migration Review

## Purpose
Protect PostgreSQL source-of-truth behavior, schema correctness and migration safety.

## Required checks
- Inspect models, migrations and database-specific behavior before editing.
- Prefer the smallest migration consistent with actual schema/state; do not create ALTER operations to reconcile state-only drift when unnecessary.
- Run `makemigrations --check --dry-run` and the repository migration-drift gate.
- Validate forward migration on PostgreSQL when schema is touched.
- Run the relevant PostgreSQL regression suite before certification.
- Preserve `client_uuid` offline-sync idempotency and SQL-first KPI authority where applicable.
- Document rollback/recovery strategy proportional to migration risk.

## Blockers
Unreviewed destructive migration, SQLite-only evidence for PostgreSQL-critical behavior, unresolved migration drift, silent data-loss risk, or generated migration noise unrelated to the LOT.