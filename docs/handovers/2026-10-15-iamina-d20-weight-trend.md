# IAMINA — D20-A descriptive weight trend, 15 October 2026

## Goal / accepted scope
Implement a read-only, provenance-preserving, optional weight history comparison as the technical precursor to Decision #20 under V1-08. Approved source: Notion register #20 (8 Oct 2026), **optional user-configured notifications** only if history sufficient, not per-entry, no medical conclusion or diagnosis; separate from reminders.

## Dependencies
D18 #18 local weight history lives in **unmerged** PRs #1060 (Django), #1064 (local vault) and #1066 (Flutter/profile). D20 is branched from exact D18-C HEAD `c25784b136641d3f58e8b659cc5e4f27008b59a3` and MUST NOT independently merge to main before approved D18 lineage. Parent D19 #920 remains clinically unapproved despite D19 technical CI and protected preview; D20 cannot inherit D19 medical signoff.

## Candidate D20-A boundaries
- Pure in-process Dart local fixed-point comparison (kg hundredths) of first and latest patient-declared weight observations within the **same** patient, sorted UTC. Source UUIDs and timestamps preserved.
- No result for zero/one measurement, ambiguous dates, any future or non-UTC row, mixed patients, duplicate evidence IDs, corrupted source/unit normalization or unknown provenance.
- **NO** notification creation, scheduler, push, user preference change, biomedical threshold, diagnosis, alerts, BMI, provider/LLM calls, data upload or UI. This intentionally cannot satisfy full D20 alone.
- Negative synthetic Dart oracles: missingness, patient-vault isolation, duplicate timestamp, corrupted kg/lb normalization, evidence and signed delta.

## Success and proof
Actual Dart tests on the exact candidate branch must pass; code inspection must establish no notification/LLM/egress; only after D18 qualified consent/privacy gate will D20-B implement opt-in criteria (explicit configurable minimum change/time window, throttle/dedup), persist preferences in owned vault, verify notification-vs-reminder semantics and localized, real UI with BEFORE/AFTER. No medical danger threshold is supplied by D20.

**Status**: CANDIDATE / TESTS NOT YET EXECUTED. D19 preview ID dpl_4n1M1pTioPgRNZvNyWPEDosfHJE2 READY at `cb540617`, still NO patient release. P5 historical 6/12 = 50% unchanged.

## Next exact
Run Flutter targeted tests in connected CI or local authorized Flutter runtime for D20-A, confirm new branch exact HEAD. Then D20-B consent prefs + source-to-trigger proof and visual comparison. If no runtime, mark technical gate pending and keep PR draft, do not fabricate test evidence.
