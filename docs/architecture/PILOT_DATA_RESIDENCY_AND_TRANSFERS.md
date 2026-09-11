# Morocco pilot data residency and foreign transfers

**Status:** candidate-bound engineering gate prepared; deployment manifest and approvals remain external.

**Policy version:** `2026-09-11.1`

Canonical release gate: `docs/P5_6_REAL_PATIENT_RELEASE_GATE.md`.

## 1. No inference from source code

The repository does not establish production geography.

Database, cache, e-mail, migration bridge, export staging, application hosting and provider locations are deployment facts. A real-patient pilot therefore requires a restricted deployment manifest tied to one exact frozen candidate SHA and the actual topology.

## 2. Required deployment flows

The manifest must contain exactly one record for each known flow:

1. `application_runtime`
2. `primary_database`
3. `redis_cache`
4. `password_reset_email`
5. `firebase_migration_bridge`
6. `patient_export_staging`
7. one `ai_provider:<provider>` record for every external provider registered in `ai_processor_policy.py`

A new runtime provider automatically creates manifest drift. Required flows must be enabled. Optional flows may be disabled only with an explicit rationale.

## 3. Location evidence

Each enabled flow records processor/service, personal-data categories, storage and processing countries/regions, cross-border status, applicable CNDP evidence, contract/retention references, accountable owner and review dates.

The validator derives foreign destinations from recorded country codes and rejects inconsistent cross-border flags.

## 4. Restricted manifest

The real manifest remains outside Git and is mounted read-only during the release gate.

```bash
export PILOT_RESIDENCY_MANIFEST_PATH=/restricted/iamina/pilot-residency.json
```

A non-operational schema example is stored at:

`docs/examples/pilot-residency-manifest.example.json`

The manifest uses opaque references only and must not contain operational secrets, private documents or direct personal data.

## 5. Exact-candidate binding

The release operator supplies the immutable candidate SHA:

```bash
export PILOT_RELEASE_SOURCE_SHA=<exact-40-char-git-sha>
```

The approved residency audit compares that explicit SHA with manifest `source_commit_sha`. A manifest from another candidate is rejected even when otherwise valid.

Any code/configuration change after freeze invalidates the candidate approval package.

## 6. Commands

Preparation audit:

```bash
cd backend
python manage.py audit_pilot_data_residency
```

Candidate-bound real-patient gate:

```bash
cd backend
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The approved command fails when the expected SHA is missing/malformed, manifest SHA differs, evidence is missing/stale/incomplete, topology coverage drifts, required CNDP evidence is absent, or provider enablement conflicts with runtime approval.

## 7. Approval checklist

The gate can close only when:

- [ ] candidate SHA frozen after exact-main CI;
- [ ] actual architecture/topology captured;
- [ ] manifest references that exact SHA;
- [ ] database, cache, runtime, e-mail and export locations verified;
- [ ] Firebase disabled or its exact migration flow approved;
- [ ] every external AI flow disabled or fully approved;
- [ ] health-data processing and foreign-transfer references recorded where applicable;
- [ ] privacy and security owners approve the manifest;
- [ ] evidence current on launch day;
- [ ] candidate-bound residency audit passes.

This contract does not prove CNDP authorization or production geography by itself.
