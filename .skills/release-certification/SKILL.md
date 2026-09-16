# Skill — Release Certification

## Purpose
Provide an independent GO/NO-GO after Builder and Reviewer work is complete.

The Certifier MUST apply `docs/QUALITY_SCORING_POLICY.md`.

## Certifier must verify
1. Scope matches one LOT and the PR diff contains no unrelated changes.
2. Reviewer findings are resolved or explicitly accepted by the human owner; no blocker remains.
3. Exact-head CI and migration drift are green after the final code/docs SHA.
4. Required specialized evidence is green: UX captures, PostgreSQL, clinical safety, security, OpenAPI, locale parity, etc., according to touched surfaces.
5. Every material step has an `EXECUTION_SCORE /10`, an `ADVERSARIAL_SCORE /10`, applicable caps, and a retained score equal to the lower admissible value — never an average.
6. Every score gap greater than `0.5` has a documented investigation, affected remediation/evidence rerun, and final rescore.
7. The LOT retained score is the lowest retained material-step score; no weak critical dimension is hidden by an average.
8. `9.5+` has a genuinely independent review. If the same executor performed the adversarial review, the `9.4/10` cap is enforced.
9. Required red/missing evidence, regressions, blockers, and UI-without-Target↔Render caps from the canonical scoring policy have been applied.
10. The mandatory final Perfection Pass is complete: remaining weaknesses were enumerated, every materially improvable in-scope weakness was fixed, affected evidence was rerun, and the final score was recalculated.
11. Canonical docs reflect the delivered truth and do not claim work not yet merged.
12. No temporary workflow/script, generated dependency noise, credential, debug artifact or bypass remains in the merge diff.
13. Merge is performed with expected-head SHA locking.
14. `main` points to the expected merge SHA and post-merge CI + migration drift complete successfully.

## Verification threshold
A LOT may be `VERIFIED` / `CERTIFIED` only when:

- final retained score is `>= 9.0/10`;
- every required binary gate is green;
- no blocking finding remains;
- every `>0.5` Execution/Adversarial discrepancy is resolved;
- the Perfection Pass is complete.

A score below `9.0/10` is `NO_GO` for `VERIFIED`, even if binary gates are green.

## Verdicts
- `NO_GO`: any blocker, stale/missing evidence, unresolved review finding, failed binary gate, unresolved score discrepancy, retained score `<9.0`, or incomplete Perfection Pass.
- `CERTIFIED_WITH_NON_BLOCKING_FINDINGS`: only when all verification thresholds above are met and any residual findings are explicitly non-blocking, non-improvable in current scope, and recorded.
- `CERTIFIED`: all applicable evidence is complete and clean, thresholds are met, and the final Perfection Pass found no remaining materially improvable in-scope weakness.

The Certifier must never infer PASS from Builder confidence, a high average, or a subset of checks.
