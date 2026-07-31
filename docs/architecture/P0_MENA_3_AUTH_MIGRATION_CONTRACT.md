# P0-MENA-3 — Sovereign authentication migration contract

## Objective

Replace Firebase as the authoritative patient authentication provider with a Django-owned account lifecycle without losing accounts, duplicating identities or breaking rollback.

The migration must be reversible until the final cutover gate passes.

## Current state

The repository currently has three distinct authentication surfaces:

1. Flutter uses Firebase Authentication for registration, sign-in, anonymous access, token refresh, password reset and sign-out.
2. Protected API routes accept either Firebase bearer tokens or Django sessions.
3. `POST /api/v1/auth/firebase` verifies a Firebase token, links it to a Django `User` and establishes a Django session.

The current bearer authenticator may create a Django user directly from a Firebase UID. This is legacy behavior and must not remain an uncontrolled identity-creation path during migration.

## Target state

Django becomes authoritative for:

- account creation;
- email verification;
- password authentication;
- password reset and recovery;
- session/token issuance;
- account disablement and deletion;
- staff and professional account controls;
- audit events and rate limiting.

Firebase becomes a temporary migration credential only, then is removed from runtime authentication.

## Canonical identity rules

- Django user ID is the permanent internal patient identity.
- Email is a login attribute, not an identity key.
- Firebase UID is a temporary external identity key recorded only for migration and reconciliation.
- A verified Firebase credential may link to an existing Django account only through an explicit deterministic rule.
- Email equality alone must never silently merge two independently established accounts.
- Client-supplied patient IDs, Django IDs or Firebase UIDs are never trusted for ownership.
- Clinical and demographic data are never synthesized during account migration.

## Migration phases

### Phase A — inventory and containment

- enumerate every Firebase runtime, backend and Flutter dependency;
- centralize Firebase token verification and identity linking;
- prevent direct user creation from secondary bearer-auth paths;
- add executable anti-bypass tests.

### Phase B — Django account lifecycle

- implement Django-owned registration and email verification;
- implement login, logout, token/session rotation and password reset;
- add rate limiting, generic error responses and audit events;
- define stronger controls for staff and professional accounts.

### Phase C — identity linking

- authenticated existing users explicitly claim/link their Firebase identity;
- brand-new Firebase users are migrated through one controlled bridge;
- ambiguous email/identity collisions are quarantined for reconciliation;
- every link operation is idempotent and audited.

### Phase D — dual-read migration

- Flutter prefers Django credentials;
- Firebase credentials are accepted only by the migration bridge;
- account state and ownership remain Django-authoritative;
- metrics track remaining Firebase-only users.

### Phase E — cutover and removal

- prove rollback before disabling Firebase login;
- remove Firebase registration, login, reset and anonymous authentication from Flutter;
- remove Firebase bearer authentication from protected API routes;
- retain migration records for the approved retention period;
- delete Firebase runtime dependencies only after the rollback window closes.

## Collision policy

The following cases must be handled explicitly:

| Case | Required action |
|---|---|
| Firebase UID already linked to one Django user | Return that user idempotently |
| Verified Firebase email matches one unlinked Django account | Require proof through the Django account before linking |
| Email matches multiple Django accounts | Quarantine; no automatic merge |
| Firebase UID conflicts with another linked account | Block and escalate |
| Existing Django user changes email | Preserve Django identity; do not relink by email |
| Anonymous Firebase user | No automatic promotion to a patient account without explicit account creation |

## Rollback contract

Before cutover, rollback must be able to:

- re-enable the migration bridge without changing Django user IDs;
- restore Flutter Firebase login for already-linked users;
- avoid creating a second Django account for the same Firebase UID;
- preserve sessions, clinical ownership and audit history;
- identify all accounts created or linked during the migration window.

Rollback must not require deleting patient data or reverting clinical migrations.

## Security requirements

- no raw authentication exception details in API responses;
- password reset and registration responses must not reveal whether an email exists;
- rate limits on login, registration, verification and recovery endpoints;
- credential rotation after login and privilege changes;
- server-side revocation and disablement;
- staff/professional accounts require stronger authentication controls than patient accounts;
- logs contain stable event categories, never passwords, reset tokens or bearer tokens.

## Acceptance gate

P0-MENA-3 is complete only when:

- all Firebase callsites are inventoried and controlled;
- Django account lifecycle and recovery are implemented and tested;
- identity linking, collision handling and rollback are executable;
- Flutter has migrated to Django authentication;
- Firebase bearer authentication is removed from protected routes;
- staff/professional controls are enforced;
- SQLite, PostgreSQL, migration drift, Ruff, import-linter, security checks, OpenAPI, Flutter analysis and secret hygiene pass on the final clean SHA.

## Completion checkpoint — 31 July 2026

- Django registration, login, logout, password establishment and native recovery are implemented.
- IAMINA bearer tokens are signed, expiring and globally revocable per patient.
- Flutter initializes native authentication before routing and stores IAMINA credentials securely.
- Native authentication is primary; Firebase remains only a temporary migration bridge and demo dependency.
- Firebase link and unlink are explicit; email is never a silent merge key for an active Django account.
- Historical Firebase shells are migrated only when uniquely identifiable and without synthesized patient facts.
- SQLite and PostgreSQL both apply migration `0011_basepatientprofile_auth_token_version`.
- Readiness audit: `python manage.py audit_auth_migration`.
- Final Firebase-removal gate: `python manage.py audit_auth_migration --require-zero-firebase`.
