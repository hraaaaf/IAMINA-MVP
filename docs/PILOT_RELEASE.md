# IAMINA Pilot Release Contract

Status: P5-4 **PWA-first** engineering contract. This document does not authorize real-patient use, a production deployment, or native Android/iOS release readiness.

Canonical product direction: `docs/P5_PWA_FIRST_RELEASE_STRATEGY.md`.

## Goal

Distribute the immediate IAMINA pilot through an installable, traceable PWA without repository or developer access, while preserving local-first data across updates and retaining a safe forward-recovery path. Native Android/iOS packaging is a deferred alignment lane and must not block the PWA pilot solely because native signing is incomplete.

## P5-4 split

### P5-4A — PWA pilot packaging — current critical path

The PWA candidate must provide retained evidence for:

1. reproducible web build from one exact Git SHA;
2. stable IAMINA PWA identity and application version;
3. browser installability without repository/developer access;
4. persistent local Drift storage, never silently accepted as in-memory;
5. local-data preservation across navigation, reload and supported PWA updates;
6. offline app-shell behavior on supported target browsers;
7. deterministic cache/update behavior and safe forward recovery;
8. no development secret, repository access or patient/API response stored in the app-shell cache;
9. exact-SHA retained build/install/update evidence.

P5-4A may close independently of native signing. P5-6 remains mandatory before any real-patient release.

### P5-4B — Native Android/iOS alignment — deferred

Native application identity remains `ma.iamina.app`.

Future native release gates retain:

- founder-controlled permanent Android signing identity;
- signed Android artifact and retained hash/signature evidence;
- Apple Developer registration/signing/provisioning;
- signed iOS/TestFlight-equivalent artifact;
- real-device clean-install and N-1 -> N update evidence on Android/iOS;
- native recovery/rollback evidence;
- native installation without repository/developer tooling.

These are mandatory before any native Android/iOS pilot or public native distribution claim, but are not P5-4A blockers.

## Release identity

`frontend/pubspec.yaml` remains the source of truth for application versioning.

- application version: stable SemVer `MAJOR.MINOR.PATCH`;
- build number: monotonically increasing positive integer;
- every retained pilot candidate must record version, build number and exact Git SHA;
- retained packaged artifacts/evidence must record a digest where an artifact exists;
- a promoted candidate must be reproducible from its recorded source SHA.

PWA identity is additionally frozen by `frontend/web/manifest.json` and the canonical IAMINA web metadata.

## PWA build and install contract

The pilot web bundle must be self-contained for the supported offline surface. The canonical build must not depend on a remote Flutter engine/CDN for app-shell startup.

Required floors:

- `flutter build web --release --no-web-resources-cdn` succeeds;
- manifest identity remains IAMINA with stable relative app ID/start URL;
- browser installability checks contain no blocking manifest/installability errors;
- required Drift WASM/worker assets are present in the built bundle;
- installation requires only the controlled pilot URL/browser flow, not Git, source code or developer tooling.

A successful compile alone is not install/update evidence; retained browser evidence is required.

## PWA local-first persistence rule

Local Drift data is user data, not disposable cache.

Before promoting candidate N:

1. start from a retained N-1 or representative synthetic local database state;
2. update/reload without clearing origin/application storage;
3. execute Drift migrations where the schema changes;
4. verify row counts and representative values before/after;
5. verify pending sync state is not silently converted to synced or dropped;
6. verify the storage implementation is persistent on the target browser, not in-memory fallback;
7. verify the app can reopen with retained local data after the supported update flow.

A migration or update that loses/corrupts retained local data is an automatic release failure.

## Offline app-shell and cache boundary

Offline app-shell caching is strictly separate from patient/backend data.

The service worker may cache only explicitly approved same-origin static application resources required to start the PWA offline. It must not app-shell-cache:

- `/api/` responses;
- authenticated/patient backend responses;
- mutating requests;
- arbitrary third-party resources.

Offline qualification requires real-browser proof with normal HTTP cache disabled and network forced offline. A hard reload must still start the app and reopen the retained synthetic local fixture.

Service-worker/cache changes must be versioned so a later app-shell can replace the previous cache deterministically. Old IAMINA app-shell caches must not accumulate indefinitely.

## PWA update and compatibility contract

The public `/api/v1/app-compatibility` contract remains authoritative for backend compatibility decisions.

- clients below the minimum supported version/build receive truthful `update_required`;
- supported older clients may receive non-blocking `update_available`;
- missing version metadata is `version_unknown`, never falsely compatible;
- invalid server compatibility configuration fails closed.

PWA update qualification additionally requires a same-origin N -> N+1 browser rehearsal showing:

1. old app-shell/cache active on N;
2. new candidate becomes active without clearing origin storage;
3. retained Drift data remains intact;
4. obsolete IAMINA app-shell cache is removed/replaced deterministically;
5. offline reopen still succeeds after the update;
6. failed rollout recovery uses a forward fix, not routine storage clearing.

## Recovery / forward-fix rule

Database downgrades are not assumed safe. Once a candidate performs an irreversible local schema migration, serving an older application over that database is not an approved recovery mechanism.

Recovery hierarchy:

1. stop further rollout;
2. keep local browser/origin storage intact;
3. restore service only with a compatible cached shell when that shell remains safe;
4. otherwise ship a forward-fix candidate with a higher build number/cache schema as appropriate;
5. use verified backup/export recovery only when such an artifact exists and the user-approved recovery flow applies;
6. never instruct pilot users to clear browser/site/application storage as routine rollback.

## Firebase migration compatibility

IAMINA native Django authentication is authoritative. Firebase remains dormant legacy migration code.

Firebase migration is disabled by default on backend and Flutter. No PWA/native pilot candidate may initialize or accept the legacy Firebase path unless an operator explicitly opens a controlled migration window with dedicated evidence.

## Native signing contract — deferred P5-4B

### Android

Release builds use external signing material only. `key.properties`, JKS and keystore files stay outside Git. Debug signing is forbidden for a claimed native pilot artifact.

### iOS

The final Runner bundle identifier remains `ma.iamina.app`. Apple signing/provisioning remains external and is required before any native iOS/TestFlight readiness claim.

## Current retained P5-4A evidence boundary

As of 2026-09-11:

- PWA packaging foundation is merged via #557 with exact-head and exact-main CI green;
- real Chrome installability + persistent Drift storage evidence is merged via #558;
- retained Chrome evidence selected `sharedIndexedDb`, returned zero installability errors, and preserved the synthetic fixture across navigation and hard reload;
- true offline app-shell proof remains an active gate under #559 until its strict offline AFTER evidence is green;
- PWA update/cache-rollover rehearsal remains required after offline qualification.

No real-patient, CNDP/legal, Vercel, Android signing or iOS signing claim follows from this evidence.

## P5-4A closure evidence

P5-4A may close only when all are retained:

- exact-SHA reproducible self-contained PWA build;
- browser installability proof;
- persistent Drift browser storage proof;
- N-1 -> N local data-preservation evidence;
- true offline hard-reload app-shell proof;
- same-origin PWA update/cache-rollover rehearsal;
- documented and rehearsed forward-recovery behavior;
- pilot installation/update instructions that require no repository/developer tooling;
- explicit boundary that P5-6 is still required before real-patient use.

P5-4B stays deferred and open for native Android/iOS alignment.

No Vercel deployment is authorized by this contract.
