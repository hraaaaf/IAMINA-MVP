'use strict';

// W02-F09-C1: intentionally NON-OPERATIONAL Web-only route.
// This is not an authenticator, not a session renewal endpoint, and does not
// accept or send any secret to Django. It is permanently fail-closed until a
// separate, independently-reviewed BFF/session contract replaces the stub.
// All validation below is preflight hygiene, NOT sufficient CSRF protection:
// a matching unsigned cookie/header MUST NOT authorize a future refresh.
const { timingSafeEqual } = require('node:crypto');

const EXPECTED_PROJECT = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const HOST_RE = /^[a-z0-9-]+\.vercel\.app$/;
const CSRF_SHAPE = /^[A-Za-z0-9_-]{16,128}$/;

function reject(res, status) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  // Always omit Set-Cookie, Authorization, CORS and browser-readable tokens.
  res.end(JSON.stringify({ detail: status === 405 ? 'Method not allowed' :
    status === 403 ? 'Forbidden' : 'Not found' }));
}

function previewHost(env) {
  if (env?.VERCEL_ENV !== 'preview' ||
      env?.VERCEL_PROJECT_ID !== EXPECTED_PROJECT) return null;
  const host = env?.VERCEL_URL;
  if (typeof host !== 'string' || !HOST_RE.test(host)) return null;
  return host;
}

function oneCookie(raw, key) {
  if (typeof raw !== 'string' || raw.length > 4096) return null;
  let found = null;
  for (const field of raw.split(';')) {
    const chunk = field.trim();
    const sep = chunk.indexOf('=');
    if (sep < 1) continue;
    if (chunk.slice(0, sep) !== key) continue;
    if (found !== null) return null; // Duplicate / cookie tossing.
    found = chunk.slice(sep + 1);
  }
  return found;
}

function constantTimeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' ||
      !CSRF_SHAPE.test(a) || !CSRF_SHAPE.test(b)) return false;
  const left = Buffer.from(a, 'ascii');
  const right = Buffer.from(b, 'ascii');
  return left.length === right.length && timingSafeEqual(left, right);
}

function hasOriginAndCsrfShape(req, host) {
  const headers = req?.headers || {};
  const expected = 'https://' + host;
  if (headers.host !== host || headers.origin !== expected) return false;
  if (headers['sec-fetch-site'] !== undefined &&
      headers['sec-fetch-site'] !== 'same-origin') return false;
  const cookie = headers.cookie;
  const refresh = oneCookie(cookie, 'iamina_refresh');
  const csrf = oneCookie(cookie, 'iamina_refresh_csrf');
  if (typeof refresh !== 'string' || refresh.length === 0) return false;
  return constantTimeEqual(csrf, headers['x-iamina-csrf']);
}

async function deniedRefresh(req, res, options = {}) {
  const env = options.env || process.env;
  const host = previewHost(env);
  if (!host) {
    reject(res, 404);
    return;
  }
  if (req?.method !== 'POST') {
    reject(res, 405);
    return;
  }
  if (!hasOriginAndCsrfShape(req, host)) {
    reject(res, 403);
    return;
  }
  // Even with apparently valid Origin and double-submit preflight, there is
  // NO authenticated binding between CSRF and a Django refresh family.
  // ALWAYS deny; no fetch, no cookie issuance, no state mutation.
  reject(res, 404);
}

module.exports = deniedRefresh;
module.exports.deniedRefresh = deniedRefresh;
module.exports.config = { api: { bodyParser: false } };
