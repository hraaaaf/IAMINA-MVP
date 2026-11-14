'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { proxy } = require('../api/index.js');

const env = {
  VERCEL_ENV: 'preview',
  VERCEL_PROJECT_ID: 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  VERCEL_GIT_COMMIT_REF: 'feat/d2-guest-bootstrap-no-db-20261114',
  IAMINA_REVIEW_PREVIEW_API_BASE_URL:
    'https://iamina-certified-m3fxatyv1-achraf-benmoussa-s-projects.vercel.app',
};

function response() {
  return {
    statusCode: 0, headers: {}, body: '',
    setHeader(key, value) { this.headers[key.toLowerCase()] = value; },
    end(body = '') { this.body = body; },
  };
}
function request(forward, token = '') {
  return {
    method: 'GET', url: '/api/v1/' + forward,
    query: { forward },
    headers: token ? { 'x-vercel-oidc-token': token } : {},
  };
}

test('D2 rejects every non-identity endpoint before network', async () => {
  const forbidden = [
    'profile', 'profile/locale', 'account/modules', 'logs',
    'patients', 'consent', 'cgm', 'sync', 'companion/chat',
    'auth/password/reset/request',
  ];
  let outbound = 0;
  const fetchImpl = async () => {
    outbound++;
    throw Error('must not run');
  };
  for (const path of forbidden) {
    const res = response();
    await proxy(request(path, 'OIDC_TEST'), res, { env, fetchImpl });
    assert.equal(res.statusCode, 404, path);
    assert.match(res.body, /identity-only/);
  }
  assert.equal(outbound, 0);
});

test('D2 identity route requires trusted OIDC, not client supplied API', async () => {
  let outbound = 0;
  const fetchImpl = async () => { outbound++; throw Error('no'); };
  const res = response();
  await proxy(request('auth/login'), res, { env, fetchImpl });
  assert.equal(res.statusCode, 503);
  assert.equal(outbound, 0);
});

test('D2 allowlisted auth only targets immutable synthetic API', async () => {
  const targets = [];
  const fetchImpl = async (url, opts) => {
    targets.push({ url, opts });
    return {
      status: 200, headers: new Headers({ 'content-type': 'application/json' }),
      arrayBuffer: async () => Buffer.from('{"ok":true}'),
    };
  };
  for (const path of ['auth/login', 'auth/register', 'auth/logout']) {
    const res = response();
    await proxy(request(path, 'OIDC_TEST'), res, { env, fetchImpl });
    assert.equal(res.statusCode, 200, path);
  }
  assert.equal(targets.length, 3);
  for (const [i, path] of ['auth/login', 'auth/register', 'auth/logout'].entries()) {
    assert.equal(new URL(targets[i].url).pathname, '/api/v1/' + path);
    assert.match(new URL(targets[i].url).hostname, /^iamina-certified-m3fxatyv1-/);
    assert.equal(targets[i].opts.headers.get('x-vercel-trusted-oidc-idp-token'), 'OIDC_TEST');
  }
});

test('D2 denies non-preview or wrong frontend project', async () => {
  for (const extra of [{VERCEL_ENV:'production'}, {VERCEL_PROJECT_ID:'other'}]) {
    const res = response();
    await proxy(request('auth/login','OIDC'), res, {
      env: {...env,...extra},
      fetchImpl: async()=>{throw Error('no');},
    });
    assert.equal(res.statusCode, 404);
  }
});
