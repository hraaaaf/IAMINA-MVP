# Profile product audit — 2026-08-16

Status: SMART audit complete; persisted-medical-default HUMAN GATE identified; runtime correction pending.

## Product contract

Profile stores patient-entered preferences and medical context. No diabetes type, treatment or glycemic target may become persisted patient truth merely because the UI supplied a default. Consent and account actions must remain explicit and independently reversible where possible.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Clear identity and settings context | 9.5/10 | KEEP |
| First-use completion panel | Correctly prompts completion without auto-saving | 9.5/10 | KEEP |
| Medical section container | Appropriate grouping of medically relevant profile context | 9.0/10 | KEEP, but inputs need truthfulness correction |
| Diabetes type choices | Useful patient context | 4.0/10 current | HUMAN GATE — UI starts on `type1` before a persisted profile exists |
| Treatment choices | Useful descriptive context | 4.0/10 current | HUMAN GATE — UI starts on `insulin` before a persisted profile exists |
| Glucose target fields | Important user/clinician-configured context used elsewhere | 3.5/10 current | HUMAN GATE — invalid/empty values silently fall back to 70/180 on save |
| Unit preference | Necessary display preference | 9.0/10 | KEEP; default mg/dL is a display preference, not medical diagnosis |
| Save medical profile | Necessary explicit persistence action | 6.0/10 current | IMPROVE after gate — must reject incomplete/invalid medical fields rather than synthesize defaults |
| Ramadan period | Useful MENA-specific temporal context | 9.2/10 | KEEP — explicit dates, order validation and partial local/server save reporting are strong |
| Ramadan clear | Necessary reversible configuration | 9.0/10 | KEEP |
| IAmina setup | Optional onboarding/configuration entry | 8.5/10 | KEEP collapsed; does not belong above medical profile |
| Account section | Appropriate home for sign-out/consent actions | 9.5/10 | KEEP |
| Sign out | Destructive session action with confirmation | 9.5/10 | KEEP |
| Withdraw AI consent | High-impact privacy action with confirmation and local/server handling | 9.5/10 | KEEP |

## Verified findings

- Before any persisted profile, state initializes `_diabetesType = 'type1'` and `_treatment = 'insulin'`; expanding the section therefore visually presents those choices as selected.
- `_saveProfile()` parses target fields with `double.tryParse(...) ?? 70.0/180.0`; blank or invalid input is silently converted to medical target values and persisted.
- The same save writes diabetes type, treatment, unit and target range together, so defaults become durable patient-profile data after one tap.
- First-use itself does **not** auto-save; the risk occurs at the explicit Save action when untouched defaults are accepted as truth.
- Ramadan period requires both dates, validates start <= end, writes locally and to server, and truthfully distinguishes full, local-only, server-only and failed save states.
- Consent withdrawal is explicitly confirmed and updates server/local consent state.
- Sign-out is explicitly confirmed.
- `preferredLanguage` is hardcoded to `fr` in the local profile save; this is a separate i18n/data-consistency issue and should be aligned with the active locale without changing medical semantics.

## HUMAN GATE — recommended choice

Recommended product contract:

- **A (recommended):** no diabetes type or treatment pre-selected for a new profile; require explicit choice before medical-profile save. Require valid target low/high values and reject blank/invalid/inverted targets instead of substituting 70/180.
- **B:** keep type/treatment defaults visible but require explicit acknowledgement before save; still reject invalid target fields.
- **C:** keep current defaults and silent target fallback. Not recommended because it persists inferred medical context as patient truth.

This gate changes persisted medical meaning and therefore must not be auto-executed.

## Certification gate

No final page score or CLOSED status before the human gate, runtime correction, exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
