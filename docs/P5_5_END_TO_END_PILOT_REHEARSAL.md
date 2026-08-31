# IAMINA P5-5 End-to-End Pilot Rehearsal

Status: ACTIVE — engineering rehearsal only. No patient data, legal/CNDP approval, production-signing proof, physical-device proof or Vercel deployment is implied.

## Goal

Prove, with one retained non-patient rehearsal packet, that IAMINA's pilot-critical flows can be exercised together without hidden resets, data loss, unsafe fallback or false capability claims.

## Success

P5-5 engineering success requires every machine-testable lane below to produce retained PASS/FAIL evidence on one exact Git SHA. A lane that depends on physical hardware, native listening, native linguistic review, live sensors, legal approval or production signing must remain explicitly gated and must not be relabelled PASS from synthetic evidence.

## Proof

Retain exact SHA, workflow/run identifiers, fixture identifiers, commands/tests executed, PASS/FAIL per lane, and any negative qualification result.

## Rehearsal lanes

| Lane | Required engineering proof | Current boundary |
|---|---|---|
| Onboarding | deterministic non-patient onboarding path reaches usable app state | machine-testable |
| Manual data entry | representative glucose/context/meal/medication/reminder data persists | machine-testable |
| Document import / OCR | bounded fixture import executes and qualification state is respected | Arabic full-document primary remains UNQUALIFIED |
| Companion | deterministic safety/zero-model/LLM routing contracts remain enforced | machine-testable; no real-patient claim |
| CGM | gateway accepts retained synthetic/provenance fixtures and preserves source truth | live physical sensor remains external |
| Reports | retained local data produces expected report/export semantics | machine-testable where existing contracts exist |
| Offline | app reopens with retained local data while app UID network egress is blocked | Android emulator proof already exists; physical device remains external |
| Update | N-1 -> N install preserves package identity and Drift fixture | Android emulator proof already exists; production signing/physical device external |
| Backup / restore | export/backup fixture can be restored without silent loss or storage reset | must be proven or explicitly FAIL/NOT IMPLEMENTED |
| Degraded modes | provider/network/OCR/CGM failures remain bounded, truthful and non-destructive | machine-testable where failure injection exists |

## Automatic FAIL conditions

- any patient or real identifying data enters the rehearsal;
- any lane passes only by clearing app storage, recreating the database or reinstalling from scratch when preservation is under test;
- synthetic evidence is described as real-device, live-sensor, native-human, legal or production evidence;
- OCR output bypasses the retained qualification state;
- Companion bypasses deterministic safety authority or egress controls;
- failure mode produces fabricated success, silent data loss or an unbounded retry loop;
- backup/restore is claimed without a retained restore proof.

## Existing retained evidence allowed as prerequisites

- P5-4 Android CI-only emulator upgrade rehearsal: run `33440140316`, artifact `9776292420`, digest `sha256:73c28c972fb43fd738bdbbfbc8de5628b67b3ba046f0bee95102ddf154226635`.
- The Android rehearsal proves N-1 -> N package/update semantics, Drift preservation and offline reopen on an instrumented emulator only. It does not prove a physical device or production signing lineage.
- P5-2 Arabic real-camera OCR qualification remains negative for local full-document Arabic primary and must be honored by P5-5.

## Execution order

1. inventory exact existing tests/scripts for each lane;
2. mark every lane `COVERED`, `PARTIAL`, `MISSING` or `EXTERNAL_GATE` with file/test references;
3. add the smallest missing deterministic fixtures/tests;
4. create one P5-5 rehearsal runner that executes only retained non-patient evidence;
5. run on one exact SHA and retain evidence artifact;
6. fix any FAIL without weakening the contract;
7. update this file with the final matrix and evidence references;
8. PR -> CI -> merge -> post-merge.

## Closure rule

P5-5 closes only when every machine-testable lane is PASS and every non-machine lane is explicitly recorded as an external gate. P5-5 closure does not close P5-1, P5-3, P5-4 physical-device evidence or P5-6 real-patient authorization.
