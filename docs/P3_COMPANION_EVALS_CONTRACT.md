# P3-EVALS — Companion Intelligence Evaluation Contract

Status: AUTOMATED IMPLEMENTATION COMPLETE — HUMAN REVIEW REQUIRED

## Objective

Convert the already-certified companion behavior into measurable release evaluations without creating a second decision engine or expanding runtime authority.

## Evaluation dimensions

1. `LONGITUDINAL` — ordered evidence windows preserve anchor, lifecycle and provenance semantics.
2. `NEGATIVE` — absent, insufficient or contradictory evidence fails closed instead of manufacturing a positive observation.
3. `FALSE_POSITIVE` — benign or non-matching inputs do not acquire a stronger interpretation or action class.
4. `BOUNDARY` — outputs remain inside the existing certified authority contract.

## Hard release rule

Every scenario marked `HARD` must pass. The threshold for all hard scenarios is 100%.

Automated success does not replace the human-review requirement already present in the roadmap. Human-reviewed scenarios require explicit review provenance before P3-EVALS can close.

## Existing blocking foundations

The evaluation lane reuses the existing companion, semantics, shield and advice regression suites already executed by full backend pytest CI. It does not duplicate their underlying logic.

## Implementation state

- EVALS-0 implemented and merged.
- EVALS-1 implemented and merged.
- EVALS-2 implemented and merged; post-merge CI #2034 and drift #1846 passed.
- EVALS-3 implemented and merged as `58f5dd4b…`; exact-head CI #2035 + drift #1847 passed; post-merge CI #2037 + drift #1849 passed.
- Final human review remains required before closeout.
