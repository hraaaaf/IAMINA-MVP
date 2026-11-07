'use strict';

// W02-F09-C4 — UNMOUNTED BFF request constructor, not a Vercel function.
// The deployed /api/session-refresh.js remains always-deny. This helper
// prepares a dedicated, signed BFF→Django JSON request for synthetic testing
// and future review only. It performs NO fetch, cookie issuance or logging.
// Browser-controlled proof/OIDC headers are NEVER forwarded as assertions.
const { timingSafeEqual } = require('node:crypto');
const { signRefreshBoundary } = require('./w02_f09c2_signing.js');

const PROJECT = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const WEB_HOST = /^[a-z0-9-]+\.vercel\.app$/;
const FAMILY = /^[1-9][0-9]{0,17}$/;
const SECRET = /^iamina-wr1\.[A-Za-z0-9_-]{64}$/;
const CSRF = /^c2\.[0-9]{10}\.[A-Za-z0-9_-]{24}\.[0-9a-f]{64}$/;

function deny() {
  throw new Error('Web refresh transport unavailable');
}

function cookieValue(raw, key) {
  if (typeof raw !== 'string' || raw.length > 4096) return null;
  let found = null;
  for (const segment of raw.split(';')) {
    const part = segment.trim();
    const pos = part.indexOf('=');
    if (pos < 1 || part.slice(0, pos) !== key) continue;
    if (found !== null) return null; // No duplicates/cookie tossing.
    found = part.slice(pos + 1);
  }
  return found;
}

function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' ||
      !CSRF.test(a) || !CSRF.test(b)) return false;
  const x = Buffer.from(a, 'ascii');
  const y = Buffer.from(b, 'ascii');
  return x.length === y.length && timingSafeEqual(x, y);
}

function prepareDedicatedRefresh(req, options = {}) {
  const { env, oidcFromRuntime, signingKey } = options;
  if (!env || env.VERCEL_ENV !== 'preview' ||
      env.VERCEL_PROJECT_ID !== PROJECT ||
      typeof env.VERCEL_URL !== 'string' ||
      !WEB_HOST.test(env.VERCEL_URL) ||
      !req || req.method !== 'POST') deny();

  const host = env.VERCEL_URL;
  const browser = req.headers || {};
  const origin = 'https://' + host;
  if (browser.host !== host || browser.origin !== origin ||
      browser['sec-fetch-site'] !== 'same-origin') deny();

  // The future function MUST obtain this from Vercel's trusted runtime
  // injection, not from client-provided JWTs. Django validates it independently.
  if (typeof oidcFromRuntime !== 'string' ||
      oidcFromRuntime.length < 100 || oidcFromRuntime.length > 10000 ||
      typeof signingKey !== 'string') deny();

  const familyText = cookieValue(browser.cookie, 'iamina_refresh_family');
  const refresh = cookieValue(browser.cookie, 'iamina_refresh');
  const csrfCookie = cookieValue(browser.cookie, 'iamina_refresh_csrf');
  const csrfHeader = browser['x-iamina-csrf'];
  if (!FAMILY.test(familyText || '') || !SECRET.test(refresh || '') ||
      !safeEqual(csrfCookie, csrfHeader)) deny();

  // Exact keys and stable order; never include arbitrary browser headers.
  const body = Buffer.from(JSON.stringify({
    family_id: Number(familyText),
    raw_refresh: refresh,
    origin,
    csrf_cookie: csrfCookie,
    csrf_header: csrfHeader,
  }), 'utf8');
  if (body.length > 4096 ||
      !Number.isSafeInteger(Number(familyText))) deny();

  const signed = signRefreshBoundary({ key: signingKey, host, body });
  const headers = Object.freeze({
    'content-type': 'application/json',
    'x-vercel-trusted-oidc-idp-token': oidcFromRuntime,
    ...signed,
  });
  return Object.freeze({ method: 'POST', path: '/api/v1/auth/refresh', headers, body });
}

module.exports = { prepareDedicatedRefresh };
