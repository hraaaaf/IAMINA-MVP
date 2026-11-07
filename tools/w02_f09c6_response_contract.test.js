'use strict';

// W02-F09-C6: candidate response composition, NOT a live Vercel handler.
// A verified backend family result would be necessary for any future call.
// These oracles do not attest backend response provenance or hosted browser use.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  composeCandidateBffRefreshResult,
  composeCandidateBffLogoutResult,
} = require('../frontend/api/w02_f09c6_response_candidate.js');

const data = Object.freeze({
  familyId: '42',
  refreshSecret: 'iamina-wr1.' + 'P'.repeat(64),
  csrfToken: 'c2.1790000000.' + 'T'.repeat(24) + '.' + 'a'.repeat(64),
  accessBearer: 'iamina-web.' + 'a1B._:ef'.repeat(8),
  cookieMaxAgeSeconds: 120,
  accessMaxAgeSeconds: 60,
});

test('C6 BFF response separates access bearer JSON from HttpOnly refresh cookies', () => {
  const response = composeCandidateBffRefreshResult(data, { enabled: true });
  assert.equal(response.status, 200);
  assert.equal(response.headers['cache-control'], 'no-store');
  assert.equal(response.headers['pragma'], 'no-cache');
  assert.equal(response.headers['x-content-type-options'], 'nosniff');
  assert.equal(response.headers['referrer-policy'], 'no-referrer');
  assert.equal(response.headers['content-type'], 'application/json; charset=utf-8');
  assert.equal(response.headers['access-control-allow-origin'], undefined);
  const body = JSON.parse(response.body);
  assert.deepEqual(Object.keys(body), ['access_token', 'token_type', 'expires_in']);
  assert.equal(body.access_token, data.accessBearer);
  assert.equal(body.token_type, 'Bearer');
  assert.equal(body.expires_in, 60);
  assert.equal(response.headers['set-cookie'].length, 3);
  const allCookies = response.headers['set-cookie'].join('\n');
  assert.doesNotMatch(allCookies, /iamina-web\./);
  assert.match(allCookies, /HttpOnly; Secure; SameSite=Strict/);
  assert.ok(!response.body.includes(data.refreshSecret));
  assert.ok(!response.body.includes(data.csrfToken));
  assert.ok(!response.body.includes(data.familyId));
  assert.equal(Object.isFrozen(response.headers), true);
});

test('C6 BFF response refuses unauthorized toggles, injected body fields and TTL confusion', () => {
  for (const options of [{}, { enabled: false }, { enabled: 'true' }]) {
    assert.throws(() => composeCandidateBffRefreshResult(data, options), /unavailable/);
  }
  for (const mutation of [
    { accessBearer: 'not-a-family-bearer' },
    { accessBearer: data.accessBearer + '\r\nSet-Cookie: evil=1' },
    { familyId: '42; Domain=evil.test' },
    { refreshSecret: 'tampered' },
    { csrfToken: 'unsafe' },
    { cookieMaxAgeSeconds: 901 },
    { cookieMaxAgeSeconds: -1 },
    { accessMaxAgeSeconds: 121 },
    { accessMaxAgeSeconds: 0 },
    { accessMaxAgeSeconds: '60' },
    { accessMaxAgeSeconds: NaN },
    { next_url: 'https://attacker.invalid' },
    { access_token: 'attacker-request-data' },
  ]) {
    assert.throws(
      () => composeCandidateBffRefreshResult({ ...data, ...mutation }, { enabled: true }),
      /unavailable/,
    );
  }
});

test('C6 logout may clear cookies only after explicit trusted backend confirmation', () => {
  assert.throws(() => composeCandidateBffLogoutResult({ enabled: true }), /unavailable/);
  assert.throws(
    () => composeCandidateBffLogoutResult({ enabled: true, backendConfirmedRevoked: 'true' }),
    /unavailable/,
  );
  const response = composeCandidateBffLogoutResult({
    enabled: true, backendConfirmedRevoked: true,
  });
  assert.equal(response.status, 200);
  assert.equal(response.headers['set-cookie'].length, 3);
  assert.equal(JSON.parse(response.body).detail, 'Signed out');
  for (const cookie of response.headers['set-cookie']) {
    assert.match(cookie, /; Max-Age=0$/);
    assert.doesNotMatch(cookie, /iamina-wr1\.|iamina-web\./);
  }
  assert.equal(response.headers['cache-control'], 'no-store');
});

test('C6 candidate is not imported by live Vercel handlers; deployment remains off', () => {
  const root = path.join(__dirname, '..');
  for (const file of ['frontend/api/session-refresh.js', 'frontend/api/index.js']) {
    const source = fs.readFileSync(path.join(root, file), 'utf8');
    assert.doesNotMatch(source, /w02_f09c6_response_candidate/);
  }
  const route = fs.readFileSync(
    path.join(root, 'frontend/api/session-refresh.js'), 'utf8',
  );
  assert.match(route, /reject\(res, 404\)/);
  const vercel = JSON.parse(fs.readFileSync(
    path.join(root, 'frontend/vercel.json'), 'utf8',
  ));
  assert.equal(vercel.git.deploymentEnabled, false);
});
