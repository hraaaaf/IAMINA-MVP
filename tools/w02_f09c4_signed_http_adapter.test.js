'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash, createHmac } = require('node:crypto');
const { prepareDedicatedRefresh } = require('../frontend/api/w02_f09c4_prepare.js');

const HOST = 'iamina-c4-synthetic.vercel.app';
const CSRF = 'c2.1790000000.' + 'Z'.repeat(24) + '.' + 'a'.repeat(64);
const SECRET = 'iamina-wr1.' + 'Y'.repeat(64);
const ENV = Object.freeze({
  VERCEL_ENV: 'preview',
  VERCEL_PROJECT_ID: 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  VERCEL_URL: HOST,
});
const KEY = 'TEST_ONLY_C4_BFF_shared_transport_key_2026_48';
const OIDC = 'synthetic-runtime-only.' + 'R'.repeat(120);

function request() {
  return {
    method: 'POST',
    headers: {
      host: HOST,
      origin: 'https://' + HOST,
      'sec-fetch-site': 'same-origin',
      cookie: 'iamina_refresh_family=42; iamina_refresh=' + SECRET +
        '; iamina_refresh_csrf=' + CSRF,
      'x-iamina-csrf': CSRF,
      authorization: 'Bearer browser-injected',
      'x-vercel-oidc-token': 'browser-untrusted-token',
      'x-iamina-bff-proof': 'browser-forgery',
    },
  };
}

function prepared(req = request(), env = ENV) {
  return prepareDedicatedRefresh(req, { env, oidcFromRuntime: OIDC, signingKey: KEY });
}

test('C4 dedicated BFF builds only signed allowlisted body+headers', () => {
  const a = prepared();
  assert.equal(a.path, '/api/v1/auth/refresh');
  assert.equal(a.method, 'POST');
  const body = JSON.parse(a.body.toString('utf8'));
  assert.deepEqual(Object.keys(body), [
    'family_id', 'raw_refresh', 'origin', 'csrf_cookie', 'csrf_header',
  ]);
  assert.equal(body.family_id, 42);
  assert.equal(body.raw_refresh, SECRET);
  assert.equal(body.csrf_header, CSRF);
  assert.equal(a.headers['x-vercel-trusted-oidc-idp-token'], OIDC);
  for (const key of ['cookie', 'authorization', 'set-cookie', 'x-vercel-oidc-token']) {
    assert.equal(a.headers[key], undefined, key + ' must never be forwarded');
  }
  const ts = a.headers['x-iamina-bff-timestamp'];
  const canonical = [
    'iamina.web.refresh.bff.v1',
    'POST',
    '/api/v1/auth/refresh',
    ts,
    a.headers['x-iamina-bff-nonce'],
    'https://' + HOST,
    createHash('sha256').update(a.body).digest('hex'),
  ].join('\n');
  assert.equal(a.headers['x-iamina-bff-proof'],
    'v1.' + createHmac('sha256', KEY).update(canonical).digest('hex'));
});

test('C4 denies missing/duplicate/tampered cookies and same-site headers', () => {
  const mutations = [
    { cookie: 'iamina_refresh=' + SECRET + '; iamina_refresh_csrf=' + CSRF },
    { cookie: 'iamina_refresh_family=42; iamina_refresh=' + SECRET +
      '; iamina_refresh=' + SECRET + '; iamina_refresh_csrf=' + CSRF },
    { cookie: 'iamina_refresh_family=42; iamina_refresh=' + SECRET +
      '; iamina_refresh_csrf=' + CSRF + '; iamina_refresh_csrf=' + CSRF },
    { 'x-iamina-csrf': 'tampered' },
    { origin: 'https://attacker.invalid' },
    { 'sec-fetch-site': 'cross-site' },
    { host: 'attacker.invalid' },
  ];
  for (const mutation of mutations) {
    const req = request();
    req.headers = { ...req.headers, ...mutation };
    assert.throws(() => prepared(req), /unavailable/, JSON.stringify(mutation));
  }
});

test('C4 denies bad env, methods, and absent runtime token', () => {
  assert.throws(() => prepared(request(), { ...ENV, VERCEL_ENV: 'production' }), /unavailable/);
  assert.throws(() => prepared(request(), { ...ENV, VERCEL_PROJECT_ID: 'wrong' }), /unavailable/);
  const req = request();
  req.method = 'GET';
  assert.throws(() => prepared(req), /unavailable/);
  assert.throws(() => prepareDedicatedRefresh(request(), {
    env: ENV, oidcFromRuntime: null, signingKey: KEY,
  }), /unavailable/);
});

test('C4 cannot mount: deployed route remains deny-only, config keeps Vercel auto-deploy off', () => {
  const rules = JSON.parse(fs.readFileSync(
    path.join(__dirname, '../frontend/vercel.json'), 'utf8'));
  assert.equal(rules.git.deploymentEnabled, false);
  assert.equal(rules.rewrites[0].destination, '/api/session-refresh.js');
  const handlerSource = fs.readFileSync(
    path.join(__dirname, '../frontend/api/session-refresh.js'), 'utf8');
  assert.doesNotMatch(handlerSource, /require\(['"]\.\/w02_f09c4_prepare/);
  assert.match(handlerSource, /reject\(res, 404\)/);
});
