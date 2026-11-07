'use strict';

// W02-F09-C1: isolated, synthetic deny-by-default route gate only.
// NO token issuance or refresh. Origin + double-submit shape is NOT final CSRF
// authorization until signed session-bound nonce and BFF trust are reviewed.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const EXPECTED_PROJECT = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const PREVIEW_HOST = 'iamina-f09c1-synthetic.vercel.app';
const ENV = Object.freeze({
  VERCEL_ENV: 'preview',
  VERCEL_PROJECT_ID: EXPECTED_PROJECT,
  VERCEL_URL: PREVIEW_HOST,
});

function response() {
  const headers = new Map();
  return {
    statusCode: 200, headers, body: undefined,
    setHeader(k, v) { headers.set(k.toLowerCase(), v); },
    end(value) { this.body = value; },
  };
}
function request(overrides = {}) {
  return {
    method: 'POST',
    url: '/api/v1/auth/refresh',
    headers: {
      host: PREVIEW_HOST,
      origin: 'https://' + PREVIEW_HOST,
      cookie: 'iamina_refresh=synthetic-opaque; iamina_refresh_csrf=synthetic-csrf-value',
      'x-iamina-csrf': 'synthetic-csrf-value',
      'x-vercel-oidc-token': 'synthetic-oidc-not-a-session',
      authorization: 'Bearer synthetic-browser-bearer',
    },
    ...overrides,
  };
}
function handler() {
  return require('../frontend/api/session-refresh.js');
}
async function call(req = request(), env = ENV) {
  const res = response();
  let fetchCalls = 0;
  await handler()(req, res, {
    env,
    async fetchImpl() { fetchCalls++; throw Error('no upstream allowed before F09-C security gate'); },
  });
  assert.equal(fetchCalls, 0, 'C1 must never call Django, Vercel or other services');
  assert.equal(res.headers.has('set-cookie'), false, 'C1 never issues or rotates cookies');
  assert.equal(res.headers.has('access-control-allow-origin'), false);
  assert.equal(res.headers.get('cache-control'), 'no-store');
  assert.equal(res.headers.get('x-content-type-options'), 'nosniff');
  return res;
}

test('F09-C1 RED: exact refresh rewrite takes precedence over generic API bridge', () => {
  const config = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../frontend/vercel.json'), 'utf8'));
  assert.equal(config.git.deploymentEnabled, false, 'no Vercel auto-deployment');
  const rules = config.rewrites;
  const dedicated = rules.findIndex(r => r.source === '/api/v1/auth/refresh');
  const generic = rules.findIndex(r => r.source === '/api/v1/:path*');
  assert.ok(dedicated >= 0, 'dedicated route must be explicit');
  assert.ok(generic >= 0 && dedicated < generic, 'dedicated route precedes generic proxy');
  assert.equal(rules[dedicated].destination, '/api/session-refresh.js');
});

test('F09-C1: feature is unreachable outside exact synthetic Preview project', async () => {
  for (const env of [
    { ...ENV, VERCEL_ENV: 'production' },
    { ...ENV, VERCEL_PROJECT_ID: 'unrelated-project' },
    { ...ENV, VERCEL_URL: undefined },
  ]) {
    const res = await call(request(), env);
    assert.equal(res.statusCode, 404);
  }
});
test('F09-C1: cannot mutate by GET, OPTIONS, HEAD or PUT', async () => {
  for (const method of ['GET', 'OPTIONS', 'HEAD', 'PUT']) {
    const res = await call(request({ method }));
    assert.equal(res.statusCode, 405);
  }
});
test('F09-C1: no missing or conflicting Origin, Host, or cross-site fetch', async () => {
  const invalid = [
    { origin: undefined },
    { origin: 'null' },
    { origin: 'https://attacker.example' },
    { origin: 'https://' + PREVIEW_HOST + '.evil.test' },
    { origin: 'https://' + PREVIEW_HOST + '@attacker.example' },
    { origin: 'http://' + PREVIEW_HOST },
    { host: 'attacker.example' },
    { 'sec-fetch-site': 'cross-site' },
  ];
  for (const changes of invalid) {
    const req = request({ headers: { ...request().headers, ...changes } });
    const res = await call(req);
    assert.equal(res.statusCode, 403, JSON.stringify(changes));
  }
});
test('F09-C1: missing, duplicate, mismatched and header-injected csrf shape denied', async () => {
  const cases = [
    { cookie: 'iamina_refresh=synthetic-opaque' },
    { cookie: 'iamina_refresh_csrf=synthetic-csrf-value; iamina_refresh_csrf=other' },
    { cookie: 'iamina_refresh_csrf=synthetic-csrf-value', 'x-iamina-csrf': 'different' },
    { cookie: 'iamina_refresh_csrf=synthetic-csrf-value', 'x-iamina-csrf': undefined },
    { cookie: 'iamina_refresh_csrf=synthetic-csrf-value', 'x-iamina-csrf': 'bad\nheader' },
  ];
  for (const change of cases) {
    const req = request({ headers: { ...request().headers, ...change } });
    const res = await call(req);
    assert.equal(res.statusCode, 403, JSON.stringify(change));
  }
});
test('F09-C1: valid-looking POST still returns 404 disabled, never refreshes', async () => {
  const res = await call(request());
  assert.equal(res.statusCode, 404);
  assert.doesNotMatch(String(res.body), /iamina-wr1\.|access_token|synthetic-opaque/);
});
