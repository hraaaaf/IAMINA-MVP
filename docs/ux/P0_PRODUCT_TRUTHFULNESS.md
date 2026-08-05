# P0 Product Truthfulness

> Status: active closure sequence. One LOT, one PR, one independently validated responsibility.

This P0 exists to ensure that every patient-facing promise in IAmina is real,
traceable and clinically safe. A visually convincing control is not considered a
feature unless its state and outcome are backed by executable behavior.

## Closure checklist

| Item | Requirement | Status | Evidence |
|---|---|---|---|
| P0-UX-1 | Every apparent action is functional or explicitly unavailable | **Closed** | PR #39; `p0_real_actions_contract_test.dart` |
| P0-UX-2 | System states such as synchronization, notifications and pilot status are live and truthful | **Closed** | PR #40; typed `SyncUiState`; `p0_truthful_system_state_contract_test.dart` |
| P0-UX-3 | Clinical conclusions, confidence and goals are explainable; no opaque score or fabricated precision | **In validation** | Coverage-aware KPI UI; `p0_clinical_explainability_contract_test.dart` |
| P0-UX-4 | Import is reachable and usable on mobile | Existing implementation observed; dedicated certification pending | Module registry and bottom navigation derive `/importer` |
| P0-UX-5 | Privacy wording never exceeds approved deployment and processor evidence | Open | Dedicated LOT required |

## P0-UX-1 contract

PR #39 closes the first requirement by enforcing all of the following:

- the desktop summary discovery control scrolls to real content;
- decorative notification controls are removed rather than simulated;
- unavailable Dexcom and Libre integrations are labelled non-interactive and
  unavailable, with no fake waitlist action;
- fallback summary content is observation-only and contains no insulin-dose or
  basal-adjustment suggestion;
- accept/ignore controls that only changed ephemeral local state are removed;
- the real create, read, update and delete loop is continuously checked against
  Drift persistence and journal routes;
- mobile navigation derivation includes the Import destination.

## P0-UX-2 contract

PR #40 closes the second requirement by making synchronization and storage claims
derive from real runtime state:

- `SyncService` exposes checking, up-to-date, pending, syncing, offline and error
  states;
- connectivity loss produces an explicit offline state rather than a success icon;
- pending local records produce a pending state;
- only an empty pending queue or confirmed successful synchronization may produce
  the up-to-date state;
- partial and total failures produce an error state with a retry action;
- the dashboard renders the authoritative state with accessible labels and tooltips;
- data shown on the Import page is labelled as local storage, not synchronization;
- decorative notification controls and static success labels are permanently
  rejected by the source contract.

## P0-UX-3 contract

The current LOT removes fabricated clinical precision and exposes the basis of each
patient-facing metric:

- a discrete set of manual/imported entries is labelled **measures in range**, not
  continuous **time in range**;
- measurement count and number of represented days are visible alongside the
  target-range, GMI and CV metrics;
- thresholds are labelled as general, non-personalized references and explicitly
  state that a patient's target may differ;
- GMI states its available-data basis, flags limited coverage and says that it does
  not replace a laboratory HbA1c;
- summary KPI cards expose coverage and remain readable on mobile and desktop;
- severity is never converted into a fabricated confidence percentage;
- threshold comparisons are never rendered as historical trend arrows;
- automated findings are labelled as observations and actions as points to discuss,
  not personalized prescriptions;
- the permanent Flutter contract rejects opaque `/100` scores, decorative signal
  strength, unsupported confidence labels and misleading CGM-duration wording.

## Score policy

A score above **9.5/10** may only be claimed after all five checklist items are
closed, the complete CI matrix is green, the application is launched from the
certified commit and the final visual/functional audit finds no critical or high
severity issue. Preparation work and source inspection alone do not increase the
score.
