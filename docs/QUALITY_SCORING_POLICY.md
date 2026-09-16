# IAmina — Quality Scoring & Verification Policy

This file is the canonical scoring policy for material execution steps, LOT verification and release certification.

## Scope

A **material step** is any implementation, remediation, migration, UI/UX change, security/privacy/data change, clinical-claim change, or other step whose failure could materially affect the LOT outcome.

Every material step MUST be scored twice after evidence is available:

- `EXECUTION_SCORE /10` — score of the implemented result against its explicit goal, acceptance criteria and evidence.
- `ADVERSARIAL_SCORE /10` — score from a deliberately critical review that tries to falsify the Builder's result, identify regressions, missing proof, weak assumptions and hidden failure modes.

The retained score is never an average:

`RETAINED_SCORE = min(EXECUTION_SCORE, ADVERSARIAL_SCORE, all applicable caps, every critical-dimension score)`

For a LOT containing multiple material steps, the LOT score is the **lowest retained material-step score**, never an average across steps.

## Mandatory discrepancy investigation

If `abs(EXECUTION_SCORE - ADVERSARIAL_SCORE) > 0.5`, the discrepancy MUST be investigated before verification. The investigation must identify why the two evaluations differ, remediate or justify the discrepancy, rerun affected evidence, and rescore.

A LOT cannot become `VERIFIED` while such a discrepancy remains unresolved.

## Score discipline

- `10.0/10` is exceptional. It requires complete evidence, all binary gates green, no known in-scope weakness that is realistically improvable, and a genuinely independent review.
- Any retained score `>= 9.5/10` requires a **genuinely independent adversarial review** by a reviewer that did not perform the execution and independently re-reads the diff/evidence.
- If the same person/model/session performs both execution and adversarial review, the retained score is automatically capped at `9.4/10`, even when the passes are isolated.
- A required test that is red, or required proof that is absent/stale, caps the retained score at `7.9/10`.
- A demonstrated regression caps the retained score at `6.9/10` until the regression is remediated and the affected evidence is rerun.
- A blocking security, privacy, data-integrity, or clinical-claim finding caps the retained score at `5.9/10` and the status MUST be `BLOCKED` until resolved.
- For UI/UX work, if there is no real `Target ↔ Render` comparison at the required identical viewports/states, the **visual-fidelity dimension** is capped at `7.5/10`.
- No strong average may hide a weak critical dimension. Every critical dimension is scored explicitly and participates in the `min(...)` retained-score rule.

Caps stack by taking the lowest applicable cap.

## Binary gates

Scores never override binary gates. A LOT may be `VERIFIED` only when:

1. every required binary gate is green on the exact applicable HEAD/evidence set;
2. no blocking finding remains;
3. every material step has both required scores;
4. all score discrepancies `> 0.5` have been investigated and resolved;
5. the LOT retained score is at least `9.0/10`;
6. the mandatory final Perfection Pass has completed.

A LOT below `9.0/10` is `NOT_VERIFIED` even if all binary gates are green.

## Mandatory Perfection Pass

A score at or above `9.0/10` does **not** close a LOT by itself. Before `VERIFIED`, perform one final **Perfection Pass**:

1. list the remaining weaknesses, rough edges, uncertainties and non-blocking findings;
2. identify which are realistically improvable inside the approved scope;
3. fix every materially improvable in-scope weakness;
4. rerun all evidence affected by those fixes on the new exact HEAD;
5. repeat Execution + Adversarial scoring under this policy;
6. document any residual issue that is genuinely non-improvable, externally blocked, or explicitly out of scope.

Example: a LOT at `9.2/10` still requires the Perfection Pass. It is not `VERIFIED` until the pass is complete and the final retained score remains `>= 9.0/10` with all binary gates green.

## Required reporting format

For every material step:

```text
Goal:
Success criterion:
Evidence:
Critical dimensions:
EXECUTION_SCORE: x.x/10
ADVERSARIAL_SCORE: x.x/10
Gap: x.x
Applicable caps: none | ...
RETAINED_SCORE: x.x/10
Status: OPEN | BLOCKED | READY_FOR_PERFECTION_PASS | VERIFIED
Remaining weaknesses:
Next exact action:
```

For LOT closeout, record the lowest retained step score, binary-gate state, independent-review status, Perfection Pass result, and the exact evidence/HEAD used.

## Independence definition

A **genuinely independent review** means the reviewer did not author the implementation and performs a fresh review of the final diff, rendered/runtime evidence, tests and claims without inheriting the Builder's conclusion as proof. A different human, agent, or model context may satisfy this only when it actually performs that independent evidence review.

An isolated second pass by the same executor is still valuable and mandatory when no independent reviewer is available, but the automatic `9.4/10` cap applies.
