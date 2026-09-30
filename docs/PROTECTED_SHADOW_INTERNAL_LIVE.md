# IAMINA — Protected Shadow Internal Live (Bounded)

Status: **IMPLEMENTED — OFF BY DEFAULT — STAFF ONLY**

## Goal

Allow a bounded real provider shadow call from real active-staff runtime while keeping
all patient-linked clinical content local to IAMINA.

The provider receives one static non-clinical wrapper instruction. Its dynamic user payload contains only:

- locale;
- script;
- one random opaque protected-body token.

The deterministic clinical body, patient message, patient identity, facts, history,
AdviceDecision details, rule ids and clinical values remain local.

## Activation

Two independent switches are required:

```text
NARRATION_PROTECTED_PROVIDER_SHADOW=true
NARRATION_PROTECTED_PROVIDER_INTERNAL_LIVE=true
```

The runtime caller must also be an active Django staff account **and** its Django user
ID must be explicitly listed in:

```text
NARRATION_PROTECTED_PROVIDER_INTERNAL_LIVE_STAFF_IDS=<comma-separated IDs>
```

Either switch OFF, an empty/malformed allowlist, an unlisted subject, or a
non-staff/inactive subject prevents internal-live provider transport.

## Patient-data governance boundary

Groq's patient-data processor policy remains `PENDING`.

Internal live does not mark that policy approved and does not alter the normal
`authorize_processor_policy()` gate. The internal-live branch is limited to the
non-patient token-only transport surface described above.

If Groq is explicitly marked `FORBIDDEN`, internal live also fails closed before
provider construction.

## Runtime behavior

For `CLINICIAN_PREP` only:

1. IAMINA resolves the real deterministic clinical reply locally.
2. IAMINA verifies the deterministic reply locally.
3. IAMINA creates a random one-shot protected body token.
4. Only `locale + script + protected_body_token` may be sent to Groq.
5. Groq returns a short non-clinical wrapper containing the token exactly once.
6. IAMINA verifies token integrity.
7. IAMINA reinjects the deterministic body locally.
8. The module protected verifier checks the final candidate.
9. Shadow telemetry stores only allowlisted status fields.
10. The patient-visible reply remains the original deterministic reply during this lot.

Any provider, structural, semantic or policy failure falls back to the deterministic
patient-visible reply.

## Transport correction

The Groq GPT-OSS adapter historically forced JSON schema on `complete()`. Protected
wrapper narration requires plain text. This lot adds `complete_text()`, which preserves
the existing bounded reasoning/output limits but does not force the JSON response schema.

Existing JSON callers remain unchanged.

## Exact-head live proof

The workflow `.github/workflows/protected-shadow-internal-live.yml` performs a maximum
of three real Groq calls using the repository `GROQ_API_KEY` secret. Its synthetic
probe subject is explicitly allowlisted as ID `0`; production/staff IDs are never
hard-coded in source control.

The probe is synthetic on the network side and sends no patient data. It checks:

- exact token-only request shape;
- deterministic body/value absent before egress;
- token exactly once;
- non-empty wrapper;
- locale/script match;
- structural reinjection;
- CLINICIAN_PREP protected semantic verifier;
- scrubbed artifact output only.

This network probe composes with the separately certified real-data local boundary audit:
the former proves real provider transport; the latter proves a real patient can reach the
same protected-envelope boundary locally without patient-linked content entering the
provider payload.

## Non-goals

This lot does not:

- approve CNDP/Groq patient-data governance;
- send real patient content to Groq;
- change patient-visible clinical output;
- enable any family other than `CLINICIAN_PREP`;
- enable the feature by default;
- deploy Vercel;
- authorize general LLM patient-data egress.

## Rollback

Set either protected narration switch to `false`. No schema/data migration is required.
The deterministic clinical path remains authoritative and available.
