# IAMINA — Protected Shadow Internal Campaign

Status: **PREPARED — NO PATIENT EGRESS, NO PROVIDER ACTIVATION**

## Goal

Prepare a bounded internal shadow campaign for the protected narration path without
changing patient-visible output, processor policy, clinical authority, or Vercel state.

## Success criteria

The campaign is considered executable only when all of the following are true:

- population is restricted to active internal staff accounts;
- family is restricted to `CLINICIAN_PREP`;
- provider remains `groq`;
- a finite `max_turns` is fixed before execution;
- locales/scripts are fixed in the local scenario manifest before execution;
- telemetry persists only the existing allowlisted event fields:
  `event | status | provider | family`;
- reporting contains counts only for
  `disabled | blocked | accepted | rejected | error`;
- patient-visible reply remains the deterministic governed reply byte-for-byte;
- the adversarial protected narration gate remains green;
- processor policy is never modified to make a campaign pass.

## Current governance constraint

Groq processor policy is still not approved for patient-data egress.

Therefore this lot may prepare and verify:

1. campaign protocol and hard bounds;
2. local scenario manifest;
3. content-free reporting;
4. dry-run / synthetic accepted-rejected-error paths;
5. policy-blocked internal runtime behavior.

It must **not** create real patient provider traffic until processor governance is
explicitly approved.

## Campaign manifest

The manifest must be local test/config data and must not be added to persisted runtime
telemetry.

Required fields:

- campaign id;
- max turns;
- locale;
- script;
- scenario id;
- expected path: blocked / synthetic verifier path.

Do not include patient ids, patient messages, clinical values, deterministic reply
bodies, tokens, rule ids, or free-form provider errors.

## Reporting

Use `ProtectedShadowCampaignProtocol` and
`summarize_protected_shadow_campaign()`.

The reporter fails closed when:

- an event contains any non-allowlisted field;
- event/provider/family is unexpected;
- status is outside the five allowed values;
- observed events exceed `max_turns`.

## Promotion protocol

Promotion is a separate decision from feature-flag activation.

Minimum prerequisites before any internal live provider opt-in:

- processor/legal governance explicitly approved;
- exact provider payload still limited to locale/script/opaque protected-body token;
- adversarial gate green on exact candidate HEAD;
- bounded campaign results reviewed;
- rejected/error causes understood;
- kill switch verified;
- deterministic fallback verified;
- no increase in clinical authority.

Patient exposure remains a later, separately authorized lot.

## Explicit non-goals

- no processor-policy edit;
- no patient egress;
- no production provider activation;
- no new clinical rule family;
- no Vercel deployment.
