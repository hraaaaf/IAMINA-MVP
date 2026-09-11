# IAMINA PWA Pilot Runbook

Status: P5-4A pilot operating runbook. This document does not authorize a production deployment, real-patient use, or P5-6 release.

## Goal

Give a pilot user an install/update path that requires no repository access, source code, terminal, or developer tooling while preserving local Drift data and the last-known-good offline shell.

## Release identity

`frontend/pubspec.yaml` is the canonical product version/build source.

Every promoted PWA candidate MUST increment the canonical version/build before release. The service-worker app-shell cache identity MUST match that version/build. A candidate whose cache identity and `pubspec` version differ is not releasable.

Retained release evidence must record at least:

- application version + build number;
- exact Git SHA;
- retained CI/browser evidence IDs and digests where available;
- controlled pilot URL once deployment is explicitly authorized.

## First installation

Human-visible flow once a controlled pilot URL exists:

1. Open the controlled IAMINA pilot URL in a supported browser.
2. Confirm the page identifies itself as IAMINA and browser installability is available.
3. Use the browser's normal **Install / Add to Home Screen** action.
4. Launch IAMINA from the installed icon.
5. Do not enable real-patient use until P5-6 is separately satisfied.

No GitHub account, repository checkout, terminal command, developer mode, APK, TestFlight, or source access is part of the PWA installation path.

`PILOT_URL` remains unresolved until deployment is explicitly authorized. No Vercel deployment is authorized by this runbook.

## Normal update behavior

IAMINA updates are deliberately non-disruptive:

1. The currently open PWA continues using its already-installed, release-coherent app shell.
2. After page load and while online, the bootstrap performs a network-only `no-store` probe of `iamina_service_worker.js`, reads the canonical `IAMINA_CACHE_SCHEMA`, and registers the release-versioned script URL `iamina_service_worker.js?release=<schema>` with `updateViaCache: 'none'`. Flutter startup does not wait for this work.
3. A canonical version/build change therefore changes the registered service-worker script URL and deterministically starts the browser update algorithm, even when the active release is serving an older cache-first bootstrap.
4. A healthy candidate installs into a **separate versioned app-shell cache**. Each precached shell resource is fetched with browser HTTP-cache bypass (`cache: 'reload'`) before it is stored, so the new release cache cannot silently inherit stale bytes from the previous release.
5. An explicit background `registration.update()` remains only as a non-blocking same-release fallback. Normal release promotion does not depend on its timing.
6. The candidate does **not** force `skipWaiting()` and does not take over an active clinical/user session.
7. The new worker may remain `waiting` while the old PWA session is open.
8. After the user fully closes the installed PWA, the old controlled client disappears.
9. On a later launch, the healthy waiting worker may activate naturally.
10. Only after activation are obsolete IAMINA app-shell caches removed.
11. Drift/IndexedDB origin storage is retained throughout; update logic must never clear it.

Practical pilot instruction: finish the current interaction, fully close IAMINA, then reopen it. The update path must not require clearing browser/site storage.

## Failed update behavior

If a new app shell cannot finish installation:

- the new worker must not become active;
- the previous healthy service worker/cache remains the last-known-good shell;
- IAMINA must remain able to reopen offline from that last-known-good shell;
- Drift/IndexedDB data remains intact;
- a partial inactive candidate cache may remain temporarily, but it must never control the app and is purged when a later healthy release activates;
- rollout of the broken candidate is stopped.

Routine advice to clear site data, browser storage, IndexedDB, or reinstall from scratch is forbidden because local-first data is user data, not disposable cache.

## Forward-fix recovery

Rollback to an older binary/schema is not assumed safe.

Recovery sequence:

1. Stop promotion of the bad candidate.
2. Preserve browser origin storage and the current healthy shell.
3. Prepare a forward-fix candidate with a higher canonical version/build.
4. Validate build, persistent Drift, offline shell, healthy-update activation and compatibility evidence on the exact candidate SHA.
5. Publish the forward fix only through the controlled pilot channel after release authorization.
6. On a later normal startup, let the production bootstrap discover the higher canonical release through the network-only service-worker probe and register its release-versioned script URL. Do not force an immediate second update seconds after a rejected service-worker install.
7. Let the healthy new worker install separately and activate across a normal close/reopen boundary.
8. Verify the active release cache contains the forward-fix bundle itself, not stale HTTP-cache bytes.
9. Verify retained Drift data and offline reopen after activation.
10. Verify obsolete IAMINA caches, including any inactive failed-candidate residue, are gone after healthy activation.

The engineering certification deliberately proves **failed-candidate preservation** and **healthy N -> N+1 activation** as separate deterministic browser properties. Immediate same-profile forward-fix timing directly after a rejected install is not certified because Chrome post-failure scheduling is browser-controlled and was observed to be non-deterministic.

## Cache boundary

The IAMINA app-shell cache is for approved static application resources only.

It must not cache:

- `/api/` responses;
- authenticated or patient backend responses;
- mutating requests;
- arbitrary cross-origin resources.

## Promotion gate

A PWA candidate is not promoted merely because `flutter build web` succeeds.

Required engineering evidence before promotion:

- self-contained release build;
- manifest/installability proof;
- persistent `sharedIndexedDb` browser storage proof;
- true offline hard-reload proof with normal HTTP cache disabled;
- release-specific cache identity matching canonical version/build;
- deterministic release discovery through the network-only service-worker probe and release-versioned registration URL;
- release-coherent precache with HTTP-cache bypass for shell assets;
- deterministic failed-candidate proof showing last-known-good shell + Drift preservation;
- deterministic healthy N -> N+1 proof showing waiting worker, close/reopen activation, correct new-release bundle bytes, Drift preservation and offline reopen;
- purge of obsolete IAMINA caches after healthy activation;
- no origin-storage clearing;
- exact-SHA evidence retained.

A controlled pilot URL and supported physical target-browser/device installation remain human/external gates until separately evidenced.

## Boundaries

PWA-first does not waive P5-6. No real-patient, CNDP/legal, clinical-human, native Android/iOS, or Vercel readiness claim follows from this runbook.
