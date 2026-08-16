# Companion product audit — 2026-08-16

Status: SMART audit complete; localized uncertainty mapping implemented; screen integration and certification pending.

## Product contract

Companion is a governed, read-only interpretation layer. It may summarize repeated observations, changes since an explicit review anchor and structured after-visit facts. It must expose useful uncertainty without leaking machine codes, and must never infer diagnosis, treatment efficacy, dose changes or a consultation that was not explicitly recorded.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Brand/header + close | Clear full-screen identity and exit | 9.0/10 | KEEP |
| Page purpose | Explains patterns / change / uncertainty before interpretation | 9.5/10 | KEEP |
| Safety card | Essential clinical-authority boundary | 9.0/10 | KEEP localized frontend notice; backend `safety_notice` is semantic evidence but cannot directly replace localized FR/AR copy while returned as English prose |
| Loading state | Truthful neutral waiting state | 9.0/10 | KEEP |
| Data-unavailable state | Explicitly avoids invented interpretation and offers retry | 9.5/10 | KEEP |
| “What your data shows” | Core governed pattern surface | 9.5/10 | KEEP |
| Pattern title/state | Makes backend observation keys readable | 9.0/10 | KEEP |
| Evidence pill | Quick repeatability signal | 8.5/10 | KEEP with uncertainty disclosure; evidence density is not probability or clinical confidence |
| Recurrence count | Factual support against vague narrative | 9.5/10 | KEEP |
| Pattern limitations | Backend supplies machine-coded limitations | 4.0/10 current | ADD only context-specific, patient-useful localized limitations; do not repeat generic boilerplate on every card |
| “Since last review” | Longitudinal comparison only from explicit review anchor | 9.5/10 | KEEP |
| Change cards | Governed change kind without treatment attribution | 9.0/10 | KEEP |
| Missing-data disclosure | Backend supplies machine-coded `missing_data[]` | 4.0/10 current | ADD localized “why uncertain” disclosure for known reason codes |
| No-review state | Refuses fabricated review history | 9.8/10 | KEEP |
| “After-visit continuity” | Tied to an explicit recorded consultation | 9.5/10 | KEEP |
| No-recorded-visit state | Refuses to infer consultation from activity | 9.8/10 | KEEP |
| Recorded visit facts | Structured follow-up count without causal claim | 9.5/10 | KEEP |
| Post-visit causality disclaimer | Prevents treatment-efficacy inference | 9.8/10 | KEEP |

## Verified backend contract

- `/api/v1/companion/overview` is read-only and creates no new clinical truth.
- Patterns contain evidence density, recurrence and `limitations[]`.
- Pattern limitations are machine codes such as `observational_association_only` and context-specific codes such as `improving_descriptively_does_not_mean_treatment_response_or_outcome`.
- Changes contain evidence strength and `missing_data[]`; missing-data reasons are machine codes such as `no_eligible_post_review_evidence` and `resolution_after_review_not_provable`.
- Review history is based on a server-captured explicit Companion review anchor, never inferred from app activity.
- After-visit status is based on an explicit stored anchor.
- Backend safety semantics forbid diagnosis, causality, treatment-response inference, prescribing, dose advice and treatment change.

## Runtime strategy

Implemented helper:
`frontend/lib/features/companion/companion_uncertainty_copy.dart`

- maps known context-specific pattern limitations to concise FR/EN/AR patient-facing explanations;
- maps known change missing-data reasons to concise FR/EN/AR explanations;
- unknown or generic boilerplate codes resolve to `null` rather than leaking raw backend tokens;
- no backend logic, evidence classification or clinical meaning changes.

Screen integration still required:
- Pattern cards should display only non-null context-specific limitation labels.
- Change cards should display non-null missing-data labels under the descriptive change copy.
- Generic clinical-authority boundaries remain in the safety card instead of being duplicated on every pattern.

## Safety-notice decision

The backend `safety_notice` is currently English prose. Replacing the existing localized safety card directly would regress FR/AR localization. Therefore the frontend keeps its localized safety copy for presentation while the backend notice remains the semantic contract to test against. A future structured/localized backend safety code could become the single presentation source.

## Anti-regression

`frontend/test/features/companion_uncertainty_copy_contract_test.dart` locks the governed reason-code mapping and the rule that unknown codes are not rendered raw.

## Certification gate

No final page score or CLOSED status before screen integration, exact-head gates, real Chrome 390×844 inspection, runtime merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
