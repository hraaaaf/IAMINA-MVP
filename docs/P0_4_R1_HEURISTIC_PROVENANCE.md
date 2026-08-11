# P0.4-R1 — Legacy Heuristic Provenance Remediation

> **Scope:** correct the clinical authority label of compatibility-only legacy heuristic memory after PR #114.  
> **Non-scope:** no clinical threshold/formula, patient-facing behavior, database schema, provider or UX change.  
> **Closure rule:** P0.4 remains open until this remediation is exact-head certified, merged with expected-head locking, and post-merge CI + migration drift are green.

## Finding

PR #114 correctly removed active learning and prompt steering from legacy `food_sensitivities`, but its v2 provenance map labelled `food_sensitivities` and `peak_hours` as `DETERMINISTIC_DERIVATION`.

That label is too strong. Under the P0.2 truth contract an approved deterministic derivation may enter deterministic clinical logic. These legacy fields were produced by historical heuristics without an approved clinical derivation contract, so persistence must not grant them that authority.

## Remediation contract

- `TruthKind.HEURISTIC_INFERENCE` explicitly represents non-authoritative heuristic output.
- `HEURISTIC_INFERENCE` cannot persist as patient clinical fact and cannot enter deterministic clinical logic.
- `deep.food_sensitivities` and `deep.peak_hours` use `HEURISTIC_INFERENCE` provenance.
- The exact deterministic markers briefly emitted by PR #114 are accepted only as backward-compatible read aliases for those two fields.
- Re-encoding a decoded snapshot writes the corrected `HEURISTIC_INFERENCE` marker.
- Any other wrong/tampered marker still fails closed to the field default.
- Existing P0.4 behavior remains unchanged: the legacy food heuristic is not actively learned and cannot drive `next_intention`.

## Required certification

1. Focused authority/provenance regressions.
2. Full backend + PostgreSQL source-of-truth + Flutter CI.
3. Django migration drift SUCCESS with no migration expected.
4. Clinical Safety Reviewer FINAL PASS.
5. Database & Migration Reviewer FINAL PASS.
6. Release Certifier GO on the same exact head.
7. Expected-head locked merge.
8. Post-merge CI + migration drift SUCCESS on `main` before P0.4 is declared CLOSED 100%.
