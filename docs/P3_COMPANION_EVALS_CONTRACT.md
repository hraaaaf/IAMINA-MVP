# P3-EVALS — Companion Intelligence Evaluation Contract

Status: CONTRACT CANDIDATE

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

## Planned implementation

- P3-EVALS-0 — contract, taxonomy and blocking manifest.
- P3-EVALS-1 — deterministic scenario runner and machine-readable report.
- P3-EVALS-2 — longitudinal, negative and false-positive scenario corpus.
- P3-EVALS-3 — human-review provenance and release certification.
- Canonical closeout only after every hard scenario passes and required human review evidence exists.
