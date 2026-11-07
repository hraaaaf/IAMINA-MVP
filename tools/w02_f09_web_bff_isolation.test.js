'use strict';

// W02-F09-A: Web BFF trust-boundary contract; synthetic only.
// The future HttpOnly refresh cookie MUST be handled on a dedicated route,
// never by the generic Preview API bridge. No real credentials or deployments.
const test = require('node:test');
const assert = require('node:assert/strict');
const { proxy } = require('../frontend/api/index.js');

const ENV = Object.freeze({
  VERCEL_ENV: 'preview',
  VERCEL_PROJECT_ID: 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  IAMINA_REVIEW_PREVIEW_API_BASE_URL:
    'https://iamina-certified-synthetic-achraf-benmoussa-s-projects.vercel.app',
});

function request(relativePath, method = 'GET') {
  return {
    method,
    query: { forward: relativePath },
    url: '/api?forward=' + encodeURIComponent(relativePath),
    headers: {
      'x-vercel-oidc-token': 'synthetic-oidc',
      authorization: 'Bearer iamina.synthetic.not-real',
      cookie: 'sessionid=legacy-synthetic; iamina_refresh=synthetic-secret',
      'x-iamina-refresh-token': 'synthetic-secret',
    },
  };
}

function response() {
  const headers = new Map();
  return {
    statusCode: 200,
    headers,
    setHeader(name, value) { headers.set(name.toLowerCase(), value); },
    end(bytes) { this.body = bytes; },
  };
}

test('F09-A: generic clinical API transport never forwards browser refresh cookies', async () => {
  const res = response();
  let seen;
  await proxy(request('logs'), res, {
    env: ENV,
    async fetchImpl(target, options) {
      seen = { target, options };
      return new Response('{"items":[]}', {
        status: 200,
        headers: {
          'content-type': 'application/json',
          'set-cookie': 'iamina_refresh=synthetic-secret; Secure; HttpOnly',
        },
      });
    },
  });
  assert.equal(res.statusCode, 200);
  assert.ok(seen, 'clinical BFF call must reach the synthetic upstream');
  assert.equal(seen.options.headers.get('authorization'), 'Bearer iamina.synthetic.not-real');
  for (const forbidden of ['cookie', 'x-iamina-refresh-token', 'x-vercel-oidc-token']) {
    assert.equal(seen.options.headers.has(forbidden), false, forbidden);
  }
  assert.equal(seen.options.headers.get('x-vercel-trusted-oidc-idp-token'), 'synthetic-oidc');
  assert.equal(res.headers.has('set-cookie'), false, 'upstream must not inject browser cookies');
  assert.equal(res.headers.get('cache-control'), 'no-store');
});

for (const relativePath of ['auth/refresh', 'auth/refresh/']) {
  test('F09-A RED: generic BFF must reserve ' + relativePath + ' for reviewed session route', async () => {
    const res = response();
    let upstreamCalls = 0;
    await proxy(request(relativePath, 'POST'), res, {
      env: ENV,
      async fetchImpl() {
        upstreamCalls += 1;
        return new Response('{"access_token":"must-never-reach-browser-here"}', {
          status: 200,
          headers: {
            'content-type': 'application/json',
            'set-cookie': 'iamina_refresh=synthetic; HttpOnly; Secure',
          },
        });
      },
    });
    assert.equal(res.statusCode, 404, 'reserved renewal must not use generic proxy');
    assert.equal(upstreamCalls, 0, 'no generic credential-bearing upstream request');
    assert.equal(res.headers.has('set-cookie'), false, 'no refresh cookie on generic route');
  });
}

test('F09-A: generic bridge remains disabled outside the narrow synthetic Preview', async () => {
  const res = response();
  let upstreamCalls = 0;
  await proxy(request('auth/refresh'), res, {
    env: { ...ENV, VERCEL_ENV: 'production' },
    async fetchImpl() { upstreamCalls += 1; throw Error('unexpected'); },
  });
  assert.equal(res.statusCode, 404);
  assert.equal(upstreamCalls, 0);
});
