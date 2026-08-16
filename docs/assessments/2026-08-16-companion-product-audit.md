# Companion product audit — 2026-08-16

Status: **CLOSED — PASS 9.5/10**.

## Product contract

Companion is a governed, read-only interpretation layer. It may summarize repeated observations, changes since an explicit review anchor and structured after-visit facts. It must expose useful uncertainty without leaking machine codes, and must never infer diagnosis, treatment efficacy, dose changes or a consultation that was not explicitly recorded.

## SMART section audit

| Section | Product interest | Final score | Decision / status |
|---|---|---:|---|
| Brand/header + close | Clear full-screen identity and exit | 9.0/10 | KEEP |
| Page purpose | Explains patterns / change / uncertainty before interpretation | 9.5/10 | KEEP |
| Safety card | Essential clinical-authority boundary | 9.0/10 | KEEP localized frontend notice; backend `safety_notice` remains semantic evidence |
| Loading state | Truthful neutral waiting state | 9.0/10 | KEEP |
| Data-unavailable state | Explicitly avoids invented interpretation and offers retry | 9.5/10 | KEEP — real Chrome certified |
| What your data shows | Core governed pattern surface | 9.5/10 | KEEP |
| Evidence pill | Quick repeatability signal | 9.0/10 | KEEP with uncertainty disclosure; evidence density is not probability or clinical confidence |
| Recurrence count | Factual support against vague narrative | 9.5/10 | KEEP |
| Pattern limitations | Exposes relevant uncertainty without leaking machine codes | 9.5/10 | IMPROVED — Decision B, localized known reasons only |
| Since last review | Longitudinal comparison only from explicit review anchor | 9.5/10 | KEEP |
| Change cards | Governed change kind without treatment attribution | 9.0/10 | KEEP |
| Missing-data disclosure | Explains why a comparison is limited when relevant | 9.5/10 | IMPROVED — Decision B, localized known reasons only |
| No-review state | Refuses fabricated review history | 9.8/10 | KEEP |
| After-visit continuity | Tied to an explicit recorded consultation | 9.5/10 | KEEP |
| No-recorded-visit state | Refuses to infer consultation from activity | 9.8/10 | KEEP |
| Recorded visit facts | Structured follow-up count without causal claim | 9.5/10 | KEEP |
| Post-visit causality disclaimer | Prevents treatment-efficacy inference | 9.8/10 | KEEP |

## Decision B — verified contract

- Pattern cards map `limitations[]` through a known FR/EN/AR allow-list and render only non-null patient-facing explanations.
- Change cards do the same for `missing_data[]`.
- Unknown/generic machine codes resolve to `null` and are never shown raw.
- Generic clinical-authority boilerplate stays in the safety card rather than being duplicated on every card.
- No backend logic, evidence classification, diagnosis, treatment, dose or causal semantics changed.

## Safety-notice decision

The backend `safety_notice` is currently English prose. Replacing the localized frontend card directly would regress FR/AR localization. The frontend therefore keeps its localized safety copy while the backend notice remains the semantic contract.

## Anti-regression

`frontend/test/features/companion_uncertainty_copy_contract_test.dart` locks the governed reason-code mapping, unknown-code suppression and screen integration.

## Certification evidence

Runtime PR: **#265**  
Runtime merge SHA: `6bfff96258e9c36b585f5ffaa4c7c29450012c20`

Exact-head before merge (`80ef0d168db150cb5f90a76202e738dec59fb24d`):
- CI #2523 — PASS
- Django migration drift #2335 — PASS
- UI screenshot audit #135 — PASS
- UI browser screenshot certification #98 — PASS
- Real Chrome `companion-390x844.png` inspected: unavailable state remains factual, no machine codes leak, no invented interpretation and no overflow.

Post-merge (`6bfff96258e9c36b585f5ffaa4c7c29450012c20`):
- CI #2524 — PASS
- Django migration drift #2336 — PASS
- UI screenshot audit #136 — PASS
- UI browser screenshot certification #99 — PASS
- Real Chrome `companion-390x844.png` inspected again post-merge: rendering remains clean and truthful.

## Final assessment

**9.5/10 — PASS.** Companion preserves a strong clinical-authority boundary while exposing relevant uncertainty in human language instead of opaque backend codes. Explicit review and visit anchors prevent fabricated longitudinal or causal claims, and both pre-merge and post-merge runtime certifications are green.

MENA roadmap numerator remains unchanged by this page audit.
