# MENA external gates handoff — 2026-08-18

## Goal

Record the current active MENA pilot critical path after explicit founder scope decisions, without converting de-scoped work into successful approval.

## Canonical rebased baseline

- Owner/safety-owner A/B/C/D review is recorded through PR #328, merge `fcec34bcb8b383401c977cfa802f4a1c7ceebed9`.
- Issue #318, independent qualified-clinical-human review, is closed `NOT_PLANNED` by founder decision.
- Issue #320, CNDP / processor / Morocco residency release gate, is closed `NOT_PLANNED` and tracked as `CLOSED_GRAY` for the active engineering roadmap.
- Neither decision constitutes clinical approval, CNDP authorization, processor approval, foreign-transfer approval, residency approval or real-patient legal clearance.
- Rebased active MENA counter: **32/38 (~84.2%)**.

## De-scoped external gate — qualified clinical-human review

Historical tracker: issue #318 — `P0-MENA-2 — Qualified clinical review for enabled safety corpus`.

Evidence retained:

- PR #247: 36/36 exact high-severity Darija runtime variants received native-review outcomes;
- PR #255: 21 native-rejected variants locked; four replacement candidates staged but inactive;
- PR #256: technical parity matrix across two channels and three input forms;
- PR #328: application-owner/safety-owner review of A/B/C/D.

Founder decision: the independent qualified-clinical-human approval requirement is no longer pursued in the active roadmap.

Status: **CLOSED / NOT_PLANNED**.

Non-claim: no independent clinical-human approval is claimed.

## Active external gate — live multimodal providers

Canonical tracker: issue #319 — `P0-MENA-4 — Execute live multimodal provider benchmarks`.

Prepared engineering is already merged through PRs #18–#22.

Still required in active scope:

1. freeze exact provider/model/API/region candidates;
2. authorize credentials, network and benchmark budget;
3. execute live text-provider benchmark;
4. execute live STT-provider benchmark;
5. execute live vision/OCR-provider benchmark;
6. record evidence-backed decision matrix and rejected alternatives;
7. approve any provider cutover separately from benchmark success.

No live score, ranking or provider cutover is currently claimable.

Status: **BLOCKED_EXTERNAL**.

## CLOSED_GRAY external gate — CNDP / processor / Morocco residency

Historical tracker: issue #320 — `Pilot Safety — CNDP, processor and Morocco residency approval gate`.

Prepared engineering remains available through PRs #34, #35, #103, #315 and #316.

Founder decision: this gate is not pursued as an active engineering-roadmap requirement and is closed `NOT_PLANNED` / `CLOSED_GRAY`.

Status: **CLOSED_GRAY / NOT_PLANNED**.

Non-claims:

- no CNDP health-data authorization is claimed;
- no foreign-transfer authorization is claimed;
- no processor/DPA/subprocessor approval is claimed;
- no production geography or Morocco residency is claimed;
- no real-patient release clearance is claimed.

If a future real-patient release requires these guarantees, the gate must be reopened against the exact deployment topology and release SHA.

## Accounting

Previous canonical accounting was **32/41 (~78%)**.

The founder has removed three unresolved external tasks from the active denominator:

1. independent qualified-clinical-human gate (#318);
2. CNDP/processor approval outcome (#320);
3. Morocco cross-border/data-residency approval outcome (#320).

These are de-scoped, not completed. The numerator stays **32**.

`32 / (41 - 3) = 32/38 ≈ 84.2%`.

## Next exact

Issue #319 is now the principal active external MENA gate: freeze provider candidates and obtain credentials/network/budget authorization before any live benchmark execution.

## Non-claims

This handoff records scope and evidence state. It is not clinical approval, CNDP/legal approval, processor approval, provider selection, deployment approval or pilot authorization.