# IAMINA Pilot Release Contract

Status: P5-4 **PWA-first** engineering contract. P5-4A engineering is `CLOSED_WITH_BOUNDARIES`; P5-4B native alignment remains deferred. This document does not authorize real-patient use, a production deployment, or native Android/iOS release readiness.

Canonical product direction: `docs/P5_PWA_FIRST_RELEASE_STRATEGY.md`.
Canonical PWA runbook: `docs/P5_PWA_PILOT_RUNBOOK.md`.
Canonical P5-4A closeout: `docs/assessments/2026-09-11-p5-4a-pwa-pilot-packaging-closeout.md`.

## Goal

Distribute the immediate IAMINA pilot through an installable, traceable PWA without repository or developer access, while preserving local-first data across updates and retaining a safe forward-recovery path. Native Android/iOS packaging is a deferred alignment lane and must not block the PWA pilot solely because native signing is incomplete.

## P5-4 split

### P5-4A — PWA pilot packaging — engineering closed with boundaries

Retained engineering evidence covers:

1. reproducible web build from exact Git SHA;
2. stable IAMINA PWA identity and application version;
3. browser installability without repository/developer access;
4. persistent local Drift storage, never silently accepted as in-memory;
5. local-data preservation across navigation, reload, offline reopen and supported PWA updates;
6. true offline app-shell behavior;
7. deterministic release discovery, cache rollover, failed-candidate preservation and forward recovery;
8. no development secret, repository access or patient/API response stored in the app-shell cache;
9. retained exact-SHA build/install/update evidence;
10. pilot install/update/recovery instructions requiring no repository/developer tooling.

P5-6 remains mandatory before any real-patient release. A controlled pilot URL and physical target-browser/device installation remain external evidence and are not implied by engineering closure.

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

Service-worker/cache changes are release-versioned so a later app-shell can replace the previous cache deterministically. Obsolete IAMINA app-shell caches are removed only after healthy new activation.

## PWA update and compatibility contract

The public `/api/v1/app-compatibility` contract remains authoritative for backend compatibility decisions.

- clients below the minimum supported version/build receive truthful `update_required`;
- supported older clients may receive non-blocking `update_available`;
- missing version metadata is `version_unknown`, never falsely compatible;
- invalid server compatibility configuration fails closed.

PWA update qualification additionally requires the certified same-origin model:

1. the currently active release keeps serving its release-coherent cache-first shell;
2. after page load, the bootstrap performs a network-only `no-store` probe of `iamina_service_worker.js` and extracts canonical `IAMINA_CACHE_SCHEMA`;
3. the bootstrap registers `iamina_service_worker.js?release=<schema>` with `updateViaCache: 'none'`, so a canonical release change changes the script URL and starts browser update discovery even when the old cached bootstrap is running;
4. explicit `registration.update()` remains a non-blocking same-release fallback and is not the release-promotion mechanism;
5. each candidate installs into a separate release cache;
6. every precached shell resource is fetched with `cache: 'reload'` before storage, preventing stale HTTP-cache bytes from contaminating the new release cache;
7. no production `skipWaiting()` forces a mid-session takeover;
8. a healthy candidate may remain `waiting` while the old controlled client is open and activate naturally after close/reopen;
9. retained Drift data remains intact and origin storage is never cleared;
10. after healthy activation, obsolete IAMINA app-shell caches are purged;
11. offline reopen succeeds from the activated new release;
12. a rejected candidate must preserve the last-known-good shell and local data.

## Recovery / forward-fix rule

Database downgrades are not assumed safe. Once a candidate performs an irreversible local schema migration, serving an older application over that database is not an approved recovery mechanism.

Recovery hierarchy:

1. stop further rollout;
2. keep local browser/origin storage intact;
3. retain the last-known-good cached shell when the rejected candidate never becomes active;
4. prepare a compatible forward-fix candidate with a higher canonical version/build;
5. let a later normal startup discover that higher release through the production network-only service-worker probe and release-versioned registration URL;
6. do not force or certify an immediate second same-profile update seconds after a rejected worker install because Chrome post-failure scheduling is browser-controlled;
7. verify the forward-fix release cache contains the new release bytes themselves;
8. let the healthy worker activate across a normal close/reopen boundary;
9. verify Drift persistence, offline reopen and obsolete-cache purge;
10. use verified backup/export recovery only when such an artifact exists and the user-approved recovery flow applies;
11. never instruct pilot users to clear browser/site/application storage as routine rollback.

## Firebase migration compatibility

IAMINA native Django authentication is authoritative. Firebase remains dormant legacy migration code.

Firebase migration is disabled by default on backend and Flutter. No PWA/native pilot candidate may initialize or accept the legacy Firebase path unless an operator explicitly opens a controlled migration window with dedicated evidence.

## Native signing contract — deferred P5-4B

### Android

Release builds use external signing material only. `key.properties`, JKS and keystore files stay outside Git. Debug signing is forbidden for a claimed native pilot artifact.

### iOS

The final Runner bundle identifier remains `ma.iamina.app`. Apple signing/provisioning remains external and is required before any native iOS/TestFlight readiness claim.

## Retained P5-4A closure evidence

As of 2026-09-11:

- #557 packaging foundation merged with exact-head and exact-main CI green;
- #558 Chrome installability + persistent Drift proof merged; artifact #10262996477 retained `sharedIndexedDb`, zero installability errors and zero manifest errors;
- #559 strict offline app-shell proof merged; artifact #10265358161 proved hard reload with normal HTTP cache disabled and browser network forced offline;
- #560 aligned the PWA-first release contract;
- #561 accepted exact head `0204d858da2370b6d66c2a5fb56aaa66ad378153` with 5/5 exact-head gates green: CI #34630798331, packaging #34630798336, persistence #34630798330, offline #34630798385, update/recovery #34630798429;
- update/recovery artifact #10275967534, digest `sha256:d8999113e4c82771062bbb97163e6f821adc8ad53ee7e4974c079070e09eeb65`, retained top-level PASS, `sharedIndexedDb`, observed rejected-candidate install request, correct v3 bundle bytes before/after activation and offline, obsolete-cache purge, and `origin_storage_cleared=false`;
- #561 merged as `main@d2df37fc14b3c9fb1087d7629460b5c240d7ff2d`; exact-main CI #34634309275 SUCCESS;
- #569 added `docs/P5_PWA_PILOT_RUNBOOK.md` on exact head `894fdc79cd9bf06fbf9bff242a566eef677b3740`; CI #34634845390 SUCCESS;
- #569 merged as `main@35ab9c5cd70fa1f7e7f41978c8e1e5e1e1388387`; exact-main CI #34634913387 SUCCESS.

## P5-4A closure state

P5-4A engineering evidence is retained and closed with explicit boundaries. P5-4B stays deferred and open for native Android/iOS alignment.

No real-patient, CNDP/legal, controlled pilot URL, physical target-device install, Vercel, Android signing or iOS signing claim follows from P5-4A closure.

No Vercel deployment is authorized by this contract.
