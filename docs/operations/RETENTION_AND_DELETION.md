# Pilot Retention and Deletion Schedule

## Status

This document defines IAmina's pilot operating schedule. It does not replace
country-specific legal review, processor commitments or a documented legal hold.

## Schedule

| Dataset | Trigger | Period | Action |
|---|---|---:|---|
| Raw AI media in the application | Not persisted | 0 days | Discard after bounded request processing |
| Patient export staging files | Rolling | 7 days | Remove restricted staging copy |
| Password-reset tokens | Cryptographic expiry | 1 day | Expire and revoke through token versioning |
| Patient application records | Verified account-deletion request | 30-day grace | Delete owned records through relational cascade |
| Security audit logs | Rolling | 2,190 days | Delete when expired or retain under documented hold |
| Encrypted backups | Infrastructure lifecycle | 35 days | Expire immutable backup; replay deletion tombstones after restore |

Policy owner: IAmina Privacy & Security  
Effective: 2026-08-02  
Review due: 2026-11-02

## Permanent audit

```bash
python manage.py audit_retention_policy
```

This command fails when a rule is missing, inconsistent, not yet effective or stale.

## Patient-deletion procedure

1. Verify the requester using the approved identity process.
2. Offer and, when requested, generate a patient export.
3. Record the verified request date and approval reference.
4. Check for legal, safety, dispute or security holds.
5. Wait the 30-day grace period, during which cancellation remains possible.
6. Run a dry plan:

```bash
python manage.py delete_patient_data \
  --user-id <ID> \
  --requested-at YYYY-MM-DD \
  --approval-reference <REFERENCE> \
  --export-sha256 <SHA256> \
  --legal-hold-status CLEARED
```

7. Review the current record manifest.
8. Execute only with the exact account-specific confirmation:

```bash
python manage.py delete_patient_data \
  --user-id <ID> \
  --requested-at YYYY-MM-DD \
  --approval-reference <REFERENCE> \
  --export-sha256 <SHA256> \
  --legal-hold-status CLEARED \
  --execute \
  --confirm DELETE-PATIENT-<ID>
```

Execution detaches historical audit actors, preserves an anonymous deletion event
and deletes the Django account plus relationally owned application records in one
transaction. Failure rolls back the database operation.

## Export staging purge

Dry run:

```bash
python manage.py purge_export_staging --directory /secure/export-staging
```

Execute:

```bash
python manage.py purge_export_staging \
  --directory /secure/export-staging \
  --execute
```

Only regular, non-symlink files named `iamina-patient-*.json` and older than seven
days are eligible.

## External infrastructure obligations

Application code cannot itself prove object-store, database snapshot or provider
backup deletion. Before pilot approval, infrastructure owners must demonstrate:

- encrypted backup lifecycle of at most 35 days;
- deletion-tombstone replay after restore;
- processor-specific retention settings;
- documented legal-hold activation and release;
- periodic evidence that the staging purge and retention audit actually run.
