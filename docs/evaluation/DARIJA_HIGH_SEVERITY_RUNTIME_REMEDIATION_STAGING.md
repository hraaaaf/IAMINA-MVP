# Darija high-severity runtime remediation staging

Status: **STAGED / FAIL-CLOSED / NO RUNTIME CHANGE**

This lot converts the completed Moroccan Darija native review into an explicit runtime-remediation delta without bypassing restricted safety governance.

## Verified review delta

- Exact reviewed runtime inventory: 36 ar-MA variants.
- Native accepted existing variants: 15.
- Native rejected existing variants: 21.
- New native replacement candidates: 4.
- Current runtime changed by this staging lot: **no**.

The machine-readable source is:
`backend/core/tests/fixtures/darija_high_severity_runtime_remediation_plan.json`.

## Pending replacement candidates

| Native evidence | Normalized runtime candidate | Input form | Semantic group |
| --- | --- | --- | --- |
| `ghadi nskhef` | `ghadi nskhef` | Latin transliteration | consciousness / fainting |
| `غادي نسخف` | `غادي نسخف` | Arabic script | consciousness / fainting |
| `kantr33d` | `kantr33d` | Latin transliteration | tremor / shivering |
| `Ddokha` | `ddokha` | Latin transliteration | dizziness |

`Ddokha` is preserved as the exact native evidence string. The proposed runtime token is lowercase because the deterministic classifier lowercases Latin input before matching.

## Why the cutover is atomic

Removing all 21 rejected phrases immediately would reduce coverage in semantic groups where the reviewed replacement is not yet authorized for runtime. Adding the replacements immediately would violate the lexicon-promotion contract, which requires clinical review, safety-owner review, parity review, complete regression classes and an explicit `approved_for_runtime` decision.

Therefore the safe sequence is:

1. keep the current runtime inventory unchanged while restricted promotion gates are intentionally open;
2. lock the 21-to-remove and 4-to-add delta in tests;
3. prove the four candidates remain inactive and fail closed;
4. when restricted review is deliberately resumed, perform an atomic cutover: remove rejected variants and add only candidates that satisfy the promotion contract;
5. regenerate the safety-corpus fingerprint and rerun positive, negative, contextual, hyperbole and ambiguity regressions.

## Governance boundary

This staging artifact is native-language working evidence and technical preparation only. It is **not** clinical approval, safety-owner approval, parity approval, restricted approval, certification, pilot authorization or runtime authorization.

No P0-MENA-2 roadmap checkbox is closed by this staging lot.
