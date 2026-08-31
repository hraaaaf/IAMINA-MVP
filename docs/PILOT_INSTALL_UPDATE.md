# IAMINA Pilot Install & Update Protocol

Status: P5-4 preflight contract. A signed Android build artifact now exists, and a CI-only Android emulator N-1 → N upgrade rehearsal has passed. This document does **not** claim that the retained production-signed Android artifact or any iOS pilot artifact has been installed/upgraded on a real physical device.

## Goal

A pilot user must be able to install and update IAMINA from a signed platform artifact without GitHub access, repository access, a terminal, Flutter, Android Studio or Xcode, while preserving local-first data.

## Hard floors

- application identifier is `ma.iamina.app` on Android and iOS;
- only signed pilot artifacts may be distributed;
- private signing keys, certificates and provisioning secrets never appear in this guide or in Git;
- updates keep the same application identity/signing lineage;
- local app storage is not cleared as a routine update or rollback step;
- every distributed artifact is linked to an exact version, build, Git SHA and SHA-256 digest in the retained release ledger;
- a failed migration or update stops rollout and preserves the existing local database.

## Android pilot path

The retained release record must name the actual selected channel. Accepted pilot paths are:

1. a controlled Android internal-testing channel; or
2. direct distribution of the signed pilot APK through a founder-controlled channel.

User-facing installation steps must contain only what the recipient needs to install the signed artifact. They must not require cloning the repository or running developer commands.

Before first install, verify:

- package identity: `ma.iamina.app`;
- release version/build matches the ledger;
- downloaded file SHA-256 matches the ledger when direct APK distribution is used.

For an update, install the newer signed artifact over the existing application. Do **not** uninstall the previous version first. After update, verify the displayed/current build identity and retained local data before continuing the pilot.

### Current Android engineering evidence

The retained ledger contains two distinct evidence classes that must not be conflated:

- permanent signed Android build evidence tied to the production signing lineage;
- CI-only Android emulator upgrade rehearsal evidence using an ephemeral non-production signer.

The cloud rehearsal passed the N-1 → N in-place update, package identity preservation, Drift fixture preservation and offline reopen checks on Android API 35. It proves engineering semantics, but it does **not** prove that the exact retained production-signed APK chain works on a real physical handset.

## iOS pilot path

Preferred pilot distribution is TestFlight or another Apple-supported signed distribution path under `ma.iamina.app`.

The retained release record must identify the Apple-supported channel, version/build and signing/provisioning reference without storing private material.

An update must install over the existing application identity. Deleting the app before updating is not an approved migration test because it can remove local-first data.

## N-1 → N upgrade evidence

Before promoting build N on each platform:

1. install retained build N-1;
2. create the non-patient fixture state required by the release test plan;
3. record representative row counts/values and pending-sync state;
4. install build N over N-1 without clearing storage;
5. reopen IAMINA offline;
6. verify Drift migration completion and the same retained fixture evidence;
7. verify the compatibility endpoint does not falsely mark the installed supported client incompatible;
8. record PASS/FAIL in the release ledger.

Any missing/corrupted retained local data is an automatic FAIL.

The CI-only Android emulator rehearsal satisfies the engineering portion of steps 1-6 for its instrumented ephemeral-signing harness. It does not satisfy the real-device, production-signing, compatibility-endpoint or human-usability evidence needed to close P5-4.

## Failed update / recovery

If installation, startup or migration fails:

1. stop further rollout;
2. preserve the current application data and database;
3. record exact app version/build, device/OS and failure evidence;
4. prefer a higher-build forward fix;
5. use an explicit verified backup/export only when such an artifact exists and the recovery procedure has been tested;
6. do not instruct a pilot user to clear application storage as routine recovery.

## Human usability proof required for P5-4

P5-4 remains **OPEN**. Retain evidence that a person who did not use the repository followed the final platform instructions and successfully:

- installed IAMINA on a clean target device;
- upgraded N-1 → N on an existing-data target device using the real retained signing lineage/channel;
- reopened the app with retained local data;
- identified the installed version/build;
- verified compatibility behavior for the supported installed client;
- completed the documented recovery/forward-fix rehearsal where applicable.

The corresponding artifact/device evidence belongs in `docs/PILOT_ARTIFACT_LEDGER.md` or a release-specific retained copy derived from that template.
