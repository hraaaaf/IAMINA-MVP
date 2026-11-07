'use strict';

// W02-F09-C6: PURE, UNMOUNTED candidate BFF response contract.
// It does NOT fetch the backend, verify Vercel OIDC, verify response
// provenance, set headers on a real HTTP response or expose a live endpoint.
// Its caller must separately prove the C4 service envelope and C5 authority
// before using this serializer in any future independently-reviewed route.
const {
  candidateRefreshCookieHeaders,
  candidateLogoutCookieHeaders,
} = require('./w02_f09c5_cookie_policy.js');

const BEARER = /^iamina-web\.[A-Za-z0-9_.:-]{24,2040}$/;
const FIELDS = Object.freeze([
  'familyId', 'refreshSecret', 'csrfToken', 'accessBearer',
  'cookieMaxAgeSeconds', 'accessMaxAgeSeconds',
]);

function reject() {
  throw new Error('Web session response candidate unavailable');
}

function baseHeaders() {
  return {
    'cache-control': 'no-store',
    'pragma': 'no-cache',
    'referrer-policy': 'no-referrer',
    'x-content-type-options': 'nosniff',
    'content-type': 'application/json; charset=utf-8',
    'vary': 'Cookie',
  };
}

function composeCandidateBffRefreshResult(result, { enabled } = {}) {
  if (enabled !== true || !result || typeof result !== 'object' ||
      Array.isArray(result) ||
      Object.keys(result).sort().join('|') !== [...FIELDS].sort().join('|') ||
      typeof result.accessBearer !== 'string' ||
      !BEARER.test(result.accessBearer) ||
      !Number.isSafeInteger(result.accessMaxAgeSeconds) ||
      result.accessMaxAgeSeconds < 1 ||
      !Number.isSafeInteger(result.cookieMaxAgeSeconds) ||
      result.accessMaxAgeSeconds > result.cookieMaxAgeSeconds) reject();

  // C5 applies stronger host-only Secure/HttpOnly/Strict cookie constraints;
  // both TTLs are synthetic fixtures, not approved patient UX policy.
  let cookies;
  try {
    cookies = candidateRefreshCookieHeaders({
      enabled: true,
      familyId: result.familyId,
      refreshSecret: result.refreshSecret,
      csrfToken: result.csrfToken,
      maxAgeSeconds: result.cookieMaxAgeSeconds,
    });
  } catch {
    reject();
  }

  const headers = Object.freeze({
    ...baseHeaders(),
    'set-cookie': cookies,
  });
  // The browser may hold this SHORT-LIVED access token in memory only.
  // Never return refresh secret, family identifier or CSRF in JSON.
  const body = JSON.stringify({
    access_token: result.accessBearer,
    token_type: 'Bearer',
    expires_in: result.accessMaxAgeSeconds,
  });
  return Object.freeze({ status: 200, headers, body });
}

function composeCandidateBffLogoutResult(options = {}) {
  if (options.enabled !== true || options.backendConfirmedRevoked !== true ||
      Object.keys(options).sort().join('|') !==
        'backendConfirmedRevoked|enabled') reject();
  const headers = Object.freeze({
    ...baseHeaders(),
    'set-cookie': candidateLogoutCookieHeaders({ enabled: true }),
  });
  return Object.freeze({
    status: 200, headers, body: JSON.stringify({ detail: 'Signed out' }),
  });
}

module.exports = {
  composeCandidateBffRefreshResult,
  composeCandidateBffLogoutResult,
};
