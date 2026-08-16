# Journal product audit — 2026-08-16

Status: runtime correction in progress; clinical color-threshold authority unresolved.

## Product contract

Journal is a factual history of recorded glucose measurements and their captured context. Filters and displayed units must match what the user actually selected. Historical insulin context remains backward-compatible; this page does not become a prescribing surface.

## Verified findings

- Default filter is 30 days while the header previously said `Historique complet`.
- Stored glucose is mg/dL, but the row previously rendered `bloodSugar.toStringAsFixed(0)` regardless of `unitPreference`; mmol/L users therefore saw the wrong numerical display.
- Deletion already requires explicit confirmation.
- Historical `insulinUnits` remains display-only compatibility data in Journal.
- Row coloring currently uses `val < 70 || val > 250` for red, otherwise profile target-range comparison for amber. Repository search did not establish authority for the hard-coded `250 mg/dL` red threshold. This audit does not modify it.

## Verdicts

| Surface | Verdict | Reason |
|---|---|---|
| 7 / 30 / all filter | KEEP | useful explicit history scope |
| Header subtitle | IMPROVE | must reflect active filter rather than claim full history |
| Glucose row value | IMPROVE | must respect mg/dL vs mmol/L preference |
| Context / meal details | KEEP | factual captured context |
| Historical insulin badge | KEEP | backward-compatible display only |
| Swipe delete | KEEP | explicit confirmation already present |
| Hard-coded red threshold `>250 mg/dL` | HOLD | clinical authority not established; no change without clinical gate |

## Runtime correction

Branch: `agent/journal-product-audit`

- Header subtitle now follows the selected 7-day, 30-day or all-history filter.
- mmol/L display converts stored mg/dL using `/ 18.0` and one decimal place.
- Existing clinical coloring thresholds, target ranges, treatment logic, schema and history remain unchanged.
- Anti-regression contract: `frontend/test/features/journal_truthfulness_contract_test.dart`.

## Certification gate

No final page score or CLOSED status before exact-head CI/relevant gates, real Chrome 390×844 inspection, post-merge recertification, canonical closeout, and resolution of the clinical-threshold HOLD.

MENA roadmap numerator remains unchanged by this page audit.
