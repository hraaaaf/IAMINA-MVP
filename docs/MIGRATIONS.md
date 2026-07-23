# IAmina — Migration Runbooks

This document contains **active migration runbooks only**. Obsolete provider-brand migration plans belong in git history.

## 1. SQLite / local fallback → PostgreSQL

### Status

PostgreSQL is the intended authoritative database outside lightweight local fallback. Docker development already provides the preferred PostgreSQL path; any remaining SQLite workflow is convenience-only.

### Principles

- Never assume behavior parity for raw SQL, JSON, locking, constraints, or concurrency.
- Test migrations against PostgreSQL before staging/production.
- Back up before destructive schema/data changes.
- Prefer reversible Django migrations and explicit recovery procedures.

### Basic validation

```bash
python backend/manage.py migrate
python backend/manage.py check --database default
python backend/manage.py shell -c "from django.db import connection; print(connection.vendor)"
```

Expected outside SQLite fallback:

```text
postgresql
```

Review SQL-first analytics for PostgreSQL compatibility whenever queries change.

---

## 2. Legacy Firebase authentication → Django-native authentication

### Status

**PLANNED / P0-MENA-3.** Firebase remains legacy current-state until an account-preserving migration is designed and tested.

### Required design before code removal

1. Define Django-native account lifecycle:
   - signup/invite model;
   - verification;
   - session/token strategy;
   - password reset and recovery;
   - abuse/rate-limit controls;
   - account export/deletion;
   - staff/professional strong-auth requirements.
2. Inventory every Firebase dependency in backend, Flutter, config, CI, docs, and deployment.
3. Define stable identity mapping from Firebase UID to Django account.
4. Define duplicate-account and missing-account reconciliation.
5. Define rollback while both identity systems coexist.

### Migration sequence

1. Introduce Django-native auth behind compatibility boundaries.
2. Add identity-mapping/reconciliation tests.
3. Support a controlled dual-read/transition period if required by the chosen design.
4. Migrate accounts with auditable reconciliation counts.
5. Switch Flutter session/token flow only after backend migration is proven.
6. Verify login, recovery, deletion, consent, and offline-sync continuity.
7. Remove Firebase runtime dependencies only after rollback window closes.
8. Revoke/remove obsolete Firebase credentials and update deployment secrets.

### Acceptance gate

- no duplicate/lost accounts;
- deterministic reconciliation report;
- tested rollback/recovery;
- no hidden Firebase dependency remains in production-critical auth flow;
- security controls appropriate to patient/staff roles are active.

---

## 3. Legacy provider-specific AI calls → privacy-gated outbound boundary

### Status

**PLANNED / P0-MENA-1 + P0-MENA-4.** The old “Gemini → Kimi” migration is cancelled as a governing plan. IAmina no longer chooses a single target provider by brand preference.

### Migration principle

Text, STT, vision, and document extraction are separate modalities and may use different providers or local/on-device models.

### Sequence

1. Inventory every external model/media callsite.
2. Classify each by modality, purpose, payload, sensitivity, consent, retention, and failure behavior.
3. Introduce one enforceable outbound policy boundary.
4. Route callsites through that boundary without changing clinical authority.
5. Add CI rules preventing new direct provider bypasses.
6. Add timeout/failure/fallback contracts.
7. Benchmark candidate providers with minimized/synthetic evaluation data.
8. Approve provider(s) per modality only after privacy + MENA quality gates.
9. Cut over gradually with observability and rollback.
10. Remove obsolete provider SDK/config only after the new path is proven.

### Acceptance gate

No production provider cutover is complete until:

- direct bypass is impossible or CI-detected;
- outbound payload policy is explicit and tested;
- consent/minimization rules are enforced;
- processor/subprocessor and retention/training terms are documented;
- MENA language/dialect evaluation passes for the enabled cohort;
- rollback/fallback behavior is tested.

---

## 4. Documentation migration rule

When a migration completes:

- update `docs/architecture/ARCHITECTURE.md` to reflect the new **current** state;
- update `docs/SPECS.md` if capability/API behavior changed;
- remove completed forward tasks from `docs/ROADMAP.md` into its concise completed-foundations summary;
- delete obsolete migration instructions from this file rather than preserving them as active-looking sections.

Git history is the archive.
