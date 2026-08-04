# Morocco pilot data residency and foreign transfers

**Status:** executable engineering gate prepared; production deployment manifest and approvals remain external.

**Policy version:** `2026-08-04.1`

## 1. No inference from source code

The repository does not establish production geography.

- `DATABASE_URL` identifies a connection target at runtime, but its presence does not prove the processor, country, region, contract or CNDP authorization.
- `REDIS_URL` behaves the same way.
- the Django e-mail backend and its processing locations are deployment facts;
- Firebase is a temporary migration bridge whose exact project/account configuration must be recorded;
- AI providers are configurable and remain separately evidence-gated;
- frontend/CDN and application-host locations are deployment facts, not repository defaults.

A real-patient pilot therefore requires a restricted deployment manifest tied to the exact deployed Git SHA.

## 2. Morocco regulatory baseline

Official CNDP guidance reviewed on 2026-08-04 states that:

- health-data processing requires prior authorization;
- purposes must be precise and disclosed, and data must be necessary and proportionate;
- processors must be controlled through contracts and audits;
- foreign transfers require one of the allowed bases or express CNDP authorization;
- a transfer authorization is granted only after the underlying treatment has itself been declared or authorized.

Official references:

- `https://www.cndp.ma/conditions/`
- `https://www.cndp.ma/notifier-une-demande-dautorisation-prealable/`
- `https://www.cndp.ma/transfert-de-donnees-a-letranger/`
- `https://www.cndp.ma/procedures-de-notification-process/`

These sources define the engineering evidence requirements. They do not prove that IAMINA has received any authorization.

## 3. Required deployment flows

The manifest must contain exactly one record for each known flow:

1. `application_runtime`
2. `primary_database`
3. `redis_cache`
4. `password_reset_email`
5. `firebase_migration_bridge`
6. `patient_export_staging`
7. one `ai_provider:<provider>` record for every external provider registered in `ai_processor_policy.py`

A new runtime AI provider automatically creates manifest drift until its residency flow is reviewed.

The application runtime, primary database and password-reset e-mail flow must be enabled for the pilot. Optional flows may be disabled only with an explicit rationale.

## 4. Location evidence

Each enabled flow records:

- processor and exact service;
- personal-data categories;
- whether data is stored at rest;
- exact storage countries and provider region identifiers;
- exact processing countries and provider region identifiers;
- whether the flow is cross-border from Morocco;
- CNDP health-processing reference when health data is involved;
- CNDP foreign-transfer reference when any country is outside Morocco;
- contract and retention references;
- accountable owner;
- review and expiry dates.

The validator derives foreign destinations from the recorded country codes and rejects an inconsistent cross-border flag.

## 5. Provider-specific notes

Public provider pages are only review inputs:

- Google Cloud data residency: `https://cloud.google.com/terms/data-residency`
- Google Cloud subprocessors: `https://cloud.google.com/terms/subprocessors`
- OpenAI subprocessors, for a future candidate only: `https://openai.com/policies/sub-processor-list/`

Public terms cannot establish the actual IAMINA account, selected region, model behavior, optional features, support access, retention configuration or signed contract. Those facts belong in restricted evidence.

## 6. Restricted manifest

The real manifest must remain outside Git and be mounted read-only at runtime or during the release gate.

Configure only its path:

```bash
export PILOT_RESIDENCY_MANIFEST_PATH=/restricted/iamina/pilot-residency.json
```

Do not place in the manifest:

- connection URLs;
- API keys or tokens;
- passwords;
- private keys;
- patient identifiers;
- signed contracts or private regulator correspondence.

Use opaque references into the approved private compliance repository.

A non-operational schema example is stored at:

`docs/examples/pilot-residency-manifest.example.json`

It deliberately contains placeholders and is not approval evidence.

## 7. Commands

Preparation audit, expected to report a missing manifest in ordinary development:

```bash
cd backend
python manage.py audit_pilot_data_residency
```

Real-patient release gate:

```bash
cd backend
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved
```

The second command fails when:

- the manifest is missing or stale;
- any known flow is absent or duplicated;
- a required flow is disabled;
- a country or region is missing;
- a foreign destination lacks transfer evidence;
- a health-data flow lacks treatment authorization evidence;
- an unapproved external AI provider is enabled;
- an approved external AI provider is omitted or disabled;
- secret-like material appears in the manifest.

## 8. Approval checklist

The roadmap gate can close only when:

- [ ] the exact production architecture is deployed;
- [ ] the manifest references the exact deployed Git SHA;
- [ ] database, cache, runtime, e-mail and export locations are verified;
- [ ] Firebase is disabled or its exact migration flow is approved;
- [ ] every external AI flow is disabled or fully approved;
- [ ] all health-data processing references are recorded;
- [ ] all foreign-transfer references are recorded;
- [ ] privacy and security owners approve the manifest;
- [ ] evidence is current on launch day;
- [ ] `audit_pilot_data_residency --require-approved` passes.
