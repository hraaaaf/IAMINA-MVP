# IAMINA D20 — real ProfileScreen visual gate, 15 October 2026

## BEFORE (reference)
Actual `ProfileScreen` from D18-C, 2 synthetic patient-declared weights (70.00 kg UTC 11 Oct, 72.50 kg UTC 14 Oct), AppLock explicitly simulated. Capture the existing screen before any D20 code UI change with this branch's baseline SHA. Languages FR/AR; viewports **390×844 / 430×932 / 768×1024 / 1280×900**; states top/open/history. Same captures after UI implementation with identical seeds/viewports and audit fonts. Never use patient data.

## Goal and observable success
After D18 history, show an OPTIONAL local descriptive weight trend:
- 0/1 observed weight = truthful unavailable comparison, without fake change.
- 2+ valid patient-owned UTC readings = signed difference in 0.01 kg, baseline/latest patient-local dates, source patient-declared, no diagnosis or color-coded danger. Do not alter clinical targets, therapies or safety warnings.
- No notification OS permission, opt-in control or push enabled by this visual slice. Keep D20-B/C/D fail-closed.
- Logical reading order FR/AR and RTL, contrast, text accessibility at four widths. No overflow. Original ProfileScreen header and patient history remain intact.

## Text mockup / reference (not yet implemented)
```
[Historique du poids]
  ... mesures précédentes ...
  ┌ Évolution du poids · facultatif ─────────┐
  │ Entre [date A] et [date B]               │
  │ Variation descriptive : +2,50 kg         │
  │ Source : mesures saisies par le patient  │
  │ Non utilisé pour ajuster les traitements │
  └──────────────────────────────────────────┘
```
For insufficient rows: `Pas assez de pesées pour comparer.` Label `Évolution` must not imply medical progression or weight goal.

## Proof ledger
- BEFORE exact SHA: PENDING first workflow run / PNG list.
- AFTER exact SHA: PENDING new UI implementation and workflow.
- Pixel diff & visual score: NOT YET VERIFIED. Do not claim validation or a score before inspecting both.
- D20 parent D18 unmerged; no Vercel and no patient release. P5 historical 6/12 = 50% unchanged.

## Next
Capture BEFORE and inspect artifact -> implement widget without changing historical data paths -> run AFTER at same viewports -> compare raster, a11y and Flutter tests -> fix until stable -> record visual proof and reviewer status.
