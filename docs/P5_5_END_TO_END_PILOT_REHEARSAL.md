# IAMINA P5-5 End-to-End Pilot Rehearsal

Status: ACTIVE — machine rehearsal certified on the retained source/tested SHA pair below; PR merge and post-merge validation remain required before P5-5 can be CLOSED. No patient data, legal/CNDP approval, production-signing proof, physical-device proof or Vercel deployment is implied.

## Goal

Prove, with one retained non-patient rehearsal packet, that IAMINA's pilot-critical flows can be exercised together without hidden resets, data loss, unsafe fallback or false capability claims.

## Success

P5-5 engineering success requires every machine-testable lane below to produce retained PASS/FAIL evidence on one exact Git source/tested SHA pair. A lane that depends on physical hardware, native listening, native linguistic review, live sensors, legal approval or production signing remains explicitly gated and is not relabelled PASS from synthetic evidence.

## Retained green proof

- source HEAD: `42cefbe4d1596274e2c7fd5e031bdbe382ee8c1f`
- GitHub tested merge SHA: `cc97c604c51b1695336841398c5d60cecbb2f115`
- P5-5 rehearsal run: `33563038752` — PASS
- retained artifact: `9822090507`
- artifact name: `p5-5-end-to-end-rehearsal-42cefbe4d1596274e2c7fd5e031bdbe382ee8c1f`
- artifact digest: `sha256:9461d41bc7039695aabba530d551f632718b6045d1b67a21be93f8df9fc19387`
- CI run: `33563038810` — PASS
- migration drift run: `33563038791` — PASS
- fixture class: `synthetic_only`
- patient data: `false`
- proof type: automated engineering

## Final machine matrix

| Lane | Status | Retained proof / boundary |
|---|---|---|
| Static analysis | PASS | `flutter analyze --no-fatal-infos` |
| Onboarding | PASS | localized onboarding + consent contracts |
| Manual data entry | PASS | synthetic glucose/context/meal/insulin/medication contracts |
| Document import / OCR | PASS | synthetic import truthfulness + local Latin OCR smoke + OCR route/shield contracts; Arabic full-document primary remains UNQUALIFIED |
| Companion | PASS | frontend truthfulness + deterministic zero-model/output guard contracts |
| CGM | PASS | synthetic/provenance gateway contracts; live physical sensor not claimed |
| Reports / export | PASS | deterministic local PDF bytes + summary truthfulness; UI share/print and Unicode PDF not claimed |
| Offline | PASS | connectivity/sync contracts plus retained emulator prerequisite run `33440140316`; physical device not claimed |
| Update | PASS | Drift N-1 to N migration contract plus retained emulator prerequisite run `33440140316`; production signing not claimed |
| Backup / restore | PASS | versioned five-table Drift round trip + transactional rollback on invalid backup |
| Degraded modes | PASS | provider/network/Companion/summary/import failures remain explicit and bounded |

Overall machine rehearsal: **PASS**.

## External / negative qualification boundaries

| Boundary | Status | Evidence |
|---|---|---|
| Physical Android device | NOT_PROVEN | P5-4 evidence is emulator-only |
| Live physical CGM sensor | NOT_PROVEN | synthetic/provenance fixtures only |
| Production signing lineage | NOT_PROVEN | P5-4 cloud rehearsal does not prove production signing |
| Arabic local full-document primary | UNQUALIFIED | retained P5-2 negative qualification remains authoritative |
| Report Unicode/Arabic PDF | NOT_QUALIFIED | export fails closed outside printable ASCII instead of corrupting content |
| Real-patient use | NOT_PROVEN | explicitly outside this synthetic rehearsal |
| Vercel deployment | NOT_PERFORMED | outside P5-5 and not authorized |

## Automatic FAIL conditions

- any patient or real identifying data enters the rehearsal;
- any lane passes only by clearing app storage, recreating the database or reinstalling from scratch when preservation is under test;
- synthetic evidence is described as real-device, live-sensor, native-human, legal or production evidence;
- OCR output bypasses the retained qualification state;
- Companion bypasses deterministic safety authority or egress controls;
- failure mode produces fabricated success, silent data loss or an unbounded retry loop;
- backup/restore is claimed without a retained restore proof.

## Existing retained prerequisite

P5-4 Android CI-only emulator upgrade rehearsal: run `33440140316`, artifact `9776292420`, digest `sha256:73c28c972fb43fd738bdbbfbc8de5628b67b3ba046f0bee95102ddf154226635`. It proves N-1 -> N package/update semantics, Drift preservation and offline reopen on an instrumented emulator only. It does not prove a physical device or production signing lineage.

## Closure rule

Machine certification is green. P5-5 remains ACTIVE until this canonical evidence commit is itself green in PR CI, PR #535 is merged, and post-merge validation on `main` is green. P5-5 closure does not close P5-1, P5-3, P5-4 physical-device evidence or P5-6 real-patient authorization.
