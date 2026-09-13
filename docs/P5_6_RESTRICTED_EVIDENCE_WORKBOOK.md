# P5-6 — Restricted evidence workbook

> **Purpose:** prepare the two restricted manifests without inventing approval evidence.  
> **Frozen candidate:** `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`

This file is a workbook only. It is not an approval manifest and must never be used as one.

## 1. Safety manifest — #318

Generate the authoritative packet from the frozen candidate first:

```bash
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-review-packet.json
```

Expected retained invariants:

- 59 exact cases;
- 10 required parity tuples;
- locales: `fr`, `ar`, `en`, `ar-MA`;
- fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- source SHA for the final manifest: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`.

The final restricted JSON must use exactly these top-level fields:

```json
{
  "schema_version": "<CURRENT_SCHEMA_VERSION_FROM_CODE>",
  "corpus_fingerprint": "823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5",
  "source_commit_sha": "fb42e4d641b7b057607fe6a2de3d5104ccf15d0b",
  "review_batch_reference": "<REAL_OPAQUE_REFERENCE>",
  "clinical_approval_reference": "<REAL_OPAQUE_REFERENCE>",
  "safety_owner_approval_reference": "<REAL_OPAQUE_REFERENCE>",
  "reviewed_on": "<YYYY-MM-DD>",
  "review_due_on": "<YYYY-MM-DD>",
  "locale_reviews": [],
  "case_reviews": [],
  "parity_reviews": []
}
```

Each `locale_reviews` row must contain exactly:

```json
{
  "locale": "fr",
  "native_reviewer_reference": "<REAL_OPAQUE_REFERENCE>",
  "qualification_reference": "<REAL_OPAQUE_REFERENCE>",
  "decision": "approved"
}
```

Do not put names, emails, phone numbers, licence numbers or direct reviewer contact data in the manifest. The code expects opaque evidence references.

Each `case_reviews` row must contain exactly:

```json
{
  "case_id": "<EXACT_CASE_ID_FROM_EXPORTED_PACKET>",
  "native_decision": "approved",
  "clinical_decision": "approved",
  "issue_reference": ""
}
```

All 59 exact case IDs must be covered once. A rejected row must carry the real issue reference and blocks release.

Each `parity_reviews` row must contain the exact exported parity dimension plus:

```json
{
  "locale": "<EXACT_LOCALE>",
  "channel": "<EXACT_CHANNEL>",
  "input_form": "<EXACT_INPUT_FORM>",
  "reviewer_reference": "<REAL_OPAQUE_REFERENCE>",
  "decision": "approved"
}
```

All 10 parity tuples must be covered once.

Human inputs still missing and therefore **must remain missing rather than invented**:

- opaque reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- qualification references;
- real clinical/safety-owner approval references where the retained evidence does not already supply an acceptable opaque reference;
- real `reviewed_on` and `review_due_on` policy/date.

## 2. Residency / processor manifest — #320

The final restricted JSON must cover every known flow exactly once:

- `application_runtime`
- `primary_database`
- `redis_cache`
- `password_reset_email`
- `firebase_migration_bridge`
- `patient_export_staging`
- `ai_provider:gemini`
- `ai_provider:kimi`
- `ai_provider:claude`
- `ai_provider:deepseek`
- `ai_provider:qwen`
- `ai_provider:groq`

Top-level structure:

```json
{
  "schema_version": "<CURRENT_SCHEMA_VERSION_FROM_CODE>",
  "pilot_country": "MA",
  "controller_reference": "<REAL_RESTRICTED_REFERENCE>",
  "source_commit_sha": "fb42e4d641b7b057607fe6a2de3d5104ccf15d0b",
  "privacy_approval_reference": "<REAL_RESTRICTED_REFERENCE>",
  "security_approval_reference": "<REAL_RESTRICTED_REFERENCE>",
  "reviewed_on": "<YYYY-MM-DD>",
  "review_due_on": "<YYYY-MM-DD>",
  "flows": []
}
```

Enabled-flow row contract:

```json
{
  "flow_id": "<EXACT_FLOW_ID>",
  "enabled": true,
  "disabled_reason": "",
  "processor": "<ACTUAL_PROCESSOR>",
  "service": "<ACTUAL_SERVICE>",
  "data_categories": ["account_data"],
  "stores_data": false,
  "storage_countries": [],
  "storage_regions": [],
  "processing_countries": ["<ACTUAL_COUNTRY_CODE>"],
  "processing_regions": ["<ACTUAL_REGION>"],
  "cross_border_from_ma": true,
  "cndp_health_processing_reference": "<REAL_REFERENCE_IF_HEALTH_DATA>",
  "cndp_foreign_transfer_reference": "<REAL_REFERENCE_IF_FOREIGN_DESTINATION>",
  "contract_reference": "<REAL_ACCOUNT_SPECIFIC_REFERENCE>",
  "retention_reference": "<REAL_REFERENCE>",
  "owner_role": "<REAL_OWNER_ROLE>",
  "reviewed_on": "<YYYY-MM-DD>",
  "review_due_on": "<YYYY-MM-DD>"
}
```

Disabled-flow row contract:

```json
{
  "flow_id": "<EXACT_FLOW_ID>",
  "enabled": false,
  "disabled_reason": "<REAL_RUNTIME_REASON>",
  "processor": "",
  "service": "",
  "data_categories": [],
  "stores_data": false,
  "storage_countries": [],
  "storage_regions": [],
  "processing_countries": [],
  "processing_regions": [],
  "cross_border_from_ma": false,
  "cndp_health_processing_reference": "",
  "cndp_foreign_transfer_reference": "",
  "contract_reference": "",
  "retention_reference": "",
  "owner_role": "",
  "reviewed_on": null,
  "review_due_on": null
}
```

Known technical facts that may be used as evidence inputs, but **not** as regulatory approval:

- predecessor Vercel runtime: `cdg1`;
- predecessor Neon PostgreSQL 16: `aws-eu-central-1`;
- predecessor health: HTTP 200 / `db=ok`;
- Redis currently unproven/absent in the predecessor runtime;
- external AI providers remain disabled for the local-only release scope;
- Firebase migration env is absent in the verified predecessor runtime;
- current candidate introduces a required `password_reset_email` SMTP contract but no actual processor/account is yet selected or evidenced.

The `password_reset_email` flow therefore **cannot be marked approved/enabled with fabricated processor metadata**. It remains a real #320 blocker until an actual mail provider/account and its processing geography/contracts are evidenced.

## 3. Exact audits after real evidence exists

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b
```

A PASS is retainable only if the output contains the exact `audited_source_commit_sha` and all referenced evidence is genuine, current and reviewable.

## 4. Human/external gate checklist

### #318

- [ ] reviewer opaque references supplied
- [ ] qualification references supplied
- [ ] real review dates / review-due policy supplied
- [ ] 59 case decisions retained
- [ ] 10 parity decisions retained
- [ ] exact-SHA safety audit PASS retained

### #320

- [ ] actual mail processor selected and account evidence retained
- [ ] controller/privacy/security approval references retained
- [ ] CNDP health-processing reference retained where applicable
- [ ] foreign-transfer references retained for each foreign destination
- [ ] processor/DPA/subprocessor/retention/deletion/privacy/security evidence retained
- [ ] explicit authorization obtained before any new Vercel deployment
- [ ] exact candidate deployed and topology frozen
- [ ] exact-SHA residency + consent audits PASS retained

### Final release

- [ ] all three audit outputs PASS on `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`
- [ ] explicit human real-patient release authorization retained

Until every applicable item is proven, status remains `NOT_RELEASE_AUTHORIZED`.
