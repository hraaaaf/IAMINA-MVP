/**
 * Synthetic first-install / old-cache replacement checks for IAMINA's PWA.
 * Run with: node scripts/tests/test_sse_pwa_cache_contract.mjs
 * No network, patient data, external providers, or deployment.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const worker = readFileSync(new URL('../../frontend/web/iamina_service_worker.js', import.meta.url), 'utf8');
const bootstrap = readFileSync(new URL('../../frontend/web/flutter_bootstrap.js', import.meta.url), 'utf8');
const pubspec = readFileSync(new URL('../../frontend/pubspec.yaml', import.meta.url), 'utf8');
const version = pubspec.match(/^version:\s*(\d+\.\d+\.\d+\+\d+)$/m)?.[1];
assert.ok(version, 'canonical Flutter build version must be present');
assert.ok(worker.includes("const IAMINA_CACHE_SCHEMA = '" + version + "';"),
  'worker cache version must match pubspec');
assert.ok(bootstrap.includes("const IAMINA_FALLBACK_RELEASE = '" + version + "';"),
  'bootstrap fallback version must match pubspec');
assert.ok(bootstrap.includes("cache: 'no-store'"),
  'release discovery must bypass browser HTTP cache');

function harness(hostname) {
  const scope = 'https://' + hostname + '/';
  const events = new Map();
  const stores = new Map();
  const networkRequests = [];
  const actions = { claim: 0, unregister: 0, skipWaiting: 0, navigate: [] };
  const keyOf = (request) =>
    new URL(typeof request === 'string' ? request : request.url, scope).href;
  const caches = {
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); },
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map());
      const store = stores.get(name);
      return {
        async put(request, response) { store.set(keyOf(request), response.clone()); },
        async match(request, options = {}) {
          const key = keyOf(request);
          if (!options.ignoreSearch) return store.get(key)?.clone();
          const pathname = new URL(key).pathname;
          for (const [saved, response] of store) {
            if (new URL(saved).pathname === pathname) return response.clone();
          }
          return undefined;
        },
      };
    },
  };
  const self = {
    location: { hostname, origin: scope.slice(0, -1) },
    registration: {
      scope,
      async unregister() { actions.unregister++; },
    },
    clients: {
      async claim() { actions.claim++; },
      async matchAll() {
        return [{ url: scope, navigate(url) { actions.navigate.push(url); } }];
      },
    },
    skipWaiting() { actions.skipWaiting++; },
    addEventListener(name, callback) { events.set(name, callback); },
  };
  async function fetchMock(request) {
    const url = keyOf(request);
    networkRequests.push({
      url,
      cache: typeof request === 'string' ? undefined : request.cache,
    });
    return new Response('fresh:' + new URL(url).pathname, { status: 200 });
  }
  runInNewContext(worker, { URL, Request, Response, caches, self, fetch: fetchMock });
  async function dispatch(name, request) {
    const listener = events.get(name);
    assert.ok(listener, 'missing ' + name + ' listener');
    let work;
    let response;
    listener({
      request,
      waitUntil(promise) { work = promise; },
      respondWith(promise) { response = promise; },
    });
    if (work) await work;
    return response ? await response : undefined;
  }
  return { caches, stores, actions, events, networkRequests, dispatch, scope };
}

const site = harness('iamina-synthetic.invalid');
assert.equal((await site.caches.keys()).length, 0, 'first install must be clean');
await site.dispatch('install');
assert.deepEqual(await site.caches.keys(), ['iamina-app-shell-' + version]);
assert.equal(site.networkRequests.length, 8, 'precache exactly expected shell resources');
assert.ok(site.networkRequests.every((req) => req.cache === 'reload'),
  'first installation must force fresh assets');

const stale = await site.caches.open('iamina-app-shell-obsolete');
await stale.put(new Request(site.scope + 'main.dart.js'),
  new Response('STALE_GET_SSE_BUNDLE'));
await site.dispatch('activate');
assert.deepEqual(await site.caches.keys(), ['iamina-app-shell-' + version],
  'activation must evict prior shell version');
assert.equal(site.actions.claim, 1, 'worker must claim shell clients');

const staticResponse = await site.dispatch('fetch', {
  method: 'GET', url: site.scope + 'main.dart.js?cachebust=1', mode: 'same-origin',
});
assert.equal(await staticResponse.text(), 'fresh:/main.dart.js',
  'old cached GET SSE shell must not survive cache activation');

const apiCallsBefore = site.networkRequests.length;
for (const method of ['GET', 'POST']) {
  const route = site.scope + 'api/v1/ai/chat/stream';
  const response = await site.dispatch('fetch', {
    method, url: route, mode: 'same-origin',
  });
  assert.equal(response, undefined, method + ' clinical API must bypass service-worker cache');
}
assert.equal(site.networkRequests.length, apiCallsBefore,
  'service worker must not fetch patient API calls itself');
assert.equal((await site.caches.keys()).length, 1,
  'API bypass must not create a data cache');

const navigation = await site.dispatch('fetch', {
  method: 'GET', url: site.scope, mode: 'navigate',
});
assert.equal(await navigation.text(), 'fresh:/index.html',
  'first navigation should use freshly precached shell');

const hosted = harness('iamina-review.vercel.app');
const oldHosted = await hosted.caches.open('iamina-app-shell-legacy');
await oldHosted.put(new Request(hosted.scope + 'main.dart.js'), new Response('stale'));
await hosted.dispatch('install');
await hosted.dispatch('activate');
assert.equal((await hosted.caches.keys()).length, 0, 'review must purge old caches');
assert.equal(hosted.actions.unregister, 1, 'review must unregister stale worker');
assert.equal(hosted.actions.navigate.length, 1, 'review must reload stale open client');
assert.equal(hosted.events.has('fetch'), false, 'hosted review must not cache app routes');

console.log('PASS: clean synthetic PWA install, fresh cache, obsolete shell eviction, API bypass, hosted-review cleanup.');
