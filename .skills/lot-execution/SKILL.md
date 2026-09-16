# Skill — LOT Execution

## Purpose
Execute one roadmap LOT from evidence to merge without scope drift.

## Mandatory sequence
1. Read `AGENTS.md`, `docs/ROADMAP.md`, `docs/CONTRIBUTING.md`, `docs/QUALITY_SCORING_POLICY.md`, relevant architecture/spec/ADR.
2. Confirm `main` and the exact starting SHA.
3. Define one responsibility, acceptance criteria, non-scope and evidence plan.
4. Create one short-lived branch and one PR for the LOT.
5. Inspect/reproduce before editing.
6. Apply the smallest coherent change.
7. Add or update permanent regression tests when a durable contract changes.
8. Run focused checks first, then all relevant repository gates.
9. For every material step, record `EXECUTION_SCORE /10` and an adversarial `ADVERSARIAL_SCORE /10`; retain the lower score and apply every cap in `docs/QUALITY_SCORING_POLICY.md`.
10. If the two scores differ by more than `0.5`, investigate, remediate/justify, rerun affected evidence and rescore before continuing.
11. Review the final diff file-by-file; remove temporary workflows/scripts/generated noise.
12. Hand off to an independent Reviewer. Builder may not certify its own work.
13. Remediate every blocking Reviewer finding and re-run affected evidence.
14. Hand off to the Release Certifier.
15. If the LOT retained score is `>= 9.0/10` and binary gates are green, perform the mandatory final **Perfection Pass** from `docs/QUALITY_SCORING_POLICY.md`; fix every materially improvable in-scope weakness, rerun affected evidence and rescore.
16. Update canonical docs before closure. If the SHA changes, re-run exact-head gates.
17. A LOT may be `VERIFIED` only when the final retained score is `>= 9.0/10`, every required binary gate is green, no blocker remains, scoring discrepancies are resolved, and the Perfection Pass is complete.
18. Merge with expected-head locking.
19. Verify `main`, then require post-merge CI and migration drift before declaring 100% complete.

## Scoring invariants
- Never average Execution and Adversarial scores; retained score is the lower value after applicable caps.
- The LOT score is the lowest retained material-step score, never an average across steps.
- Same executor + adversarial reviewer caps the retained score at `9.4/10`.
- `9.5+` requires a genuinely independent review.
- Required red test or missing/stale required proof caps at `7.9/10`.
- Demonstrated regression caps at `6.9/10` until remediated and rerun.
- Blocking security/privacy/data/clinical-claim finding caps at `5.9/10` and forces `BLOCKED`.
- UI visual fidelity without real Target ↔ Render comparison is capped at `7.5/10`.
- No weak critical dimension may be hidden by an average.

## Fail conditions
- Unproven claims.
- More than one roadmap responsibility in the same LOT without explicit inseparability rationale.
- Temporary bypass or weakened safety gate.
- Stale test evidence after the head SHA changed.
- Canonical documentation disagreeing with merged reality.
- Declaring `VERIFIED` below `9.0/10`, with a red/missing binary gate, unresolved `>0.5` score gap, or before the Perfection Pass.

## Required closeout evidence
Branch, PR, exact head SHA, tests/gates, per-material-step Execution/Adversarial/retained scores, applied caps, discrepancy investigations, Reviewer verdict, Perfection Pass result, Certifier verdict, merge SHA, post-merge gates, next LOT.
