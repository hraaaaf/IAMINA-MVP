# Summary product audit — 2026-08-15

Status: runtime correction in progress; exact-head certification pending.

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

Branch: `agent/summary-product-audit`

- `_ActionPlan` now renders nothing when no backend action exists.
- backend actions remain discussion points only.
- arbitrary day offsets and J1/J3/J7 fallback tasks removed.
- no clinical threshold, target, dose, treatment or persisted-data semantics changed.
- anti-regression source contract added in `frontend/test/features/summary_truthfulness_contract_test.dart`.

## Certification gate

No final page score is assigned before:

1. exact-head CI/relevant gates,
2. real Chrome 390×844 artifact + manual inspection,
3. merge with expected head,
4. post-merge main recertification,
5. canonical closeout consistency.

MENA roadmap numerator is unchanged by this page audit.
