# Skill — LOT Execution

## Purpose
Execute one roadmap LOT from evidence to merge without scope drift.

## Mandatory sequence
1. Read `AGENTS.md`, `docs/ROADMAP.md`, `docs/CONTRIBUTING.md`, relevant architecture/spec/ADR.
2. Confirm `main` and the exact starting SHA.
3. Define one responsibility, acceptance criteria, non-scope and evidence plan.
4. Create one short-lived branch and one PR for the LOT.
5. Inspect/reproduce before editing.
6. Apply the smallest coherent change.
7. Add or update permanent regression tests when a durable contract changes.
8. Run focused checks first, then all relevant repository gates.
9. Review the final diff file-by-file; remove temporary workflows/scripts/generated noise.
10. Hand off to an independent Reviewer. Builder may not certify its own work.
11. Remediate every blocking Reviewer finding and re-run affected evidence.
12. Hand off to the Release Certifier.
13. Update canonical docs before closure. If the SHA changes, re-run exact-head gates.
14. Merge with expected-head locking.
15. Verify `main`, then require post-merge CI and migration drift before declaring 100% complete.

## Fail conditions
- Unproven claims.
- More than one roadmap responsibility in the same LOT without explicit inseparability rationale.
- Temporary bypass or weakened safety gate.
- Stale test evidence after the head SHA changed.
- Canonical documentation disagreeing with merged reality.

## Required closeout evidence
Branch, PR, exact head SHA, tests/gates, Reviewer verdict, Certifier verdict, merge SHA, post-merge gates, next LOT.