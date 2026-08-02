# Patient Data Export — Operational Process

## Purpose

Provide one authenticated patient's IAmina data in a machine-readable JSON file
without exposing credentials, password hashes or another patient's records.

## Command

Run from `backend/` in an authorized administrative environment:

```bash
python manage.py export_patient_data \
  --user-id <DJANGO_USER_ID> \
  --output /secure/export-directory/iamina-patient-<ID>.json
```

The command:

- resolves exactly one Django user;
- walks reverse ownership relations through the `core`, `diabetes` and `ai` apps;
- does not follow forward relations into shared catalogues;
- excludes password, token and credential fields;
- writes atomically with file mode `0600`;
- refuses to overwrite unless `--overwrite` is explicitly supplied;
- emits a deterministic SHA-256 content fingerprint;
- creates an append-only `AuditLog` export event.

## Delivery procedure

1. Verify the requester using the approved identity-verification procedure.
2. Generate the export in a restricted temporary directory.
3. Compare the recorded SHA-256 value with the generated file.
4. Deliver through the approved encrypted channel.
5. Record delivery without copying patient content into tickets or chat.
6. Delete the temporary file according to the export staging retention rule.

## Export structure

- `schema_version`
- `generated_at`
- `subject.user_id`
- `manifest.models`
- `manifest.record_count`
- `data.account`
- `data.records`
- `sha256`

## Fail-closed rules

- No stdout export is supported, preventing accidental CI/log disclosure.
- A missing account, missing output directory or existing destination fails.
- Shared/global objects are not traversed.
- Secrets and authentication material are excluded even when related to the user.
- The export is not a backup restore format and does not authorize account deletion.
