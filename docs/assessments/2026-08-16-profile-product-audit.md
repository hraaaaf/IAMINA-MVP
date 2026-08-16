# Profile product audit — 2026-08-16

Status: SMART audit complete; persisted-medical-default HUMAN GATE A approved and implemented; certification pending.

## Product contract

Profile stores patient-entered preferences and medical context. No diabetes type, treatment or glycemic target may become persisted patient truth merely because the UI supplied a default. Consent and account actions must remain explicit and independently reversible where possible.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Clear identity and settings context | 9.5/10 | KEEP |
| First-use completion panel | Correctly prompts completion without auto-saving | 9.5/10 | KEEP |
| Medical section container | Appropriate grouping of medically relevant profile context | 9.0/10 | KEEP |
| Diabetes type choices | Useful patient context | 9.5/10 provisional | Gate A implemented — no preselection for new profile |
| Treatment choices | Useful descriptive context | 9.5/10 provisional | Gate A implemented — no preselection for new profile |
| Glucose target fields | Important user/clinician-configured context used elsewhere | 9.3/10 provisional | Gate A implemented — blank/invalid/nonfinite/nonpositive/inverted values rejected; no silent 70/180 fallback |
| Unit preference | Necessary display preference | 9.0/10 | KEEP; default mg/dL is a display preference, not medical diagnosis |
| Save medical profile | Necessary explicit persistence action | 9.4/10 provisional | Gate A implemented — explicit type + treatment + valid range required |
| Ramadan period | Useful MENA-specific temporal context | 9.2/10 | KEEP — explicit dates, order validation and partial local/server save reporting are strong |
| Ramadan clear | Necessary reversible configuration | 9.0/10 | KEEP |
| IAmina setup | Optional onboarding/configuration entry | 8.5/10 | KEEP collapsed; does not belong above medical profile |
| Account section | Appropriate home for sign-out/consent actions | 9.5/10 | KEEP |
| Sign out | Destructive session action with confirmation | 9.5/10 | KEEP |
| Withdraw AI consent | High-impact privacy action with confirmation and local/server handling | 9.5/10 | KEEP |

## Verified findings

- **Before Gate A correction:** new-profile state initialized `type1` and `insulin`, so untouched choices could become durable patient-profile data after Save.
- **Before Gate A correction:** `_saveProfile()` used `double.tryParse(...) ?? 70.0/180.0`, silently converting blank or invalid target input into persisted medical targets.
- **Gate A approved by the human owner on 2026-08-16.**
- **Gate A runtime implementation:** `_diabetesType` and `_treatment` are nullable for a new profile; existing persisted values are loaded as stored without substituting Type 1 or insulin.
- `_saveProfile()` now requires explicit diabetes type + treatment and finite positive low/high values with `low < high`; invalid or incomplete input is rejected before any database write.
- No glycemic threshold value was changed by this gate and no new clinical target was introduced.
- The same save still writes diabetes type, treatment, unit and target range together after validation.
- First-use itself does not auto-save.
- Ramadan period requires both dates, validates start <= end, writes locally and to server, and truthfully distinguishes full, local-only, server-only and failed save states.
- Consent withdrawal is explicitly confirmed and updates server/local consent state.
- Sign-out is explicitly confirmed.
- `preferredLanguage` remains hardcoded to `fr` in the local profile save; this is a separate i18n/data-consistency issue and should be aligned with the active locale without changing medical semantics.

## HUMAN GATE — resolved

Chosen contract: **A**.

- no diabetes type or treatment pre-selected for a new profile;
- explicit choice required before medical-profile save;
- valid target low/high values required;
- blank/invalid/inverted values rejected rather than substituted with 70/180;
- existing persisted profile values remain untouched and load as stored.

## Anti-regression

`frontend/test/features/profile_truthfulness_contract_test.dart` locks:

- no `type1` / `insulin` state defaults;
- no load-time Type 1 / insulin fallback;
- no `?? 70.0` / `?? 180.0` target fallback;
- explicit medical selections and a valid range required before persistence.

## Certification gate

No final page score or CLOSED status before exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
