# IAMINA — Protected Shadow Internal Live Certification

Status: **CERTIFIED PRE-MERGE**

Date: 2026-09-30
PR: #840
Branch: `conversation/protected-shadow-internal-live-bounded`
Certified code HEAD: `0f4033248b2f945424239840070f2d759630782a`

## Goal

Prove that IAMINA can execute a bounded real Groq protected-shadow wrapper call for
`CLINICIAN_PREP` while preserving deterministic clinical authority and keeping
patient-linked clinical content local.

## Success criteria

- feature remains OFF by default;
- internal-live requires active staff + explicit staff-id allowlist;
- family restricted to `CLINICIAN_PREP`;
- patient-visible output remains deterministic;
- provider dynamic payload is limited to `locale + script + protected_body_token`;
- no patient identity, patient message, deterministic clinical body, exact clinical value,
  history, AdviceDecision or rule id enters the provider payload;
- real Groq live probe completes for FR, Darija Arabic and Darija Latin;
- structural reinjection and protected semantic verifier pass;
- rollback remains one-switch reversible;
- no Vercel deployment;
- Groq patient-data governance status remains separate and PENDING.

## Exact-head evidence

### Protected Shadow internal live probe

Workflow run: **#37**
Run ID: `36729998756`
Conclusion: **SUCCESS**

Pre-network validation:
- Ruff: PASS
- targeted pytest: **29 passed**

Live machine gate:
- `machine_passed=true`
- `planned_calls=3`
- `patient_data=false`

Case results:
- `fr-default` / locale `fr` / script `default`: PASS, violations=[]
- `darija-arabic` / locale `ar-MA` / script `arabic`: PASS, violations=[]
- `darija-latin` / locale `ar-MA` / script `latin`: PASS, violations=[]

Scrubbed artifact:
- artifact ID: `11104402477`
- SHA-256 of uploaded artifact zip:
  `4b860f26e0eea9ed2a7a8462e16e94c34268cb0024b781d700d2a00cc7f96e5d`

### Repository checks on the same code HEAD

- Django migration drift #4204: **SUCCESS**
- CI #5185: **PENDING at certification-doc update time**
- Companion real chat E2E screenshots #346: **PENDING at certification-doc update time**

The certification document update is metadata-only and intentionally retriggers the
protected-shadow workflow so the final PR HEAD can be validated independently before merge.

## Boundary of certification

This certification proves the bounded token-only internal-live transport and its local
verification path. It does **not** certify general patient-data egress, change Groq's
patient-data processor approval status, authorize patient-visible provider narration,
or approve any Vercel deployment.

The deterministic IAMINA clinical reply remains authoritative and patient-visible during
this lot.

## Rollback

Set either of the following to `false`:

- `NARRATION_PROTECTED_PROVIDER_SHADOW`
- `NARRATION_PROTECTED_PROVIDER_INTERNAL_LIVE`

No schema or data rollback is required.
