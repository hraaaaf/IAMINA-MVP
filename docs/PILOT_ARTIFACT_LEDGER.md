# IAMINA Pilot Artifact Ledger

Status: P5-4 evidence template. Empty/unfilled rows are **not** release evidence.

## Purpose

Retain a minimal non-secret chain from a distributed pilot artifact to its source revision, signing lineage, target device and upgrade result.

## One record per retained artifact/device proof

| Field | Required evidence |
|---|---|
| Platform | `android` or `ios` |
| Application ID | `ma.iamina.app` |
| Version | Stable `MAJOR.MINOR.PATCH` |
| Build | Monotonically increasing positive integer |
| Git SHA | Exact 40-character source commit |
| Artifact filename / distribution build ID | Exact retained identifier |
| SHA-256 | 64-hex digest of the distributed artifact where a downloadable artifact is available |
| Signing reference | Non-secret certificate/key alias or platform signing reference sufficient to prove lineage; never private material |
| Distribution channel | Controlled Android internal/direct signed APK, TestFlight, or other approved signed pilot channel |
| Device | Manufacturer/model or Apple model class used for proof |
| OS | Exact Android/iOS version |
| Install mode | Clean install or N-1 → N update |
| Previous version/build | Required for update proof |
| Local-data fixture | Non-patient fixture identifier/version |
| Migration/data-preservation result | PASS/FAIL + retained evidence reference |
| Offline reopen result | PASS/FAIL |
| Compatibility-contract result | Status returned for this client build |
| Recovery rehearsal | PASS/FAIL/not-applicable + evidence reference |
| Tester/reviewer | Human reviewer identity/reference appropriate to the project record |
| Timestamp | UTC timestamp |
| Notes | Non-secret anomalies or limitations |

## Hard validation rules

A release record is incomplete if any applicable required field is missing.

Automatic rejection conditions:

- application ID differs from `ma.iamina.app`;
- release artifact is unsigned or signing lineage is not traceable;
- version/build cannot be tied to an exact Git SHA;
- downloadable artifact digest is missing or mismatched;
- N-1 → N evidence required an uninstall or storage clear;
- retained local data is missing/corrupted after update;
- a failed migration was hidden by resetting local storage;
- the installation path required repository access or developer tooling for the pilot user.

## Retained build evidence — not yet promoted to device proof

### Android 0.1.0+1 — signed build evidence

```text
Release: 0.1.0+1
Platform: android
Application ID: ma.iamina.app
Git SHA: 13b2159d14a211516262cfa96872dc9a722a6743
Artifact / build ID: GitHub Actions artifact 9718955721 / iamina-android-13b2159d14a2
APK SHA-256: ab1b91742c41a4880c01ac0f5cf84582c337e7ffa56096d2e683e66712073cca
Signing reference: certificate SHA-256 8f33268da08fe895951945b2d70e841f13c6552235f0e10d9d0e4f883cf2a7ce
Signature scheme: APK Signature Scheme v2
Signing-lineage source: encrypted JKS artifact 9718544880; exact lineage restored and verified; no regeneration in successful run
Build workflow: hraaaaf/-IAMINA-RELEASE run 33266734607 — success
Build repository visibility during run: public, then verified private after completion
Device / OS: NOT YET PROVEN
Install mode: NOT YET PROVEN
Previous version/build: N/A until N-1 -> N rehearsal
Local-data fixture: NOT YET PROVEN ON DEVICE
Migration/data preservation: NOT YET PROVEN ON DEVICE
Offline reopen: NOT YET PROVEN
Compatibility contract: NOT YET PROVEN ON DEVICE
Recovery rehearsal: NOT YET PROVEN
Tester/reviewer: NOT YET PROVEN
Timestamp UTC: 2026-08-29T17:59:33Z artifact upload completion evidence
Notes: Signed artifact exists and is cryptographically traceable, but this is build evidence only. It is not yet a complete pilot release/device record and does not authorize distribution to patients.
```

## Retained release records

Do not pre-fill this section before real device evidence exists. Add one dated subsection per promoted pilot build only after device/install/update evidence is collected.

### Template

```text
Release: <version+build>
Platform: <android|ios>
Application ID: ma.iamina.app
Git SHA: <40 hex>
Artifact / build ID: <identifier>
SHA-256: <64 hex or N/A only when the platform channel does not expose a downloadable artifact>
Signing reference: <non-secret reference>
Distribution channel: <channel>
Device / OS: <device> / <OS>
Install mode: <clean|N-1 -> N>
Previous version/build: <value or N/A>
Local-data fixture: <non-patient fixture>
Migration/data preservation: <PASS|FAIL> — <evidence>
Offline reopen: <PASS|FAIL>
Compatibility contract: <status>
Recovery rehearsal: <PASS|FAIL|N/A> — <evidence>
Tester/reviewer: <reference>
Timestamp UTC: <timestamp>
Notes: <limitations/anomalies>
```

No row in this ledger constitutes CNDP, legal, clinical or real-patient authorization.
