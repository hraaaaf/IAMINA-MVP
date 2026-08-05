# P0 Product Truthfulness

> **Status: CLOSED.** Five independently validated LOTs are merged or carried by the final closure PR #43.

This P0 ensures that every patient-facing promise in IAmina is real, traceable and
clinically safe. A visually convincing control is not considered a feature unless
its state and outcome are backed by executable behavior.

## Closure checklist

| Item | Requirement | Status | Evidence |
|---|---|---|---|
| P0-UX-1 | Every apparent action is functional or explicitly unavailable | **Closed** | PR #39; `p0_real_actions_contract_test.dart` |
| P0-UX-2 | System states such as synchronization, notifications and pilot status are live and truthful | **Closed** | PR #40; typed `SyncUiState`; `p0_truthful_system_state_contract_test.dart` |
| P0-UX-3 | Clinical conclusions, confidence and goals are explainable; no opaque score or fabricated precision | **Closed** | PR #41; `p0_clinical_explainability_contract_test.dart` |
| P0-UX-4 | Import is reachable and usable on mobile | **Closed** | PR #42; 390 × 844 and 360 × 560 widget journeys |
| P0-UX-5 | Privacy wording never exceeds approved deployment and processor evidence | **Closed** | PR #43; `p0_privacy_truthfulness_contract_test.dart` |

## P0-UX-1 — real actions

PR #39 closes false or empty controls, preserves the real Drift CRUD loop and
requires unavailable integrations to be visibly non-interactive.

## P0-UX-2 — truthful system state

PR #40 makes synchronization, offline, pending and error labels derive from typed
runtime state. Local storage is never presented as confirmed server synchronization.

## P0-UX-3 — clinical explainability

PR #41 removes fabricated confidence, decorative trends and opaque scores. Discrete
manual/imported readings are not labelled as CGM time, and KPI method, coverage and
limitations remain visible.

## P0-UX-4 — mobile import

PR #42 proves that Importer remains reachable at 390 px, the real Pulper route opens,
and the picker remains scrollable without overflow at 360 × 560. Persistence still
requires explicit review and confirmation.

## P0-UX-5 — privacy truthfulness

PR #43 closes privacy overclaiming through a fail-closed patient-facing contract:

- no provider name is hardcoded as a permanent deployment fact;
- consent text does not promise pseudonymisation, no-training, no-retention or
  third-party-sales guarantees without deployment evidence;
- French, English and Arabic state that external processing requires valid consent
  plus approved provider, region and retention policy;
- the document picker shows the external-processing gate before file selection;
- unsupported privacy claims are rejected permanently by a Flutter source contract;
- generated localizations are checked so reviewed ARB wording cannot drift from the
  runtime application.

## Closure and score policy

**P0 source and CI closure: 5/5 requirements complete.** A product score above
**9.5/10** still requires launching the certified merge commit and completing the
final visual/functional audit with no critical or high-severity finding. This file
does not convert source inspection into a deployment claim.
