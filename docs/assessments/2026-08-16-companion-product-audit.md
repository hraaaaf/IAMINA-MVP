# Companion product audit — 2026-08-16

Status: SMART audit complete; uncertainty-surface corrections identified; runtime correction pending.

## Product contract

Companion is a governed, read-only interpretation layer. It may summarize repeated observations, changes since an explicit review anchor and structured after-visit facts. It must expose uncertainty and limitations, and must never infer diagnosis, treatment efficacy, dose changes or a consultation that was not explicitly recorded.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Brand/header + close | Clear full-screen identity and exit | 9.0/10 | KEEP |
| Page purpose | Explains “patterns / change / uncertainty” before interpretation | 9.5/10 | KEEP |
| Safety card | Essential clinical-authority boundary | 8.5/10 | IMPROVE — frontend hardcodes a separate notice while backend already returns canonical `safety_notice` |
| Loading state | Truthful neutral waiting state | 9.0/10 | KEEP |
| Data-unavailable state | Explicitly avoids invented interpretation and offers retry | 9.5/10 | KEEP |
| “What your data shows” | Core governed pattern surface | 9.5/10 | KEEP |
| Pattern title/state | Makes backend observation keys readable | 9.0/10 | KEEP after key-map verification |
| Evidence pill | Gives quick evidence-density signal | 8.5/10 | IMPROVE — useful but insufficient without the backend `limitations[]` |
| Recurrence count | Adds factual support and resists vague narrative | 9.5/10 | KEEP |
| Pattern limitations | Backend supplies explicit limitations | 4.0/10 current | ADD — currently discarded by the UI; show concise secondary limitations |
| “Since last review” | Useful longitudinal comparison only when an explicit review anchor exists | 9.5/10 | KEEP |
| Change cards | Shows governed change kind without treatment attribution | 9.0/10 | KEEP |
| Missing-data disclosure | Backend supplies `missing_data[]` for each change | 4.0/10 current | ADD — currently discarded by UI; show concise secondary missing-data context |
| No-review state | Correctly refuses to fabricate previous review history | 9.8/10 | KEEP |
| “After-visit continuity” | Useful continuity surface tied to an explicit recorded consultation | 9.5/10 | KEEP |
| No-recorded-visit state | Explicitly refuses to infer a consultation from activity | 9.8/10 | KEEP |
| Recorded visit facts | Shows structured follow-up count without causal claim | 9.5/10 | KEEP |
| Post-visit causality disclaimer | Prevents treatment-efficacy inference | 9.8/10 | KEEP |

## Verified backend contract

- `/api/v1/companion/overview` is read-only and does not consume proactive-attention state.
- `build_companion_overview()` composes already-governed pattern intelligence, change-since-review and explicit `AfterVisitAnchor` data.
- It performs no writes and creates no new clinical truth.
- Each pattern includes `evidence_density`, recurrence count, evidence id and `limitations`.
- Each change includes `evidence_strength` and `missing_data`.
- After-visit status is `recorded` only from an explicit stored anchor; otherwise `no_recorded_visit`.
- Backend canonical safety notice explicitly forbids diagnosis, treatment-efficacy inference, prescribing, dose advice and treatment change.

## Verified findings

- Frontend models correctly deserialize pattern `limitations` and change `missingData`, but `companion_premium_screen.dart` never renders either field.
- The screen therefore communicates evidence strength without exposing the backend-provided reason for uncertainty or missing evidence.
- Frontend also deserializes `overview.safetyNotice` but `_SafetyCard` ignores it and uses an independent hardcoded trilingual sentence.
- Empty/error states are unusually disciplined: they explicitly refuse to invent data or history.
- The after-visit section correctly states that temporal change after a consultation does not prove treatment causality.

## Recommended runtime correction

- Render non-empty pattern limitations as concise secondary disclosure under each pattern card.
- Render non-empty change `missingData` as concise secondary disclosure under each change card.
- Prefer the backend `safety_notice` as the canonical semantic contract, with localization/presentation that cannot weaken its meaning.
- Keep the current three-part hierarchy: Understand → Follow → Prepare. No section should be removed or merged.

## Certification gate

No final page score or CLOSED status before runtime correction, exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
