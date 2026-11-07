'use strict';

// Synthetic W01 Preview only: same-origin API bridge.
// Browser credentials are never forwarded to another Vercel deployment.
// Vercel injects the short-lived OIDC token into the function request; the
// destination API project must independently trust Web Preview -> API Preview.
const EXPECTED_PROJECT = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const API_URL_PATTERN = /^https:\/\/iamina-certified-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app\/?$/;
const MAX_RESPONSE_BYTES = 25 * 1024 * 1024;
const METHODS = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']);
const REQUEST_HEADERS = [
  'accept', 'authorization', 'content-type', 'if-match', 'if-none-match',
  'idempotency-key', 'x-request-id',
];
const RESPONSE_HEADERS = [
  'content-type', 'content-disposition', 'etag', 'cache-control', 'last-modified',
  'x-request-id',
];

function fail(res, status, message) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify({ detail: message }));
}

function validTarget(origin) {
  if (typeof origin !== 'string' || !API_URL_PATTERN.test(origin)) return null;
  return origin.replace(/\/$/, '');
}

function validPath(value) {
  if (typeof value !== 'string' || !value || value.length > 512) return null;
  if (!/^[A-Za-z0-9_./-]+$/.test(value)) return null;
  if (value.startsWith('/') || value.includes('//') || value.split('/').includes('..')) return null;
  return value;
}

async function proxy(req, res, options = {}) {
  const env = options.env || process.env;
  const fetchImpl = options.fetchImpl || fetch;

  if (env.VERCEL_ENV !== 'preview' || env.VERCEL_PROJECT_ID !== EXPECTED_PROJECT) {
    fail(res, 404, 'Not found');
    return;
  }
  const origin = validTarget(env.IAMINA_REVIEW_PREVIEW_API_BASE_URL);
  if (!origin) {
    fail(res, 503, 'Preview API configuration unavailable');
    return;
  }

  const method = String(req.method || '').toUpperCase();
  if (method === 'OPTIONS') {
    res.statusCode = 204;
    res.setHeader('Allow', [...METHODS].join(', '));
    res.end();
    return;
  }
  if (!METHODS.has(method)) {
    fail(res, 405, 'Unsupported method');
    return;
  }
  const relativePath = validPath(req.query && req.query.forward);
  if (!relativePath) {
    fail(res, 400, 'Invalid API path');
    return;
  }
  // W02-F09-A: refresh must have its OWN reviewed same-origin BFF handler.
  // Never treat future renewal credentials as regular clinical API traffic:
  // the generic bridge intentionally does not forward Cookie/Set-Cookie or
  // perform refresh-specific CSRF, Origin, replay or rotation checks.
  // Exact path reservation is fail-closed; no renewal endpoint is enabled.
  if (relativePath === 'auth/refresh' || relativePath === 'auth/refresh/') {
    fail(res, 404, 'Not found');
    return;
  }
  // Never accept client-supplied destination URLs or follow redirects. The
  // only outbound host is the exact immutable synthetic Preview API.
  const target = new URL(`/api/v1/${relativePath}`, `${origin}/`);
  const requested = new URL(req.url || '/', 'https://preview.invalid');
  requested.searchParams.delete('forward');
  target.search = requested.searchParams.toString();

  const issuedToken = req.headers && req.headers['x-vercel-oidc-token'];
  if (typeof issuedToken !== 'string' || !issuedToken) {
    fail(res, 503, 'Protected API transport unavailable');
    return;
  }
  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = req.headers?.[name];
    if (typeof value === 'string') headers.set(name, value);
  }
  headers.set('x-vercel-trusted-oidc-idp-token', issuedToken);
  // Never forward browser cookies, x-vercel-oidc-token, or arbitrary headers.

  const hasBody = !['GET', 'HEAD'].includes(method);
  const opts = { method, headers, redirect: 'manual', signal: AbortSignal.timeout(20000) };
  if (hasBody) {
    // Vercel Node Functions expose a body stream. Disable framework parsing,
    // retaining JSON, upload, and sync request bodies unmodified.
    opts.body = req;
    opts.duplex = 'half';
  }
  let upstream;
  try {
    upstream = await fetchImpl(target.toString(), opts);
  } catch (_) {
    fail(res, 502, 'Preview API temporarily unavailable');
    return;
  }
  if (upstream.status >= 300 && upstream.status < 400) {
    fail(res, 502, 'Unexpected API redirect');
    return;
  }
  const declaredLength = Number(upstream.headers.get('content-length'));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_RESPONSE_BYTES) {
    fail(res, 502, 'API response exceeds Preview limit');
    return;
  }
  let bytes;
  try {
    bytes = Buffer.from(await upstream.arrayBuffer());
  } catch (_) {
    fail(res, 502, 'API response unavailable');
    return;
  }
  if (bytes.length > MAX_RESPONSE_BYTES) {
    fail(res, 502, 'API response exceeds Preview limit');
    return;
  }
  res.statusCode = upstream.status;
  for (const name of RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) res.setHeader(name, value);
  }
  res.setHeader('Cache-Control', 'no-store');
  res.end(method === 'HEAD' ? undefined : bytes);
}

module.exports = proxy;
module.exports.proxy = proxy;
module.exports.config = { api: { bodyParser: false } };
