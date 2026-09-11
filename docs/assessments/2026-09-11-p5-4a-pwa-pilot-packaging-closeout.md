# P5-4A — PWA Pilot Packaging Closeout

Date: 2026-09-11  
Status: **ENGINEERING CLOSED_WITH_BOUNDARIES**  
Tracker: #519  
Canonical roadmap: `docs/ROADMAP.md`

## Goal

Prove a PWA-first pilot delivery path that is reproducible from an exact Git SHA, installable without repository/developer access, persistent/offline, release-coherent across updates, non-destructive to local Drift data, and recoverable after a rejected candidate.

## Success criteria

P5-4A engineering may close only with retained evidence for:

1. self-contained exact-SHA PWA build;
2. stable release identity/version;
3. browser installability without repository/developer tooling;
4. persistent `sharedIndexedDb` Drift storage;
5. true offline hard reload;
6. deterministic N -> N+1 service-worker discovery and release-coherent cache rollover;
7. rejected-candidate last-known-good preservation;
8. healthy candidate waiting/activation across close/reopen;
9. no origin-storage clearing;
10. documented pilot install/update/recovery operating model.

## Retained evidence

### Foundation / installability / persistence / offline

- #557 foundation merged as `main@b6774773a0200a90b997aa7ec17c911421b023c4`.
- #558 Chrome installability + persistent Drift merged as `main@8cabab85d519f94a506150e54c7115c52ef0e1ec`.
- Browser artifact #10262996477, digest `sha256:6c9f74f29c8b8ff8b3b97321ac34bd51418c94a5289a9f307f48aea13e10c5bb`, retained `sharedIndexedDb` and zero installability/manifest errors.
- #559 strict offline shell merged as `main@5fe3380c185bb780f8440e902c9b029a5cf1f85b`.
- Offline artifact #10265358161, digest `sha256:eba7bdd5d4a2f70c2fbca124f8319b5360e300ae416d200b8ed5524ff5e5df94`, proved HTTP cache disabled + browser network forced offline + hard-reload restore of the retained fixture.
- #560 aligned `docs/PILOT_RELEASE.md` with the PWA-first release contract.

### Update / recovery

Accepted exact head: `0204d858da2370b6d66c2a5fb56aaa66ad378153`.

Exact-head gates:

- CI #34630798331 — SUCCESS;
- pilot mobile packaging #34630798336 — SUCCESS;
- browser persistence #34630798330 — SUCCESS;
- strict offline app-shell #34630798385 — SUCCESS;
- update/recovery #34630798429 — SUCCESS.

Retained update/recovery artifact:

- artifact #10275967534;
- digest `sha256:d8999113e4c82771062bbb97163e6f821adc8ad53ee7e4974c079070e09eeb65`;
- top-level `result: PASS`;
- `storage_implementation: sharedIndexedDb` on both deterministic scenarios;
- rejected v2 install attempt observed via `/missing-v2.asset`;
- rejected v2 never became waiting/active and v1 remained the last-known-good shell;
- broken-candidate offline restore succeeded;
- healthy v3 reached `waiting` beside active v1;
- v3 cache bundle identity verified before activation, after activation, and offline;
- obsolete IAMINA caches reduced to the v3 cache after activation;
- `origin_storage_cleared: false`.

Product behavior certified by that proof:

- bootstrap performs a network-only `no-store` probe of `iamina_service_worker.js` after page load;
- canonical `IAMINA_CACHE_SCHEMA` drives a release-versioned service-worker registration URL;
- `updateViaCache: 'none'` bypasses worker HTTP caching;
- release change therefore deterministically starts browser update discovery even if the old cache-first bootstrap is running;
- explicit `registration.update()` remains a non-blocking same-release fallback only;
- release precache fetches shell assets with `cache: 'reload'` before storing them, preventing stale HTTP-cache bytes from contaminating a new release cache;
- production has no `skipWaiting()` takeover;
- activation occurs naturally after controlled-client close/reopen;
- Drift/IndexedDB is never cleared by update logic.

#561 merged as `main@d2df37fc14b3c9fb1087d7629460b5c240d7ff2d`; exact-main post-merge CI #34634309275 — SUCCESS.

### Pilot operating runbook

#569 exact head `894fdc79cd9bf06fbf9bff242a566eef677b3740` documented the certified mechanism in `docs/P5_PWA_PILOT_RUNBOOK.md`; CI #34634845390 — SUCCESS.

#569 merged as `main@35ab9c5cd70fa1f7e7f41978c8e1e5e1e1388387`; exact-main post-merge CI #34634913387 — SUCCESS.

## Rejected assumptions retained as evidence

The final model was reached by rejecting unsafe or non-deterministic assumptions rather than weakening the proof:

- network-first + automatic `skipWaiting()` was rejected because it could displace the last-known-good offline shell;
- same-session immediate forward-fix timing after a rejected worker was rejected as browser-scheduling dependent;
- symlink-backed candidate exposure was rejected as unreliable;
- CDP-only observation was replaced by durable server-side install-request evidence;
- delayed same-URL `registration.update()` was rejected after repeated no-install evidence;
- release-versioned discovery solved the stale-bootstrap catch-22;
- the first deterministic discovery pass exposed stale HTTP-cache contamination of v3 shell bytes, which was fixed by release precache with `cache: 'reload'`.

## Boundaries / non-claims

This closeout is **engineering-only**.

It does not claim or authorize:

- a Vercel or production deployment;
- a controlled pilot URL;
- physical target-device/browser installation evidence;
- native Android/iOS release readiness;
- P5-6 completion;
- CNDP/legal/processor/residency approval;
- clinical-human approval;
- real-patient use.

P5-4B native Android/iOS alignment remains deferred. P5-4 overall therefore remains open as a split workstream even though P5-4A engineering is closed.

## Progress arithmetic

No P5 numerator change is taken from this sub-lot closeout. Canonical Pilot Readiness remains **3/9 = 33.3%** because P5-4 is not closed as a whole. MENA remains **32/38 = 84.2%**.

## Conclusion

**P5-4A engineering: CLOSED_WITH_BOUNDARIES.**

The immediate engineering critical path moves away from PWA packaging and toward the remaining human/external release gates, especially P5-6, while P5-4B remains deferred until a native lane is intentionally activated.
