# IAMINA Pilot Release Contract

Status: P5-4 engineering foundation + Firebase-off pilot decision. This document does not claim a signed pilot build exists.

## Goal

Distribute IAMINA to a founder-selected pilot cohort as signed mobile artifacts without repository access, while preserving local-first data across upgrades and retaining a safe recovery path.

## Canonical application identity

Android and iOS pilot application identifier: `ma.iamina.app`.

The identifier is treated as permanent for the first distributed pilot line. Changing it after distribution creates a different application identity and is not an update path.

Android has moved to the permanent identifier. iOS remains on the historical placeholder until Apple provisioning is available and is therefore still blocked from release-ready status.

## Release identity

`frontend/pubspec.yaml` is the source of truth for application versioning.

- `versionName` / iOS marketing version: SemVer `MAJOR.MINOR.PATCH`.
- Android `versionCode` / iOS build number: monotonically increasing positive integer.
- Every retained pilot artifact must record version, build number, Git SHA and SHA-256 digest.
- A new signed artifact requires a new build number even when the marketing version is unchanged.

## Android signing

Release builds use an external keystore configuration only.

Required ignored `frontend/android/key.properties` entries:

```text
storePassword=...
keyPassword=...
keyAlias=...
storeFile=/absolute/or/controlled/path/to/iamina-upload.jks
```

`key.properties`, JKS and keystore files are ignored by Git. Release builds must fail when the four values are absent. Debug signing is forbidden for pilot artifacts.

Recommended distribution for the pilot is a controlled internal-testing channel or a directly distributed signed APK where store enrollment is not yet available. Whichever channel is selected, updates must be signed by the same application signing identity.

## iOS signing

The final Runner bundle identifier must be `ma.iamina.app` and registered in the founder-controlled Apple Developer account before a pilot IPA/TestFlight build is accepted.

Distribution certificates, private keys and provisioning profiles remain external to Git. TestFlight is the preferred pilot update channel once the Apple account is ready.

## Firebase migration compatibility

IAMINA native Django authentication is authoritative. Firebase remains only as dormant legacy migration code.

**Pilot decision:** Firebase migration is disabled by default on both backend and Flutter. No pilot build may initialize Firebase or accept Firebase bearer credentials unless an operator explicitly opens a controlled migration window with `ENABLE_FIREBASE_MIGRATION=true` on the relevant runtime/build.

The historical `frontend/lib/firebase_options.dart` remains in the repository only for a possible legacy-account migration window. Its old `com.example.amina` metadata is not accepted as pilot identity configuration and is not initialized by default.

For the first pilot line:

1. native registration/login/password recovery are the supported identity path;
2. Android no longer applies the Google Services Gradle plugin and uses `ma.iamina.app`;
3. Firebase migration may be re-enabled only by an explicit operator decision with dedicated migration tests;
4. if a later cohort requires legacy Firebase accounts, the migration bridge must either be rebound to the permanent app identity or run through a separately controlled migration procedure before those accounts are admitted.

## Update channel

Pilot updates use signed platform artifacts, not repository pulls and not authentication as a code-update mechanism.

- Android: controlled signed internal release/APK line under the same application ID and signing identity.
- iOS: TestFlight or another Apple-supported signed pilot distribution path under the same bundle ID.
- Backend/API changes must retain a declared compatibility window for the currently supported pilot app version.
- A client that is below the minimum compatible version must receive a truthful update-required state rather than continue against an incompatible API.

## Local-first migration rule

Local Drift data is user data, not disposable cache.

Before promoting build N:

1. start from a retained N-1 fixture database containing profile, journal/log, chat, medication and reminder data where applicable;
2. install/upgrade to build N without deleting application storage;
3. execute Drift migrations;
4. verify row counts and representative values before/after;
5. verify pending sync state is not silently converted to synced or dropped;
6. verify the app can reopen offline after migration.

A migration that loses or corrupts retained local data is an automatic release failure.

## Rollback and recovery

Database downgrades are not assumed safe. Once a build performs an irreversible local schema migration, installing an older binary over that database is not an approved rollback mechanism.

Recovery hierarchy:

1. stop further rollout;
2. keep the current local database intact;
3. ship a forward-fix build with a higher build number when possible;
4. restore from an explicit verified backup/export only when the product has produced such an artifact and the user has approved the recovery flow;
5. never instruct a pilot user to clear application storage as a routine rollback procedure.

## Release evidence required for P5-4 closure

P5-4 remains open until all are retained:

- Android `ma.iamina.app` signed release artifact on a real target device;
- iOS `ma.iamina.app` signed/TestFlight-equivalent artifact on a real target device;
- exact version/build/SHA/digest for both artifacts;
- Firebase-off pilot decision proven by runtime/CI contracts;
- N-1 -> N Drift data-preservation proof;
- documented recovery/forward-fix rehearsal;
- installation/update instructions successfully followed without repository access or developer tooling.

No Vercel deployment is part of this contract.
