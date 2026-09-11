const IAMINA_CACHE_PREFIX = 'iamina-app-shell-';
const IAMINA_CACHE_SCHEMA = '0.1.0+1';
const CACHE_NAME = `${IAMINA_CACHE_PREFIX}${IAMINA_CACHE_SCHEMA}`;

const PRECACHE = [
  './',
  './index.html',
  './flutter_bootstrap.js',
  './main.dart.js',
  './manifest.json',
  './favicon.png',
  './sqlite3.wasm',
  './drift_worker.js',
];

const STATIC_FILES = new Set([
  '/',
  '/index.html',
  '/flutter_bootstrap.js',
  '/main.dart.js',
  '/manifest.json',
  '/favicon.png',
  '/sqlite3.wasm',
  '/drift_worker.js',
]);
const STATIC_PREFIXES = ['/assets/', '/canvaskit/', '/icons/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE)),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter(
            (name) =>
              name.startsWith(IAMINA_CACHE_PREFIX) && name !== CACHE_NAME,
          )
          .map((name) => caches.delete(name)),
      ),
    ),
  );
  self.clients.claim();
});

function isCacheableStaticPath(pathname) {
  return (
    STATIC_FILES.has(pathname) ||
    STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))
  );
}

async function cacheFirstStatic(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request, { ignoreSearch: true });
  if (cached) return cached;

  const response = await fetch(request);
  if (response.ok) {
    await cache.put(request, response.clone());
  }
  return response;
}

async function cacheFirstNavigation(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached =
    (await cache.match('./index.html')) || (await cache.match('./'));
  if (cached) return cached;

  const response = await fetch(request);
  if (response.ok) {
    await cache.put('./index.html', response.clone());
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Patient/backend responses are never stored in the app-shell cache.
  if (url.pathname.startsWith('/api/')) return;

  if (request.mode === 'navigate') {
    event.respondWith(cacheFirstNavigation(request));
    return;
  }

  if (isCacheableStaticPath(url.pathname)) {
    event.respondWith(cacheFirstStatic(request));
  }
});
