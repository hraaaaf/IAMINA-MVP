# IAMINA — Protected Shadow Internal Live Certification

Status: **CERTIFIED PRE-MERGE**

Date: 2026-09-30
PR: #840
Branch: `conversation/protected-shadow-internal-live-bounded`
Certified HEAD: `39d2c6db744553750b819ee595ad1d330b013bc3`

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

Workflow run: **#34**
Run ID: `36725384424`
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
- artifact ID: `11103020201`
- SHA-256 of uploaded artifact zip:
  `ebce81082f4547b0c774efe8894301684be067176b6e6b326008a3a3544a2966`

### Repository checks on the same HEAD

- CI #5182: **SUCCESS**
- Django migration drift #4201: **SUCCESS**
- Companion real chat E2E screenshots #343: **SUCCESS**

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
