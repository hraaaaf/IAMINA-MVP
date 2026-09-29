# IAMINA — Protected Shadow Promotion Gate

Status: **BLOCKED BY PROCESSOR GOVERNANCE — EXPECTED**

## Goal

Turn protected-shadow evidence into an explicit, deterministic and reversible promotion
decision without activating provider traffic or changing patient-visible output.

## Success

The gate may return `promotable=true` only when every prerequisite is explicitly
supplied and satisfied:

- processor governance is explicitly approved;
- provider payload boundary is verified;
- protected narration adversarial gate is green;
- kill switch is verified;
- deterministic fallback is verified;
- clinical authority is unchanged;
- campaign contains at least one observation;
- campaign contains zero blocked turns;
- campaign contains zero errors;
- campaign contains zero unresolved rejections;
- every observed turn is accepted.

Any missing or failed prerequisite blocks promotion.

## Current verified decision

The current repository/governance state has **not** approved Groq for patient-data
processor egress. Therefore the promotion gate must remain blocked. This lot must not
change processor policy to make the decision pass.

## Boundary

This gate is evidence evaluation only. It does not:

- modify processor policy;
- enable `NARRATION_PROTECTED_PROVIDER_SHADOW`;
- create provider traffic;
- authorize internal live opt-in;
- authorize patient exposure;
- change clinical authority;
- change deterministic patient output;
- deploy Vercel.

## Next human gate

A real internal-live campaign remains unavailable until processor governance is
explicitly approved outside this evaluator. After such approval, evidence must still be
collected and re-evaluated; governance approval alone is not sufficient for promotion.
