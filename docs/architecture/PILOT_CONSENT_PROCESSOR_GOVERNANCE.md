# Pilot consent and processor governance

**Status:** candidate-bound engineering gate prepared; legal/privacy/processor approval remains external.

**Policy version:** `2026-09-11.1`

**Pilot country:** Morocco

Canonical release gate: `docs/P5_6_REAL_PATIENT_RELEASE_GATE.md`.

## 1. Invariant

No single fact authorizes patient-data egress.

Independent gates include, where applicable:

1. approved patient notice;
2. base AI consent;
3. purpose/modality-specific raw audio, image or document consent;
4. health-data processing authorization;
5. foreign-transfer authorization or approved basis;
6. exact processor/account/product/model/region approval;
7. DPA, service terms and subprocessor evidence;
8. retention, deletion and training-use evidence;
9. security and privacy owner approval;
10. exact candidate SHA binding.

Patient consent does not replace CNDP authorization, contractual evidence, security review or processor approval.

## 2. Runtime fail-closed policy

`backend/core/ai_processor_policy.py` remains authoritative for patient-data egress.

At the current policy baseline:

- `gemini`, `kimi`, `claude`, `deepseek`, `qwen` and `groq` are network providers with status `PENDING`;
- `fallback` and `quota-exhausted` are local-only and `APPROVED`;
- configuration alone cannot convert a pending network provider into an approved patient-data processor.

The restricted approval manifest does **not** bypass runtime policy. It must contain approval rows for every external provider whose runtime policy is already `APPROVED`, and it must contain no extra provider rows.

## 3. Executable consent matrix

`backend/core/pilot_consent_governance.py` derives its matrix from every registered purpose/modality.

Permanent invariants:

- a new runtime purpose or modality creates matrix drift until covered;
- audio, image and document paths require granular raw-media consent;
- external processor paths require base AI consent, health-data authorization, transfer clearance and processor approval;
- a runtime-approved external provider with unresolved governance blockers is rejected;
- local fallback paths cannot authorize network egress.

## 4. Restricted candidate approval manifest

The real release approval manifest remains outside Git.

Configure its path:

```bash
export PILOT_CONSENT_GOVERNANCE_MANIFEST_PATH=/restricted/iamina/pilot-consent-governance.json
```

A non-operational schema example is stored at:

`docs/examples/pilot-consent-governance-manifest.example.json`

The real manifest records only opaque evidence references and must include:

- schema version and pilot country;
- exact `source_commit_sha`;
- controller reference;
- patient notice reference;
- base AI consent reference;
- raw-media consent reference;
- health-data authorization reference;
- privacy and security approval references;
- review and expiry dates;
- exact account-specific approval rows for every runtime-approved external provider.

It must not contain credentials, patient records, signed contracts, private regulator correspondence or reviewer contact details.

## 5. Exact-candidate binding

The release operator must supply the frozen candidate SHA explicitly:

```bash
export PILOT_RELEASE_SOURCE_SHA=<exact-40-char-git-sha>
```

A manifest whose `source_commit_sha` differs from this value is rejected. A syntactically valid old SHA is not enough.

Any code/configuration change after candidate freeze invalidates the approval package.

## 6. Commands

Structural audit:

```bash
cd backend
python manage.py audit_pilot_consent_governance
```

Candidate-bound real-patient gate:

```bash
cd backend
python manage.py audit_pilot_consent_governance \
  --manifest /restricted/iamina/pilot-consent-governance.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The approved gate fails when the manifest is missing, malformed, stale, SHA-mismatched, has missing/extra runtime-approved external processors, or contains invalid evidence references.

## 7. Evidence handling

Git may contain public policy references, status, accountable roles, schema examples and opaque references.

Git must not contain signed contracts, patient consent records, CNDP private correspondence, credentials, private processor audit reports or personal contact details.

Restricted evidence belongs in the approved private compliance repository.

## 8. Approval checklist

The real-patient gate remains open until:

- [ ] frozen candidate SHA recorded;
- [ ] final patient notice approved;
- [ ] consent wording approved;
- [ ] health-data processing authorization evidence recorded;
- [ ] transfer evidence recorded for every actual destination;
- [ ] every runtime-approved external processor/account/product/region approved;
- [ ] subprocessors, DPA, retention, deletion and training-use evidence approved;
- [ ] security and privacy approval current;
- [ ] restricted consent manifest references the frozen SHA;
- [ ] `audit_pilot_consent_governance --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" --require-approved` passes;
- [ ] evidence is current on launch day.

This contract is engineering governance, not legal advice or release authorization.
