# Summary product audit — 2026-08-15

Status: runtime merged; post-merge main recertification pending.

## Product contract

Summary is an observational diabetes summary, not a treatment planner. It may present measured KPIs, evidence-bounded observations and clinician discussion points. It must not turn non-prescriptive backend copy into a dated treatment/action schedule.

## Verified findings

- `AISummaryScreen` loads Summary + KPI data for 7/21/90 days.
- KPI/AGP rendering is conditional on sufficient data and exposes coverage/reference copy.
- backend `InsightCard.action` is constrained as a non-prescriptive discussion/recommendation field.
- previous frontend `_ActionPlan` assigned arbitrary J1/J2/J3/J5/J6/J7 dates to backend actions.
- previous frontend also fabricated three fallback tasks when no backend action existed.

## Verdicts

| Surface | Verdict | Reason |
|---|---|---|
| Period selector 7/21/90 | KEEP | explicit observational window |
| KPI cards / coverage | KEEP | useful with sufficiency disclosure |
| AGP + TIR/TAR/TBR | KEEP | observational analytics; clinical references unchanged |
| Insight cards | KEEP / IMPROVE | preserve evidence-bounded observation semantics |
| Backend `action` | KEEP | non-prescriptive clinician-discussion content |
| Dated 7-day action plan | REMOVE | frontend-added authority not present in backend contract |
| Fabricated fallback tasks | REMOVE | violates truthfulness / provenance |
| Discussion points | IMPROVE | render only when supplied by backend, without invented dates |

## Runtime correction

Runtime PR: #250
Runtime merge SHA: `1db7facb8c8cd8696b88cd0a6003c51219abbc7e`
Exact-head certified SHA: `3a20e293b6832b8c9ce5bd84a942631c947e95c8`

- `_ActionPlan` now renders nothing when no backend action exists.
- backend actions remain discussion points only.
- arbitrary day offsets and J1/J3/J7 fallback tasks removed.
- no clinical threshold, target, dose, treatment or persisted-data semantics changed.
- anti-regression source contract added in `frontend/test/features/summary_truthfulness_contract_test.dart`.

## Exact-head certification

- CI #2438: PASS.
- Django migration drift #2250: PASS.
- UI screenshot audit #71: PASS.
- Chrome certification #30: PASS on attempt 2 after an infrastructure-only attempt-1 failure.
- Chrome artifact: `9254367640`, digest `sha256:5c16da870023d3b170a313b67df51e5d0a7049651f0666943cd0ce83360918b2`.
- Manual inspection of `summary-390x844.png`: clean first-use state, no collision/overflow, readable CTA hierarchy.
- The Chrome harness does not mock Summary backend data, so the no-fabrication behavior is certified by the exact-head source contract rather than inferred from a synthetic rendered state.

## Remaining closeout gate

No final page score or CLOSED status is assigned before post-merge `main` recertification is green and canonical consistency is confirmed.

MENA roadmap numerator is unchanged by this page audit.
