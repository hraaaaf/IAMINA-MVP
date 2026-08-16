# Profile product audit — 2026-08-16

Status: CLOSED — 9.4/10.

## Product contract

Profile stores patient-entered preferences and medical context. No diabetes type, treatment or glycemic target may become persisted patient truth merely because the UI supplied a default. Consent and account actions remain explicit and independently reversible where possible.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Clear identity and settings context | 9.5/10 | KEEP |
| First-use completion panel | Prompts completion without auto-saving | 9.5/10 | KEEP |
| Medical section container | Appropriate grouping of medically relevant profile context | 9.4/10 | KEEP |
| Diabetes type choices | Useful patient context | 9.6/10 | Gate A complete — no preselection for a new profile |
| Treatment choices | Useful descriptive context | 9.6/10 | Gate A complete — no preselection for a new profile |
| Glucose target fields | Important user/clinician-configured context | 9.6/10 | Gate A complete — invalid/nonfinite/nonpositive/inverted values rejected; no silent 70/180 fallback |
| Unit preference | Necessary display preference | 9.0/10 | KEEP; default mg/dL is display preference, not diagnosis |
| Save medical profile | Explicit persistence action | 9.6/10 | Gate A complete — explicit type + treatment + valid range required |
| Ramadan period | Useful MENA-specific temporal context | 9.2/10 | KEEP |
| Ramadan clear | Necessary reversible configuration | 9.0/10 | KEEP |
| IAmina setup | Optional onboarding/configuration entry | 8.5/10 | KEEP collapsed |
| Account section | Appropriate home for sign-out/consent actions | 9.5/10 | KEEP |
| Sign out | Destructive session action with confirmation | 9.5/10 | KEEP |
| Withdraw AI consent | High-impact privacy action with confirmation and local/server handling | 9.5/10 | KEEP |

## Verified findings

- Before Gate A, new-profile state initialized `type1` and `insulin`, so untouched choices could become durable patient-profile data after Save.
- Before Gate A, `_saveProfile()` used `double.tryParse(...) ?? 70.0/180.0`, silently converting blank or invalid target input into persisted medical targets.
- HUMAN GATE A was approved on 2026-08-16.
- `_diabetesType` and `_treatment` are now nullable for a new profile; existing persisted values load as stored without substituting Type 1 or insulin.
- `_saveProfile()` requires explicit diabetes type + treatment and finite positive low/high values with `low < high`; invalid or incomplete input is rejected before any database write.
- No glycemic threshold value was changed and no treatment recommendation or new clinical target was introduced.
- Ramadan dates remain explicit, ordered and truthfully report local/server save outcomes.
- Consent withdrawal and sign-out remain explicitly confirmed.
- `preferredLanguage` remains hardcoded to `fr` in the local profile save. This is a separate i18n/data-consistency debt, not a medical-semantics blocker, and prevents a 9.5/10 final score.

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

## Certification evidence

- Exact-head `431a717653133312b9df4ad79bead58ffa7cc8e6`: CI #2541 SUCCESS, drift #2353 SUCCESS, UI screenshot audit #147 SUCCESS, real Chrome #110 SUCCESS.
- Chrome #110 390×844 was inspected directly: no diabetes type, treatment or target is presented as already selected; the medical section states `À compléter ou vérifier`; Ramadan remains unconfigured; no overflow or hierarchy regression was observed.
- Runtime PR #263 merged to `main` at `50d1d9d0b0ed25017b9b24d49c837690055c50b4`.
- Post-merge `50d1d9d0…`: CI #2542 jobs SUCCESS, drift #2354 SUCCESS, UI screenshot audit #148 SUCCESS, real Chrome #111 SUCCESS.
- Chrome #111 post-merge 390×844 was inspected directly and preserves the same neutral Gate A state and clean hierarchy.

## Final assessment

**9.4/10 — PASS / CLOSED.**

The medically significant defaults and fallback persistence defects are removed and locked by tests. The page is truthful, reversible where appropriate and fully certified pre/post merge. The remaining hardcoded language persistence is explicitly retained as i18n debt and is the reason the final score is not inflated to 9.5/10.

MENA roadmap numerator remains unchanged by this page audit.
