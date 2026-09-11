# P5-5 — End-to-End Pilot Rehearsal Closeout

**Status:** CLOSED — engineering rehearsal only, with explicit boundaries  
**Date:** 2026-09-11  
**Merged implementation:** PR #552  
**Main SHA under post-merge proof:** `88b78e036ce3494dfe37921e70e064fbfdabd6bb`

## Goal

Retain one synthetic, non-patient end-to-end rehearsal on current `main` across the pilot-critical machine-executable lanes, without converting external or human/device gates into false PASS claims.

## Success criterion

The exact merged `main` SHA must pass both canonical CI and the P5-5 rehearsal, and the retained artifact must identify its evidence class, source SHA, lane outcomes and qualification boundaries.

## Proof

- PR #552 merged to `main` as `88b78e036ce3494dfe37921e70e064fbfdabd6bb`.
- Post-merge CI run #34573137452: `success`, exact head SHA `88b78e036ce3494dfe37921e70e064fbfdabd6bb`.
- Post-merge P5-5 run #34573137446: `success`, exact head SHA `88b78e036ce3494dfe37921e70e064fbfdabd6bb`.
- Retained artifact #10188573954, `p5-5-end-to-end-pilot-rehearsal`.
- Artifact digest: `sha256:4e2b923ea948d99702bac4b37d65e9d9f1f471ca0bfdb1022bab2a9deb317139`.
- Artifact declares `EVIDENCE_CLASS=synthetic-non-patient`, `REAL_PATIENT_EVIDENCE=false`, `SOURCE_SHA=88b78e036ce3494dfe37921e70e064fbfdabd6bb`, `EVENT=push`.
- Machine lanes PASS: onboarding, data/import, Companion, CGM, reports/PDF, offline/sync, backup/restore, degraded modes.
- Final retained result: `P5_5_RESULT=PASS_WITH_BOUNDARIES`.

## Boundaries retained

- Arabic local full-document OCR primary: `QUALIFIED_NEGATIVE`; P5-2 real-camera evidence remains authoritative and does not qualify it as primary.
- Physical update/install: `EXTERNAL`; P5-4 signed-artifact and real-device upgrade evidence remain separate gates.
- Physical Android device: `EXTERNAL`.
- Live physical CGM sensor: `EXTERNAL`.
- Production signing/distribution: `EXTERNAL`.
- No real-patient evidence, CNDP/legal/regulatory approval, clinical-human approval or production distribution is claimed.
- No Vercel deployment was performed.

## Conclusion

P5-5 is CLOSED at its stated engineering evidence boundary. This raises Pilot Readiness from 2/9 to 3/9 = 33.3%. It does not close P5-1, P5-3, P5-4 or authorize P5-6 real-patient release.
