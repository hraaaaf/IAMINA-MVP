# Companion product audit — 2026-08-16

Status: SMART audit complete; Decision B implemented; certification pending.

## Product contract

Companion is a governed, read-only interpretation layer. It may summarize repeated observations, changes since an explicit review anchor and structured after-visit facts. It must expose useful uncertainty without leaking machine codes, and must never infer diagnosis, treatment efficacy, dose changes or a consultation that was not explicitly recorded.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Brand/header + close | Clear full-screen identity and exit | 9.0/10 | KEEP |
| Page purpose | Explains patterns / change / uncertainty before interpretation | 9.5/10 | KEEP |
| Safety card | Essential clinical-authority boundary | 9.0/10 | KEEP localized frontend notice; backend `safety_notice` remains semantic evidence |
| Loading state | Truthful neutral waiting state | 9.0/10 | KEEP |
| Data-unavailable state | Explicitly avoids invented interpretation and offers retry | 9.5/10 | KEEP |
| What your data shows | Core governed pattern surface | 9.5/10 | KEEP |
| Evidence pill | Quick repeatability signal | 8.5/10 | KEEP with uncertainty disclosure; evidence density is not probability or clinical confidence |
| Recurrence count | Factual support against vague narrative | 9.5/10 | KEEP |
| Pattern limitations | Backend supplies machine-coded limitations | 4.0/10 baseline → 9.2/10 provisional | Decision B — show only known, context-specific localized explanations when relevant |
| Since last review | Longitudinal comparison only from explicit review anchor | 9.5/10 | KEEP |
| Change cards | Governed change kind without treatment attribution | 9.0/10 | KEEP |
| Missing-data disclosure | Backend supplies machine-coded `missing_data[]` | 4.0/10 baseline → 9.2/10 provisional | Decision B — short localized explanation only when a known reason is relevant |
| No-review state | Refuses fabricated review history | 9.8/10 | KEEP |
| After-visit continuity | Tied to an explicit recorded consultation | 9.5/10 | KEEP |
| No-recorded-visit state | Refuses to infer consultation from activity | 9.8/10 | KEEP |
| Recorded visit facts | Structured follow-up count without causal claim | 9.5/10 | KEEP |
| Post-visit causality disclaimer | Prevents treatment-efficacy inference | 9.8/10 | KEEP |

## Decision B — implemented contract

- Pattern cards map `limitations[]` through a known FR/EN/AR allow-list and render only non-null patient-facing explanations.
- Change cards do the same for `missing_data[]`.
- Unknown/generic machine codes resolve to `null` and are never shown raw.
- Generic clinical-authority boilerplate stays in the safety card rather than being duplicated on every card.
- No backend logic, evidence classification, diagnosis, treatment, dose or causal semantics changed.

## Safety-notice decision

The backend `safety_notice` is currently English prose. Replacing the localized frontend card directly would regress FR/AR localization. The frontend therefore keeps its localized safety copy while the backend notice remains the semantic contract.

## Anti-regression

`frontend/test/features/companion_uncertainty_copy_contract_test.dart` locks the governed reason-code mapping, unknown-code suppression and screen integration.

## Certification gate

No final page score or CLOSED status before exact-head CI/drift/UI/real Chrome, runtime merge, post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
