import test from 'node:test';
import assert from 'node:assert/strict';
import { Readable } from 'node:stream';
import { proxy } from '../../api/preview-proxy.js';

const host = 'iamina-review-git-cert-d7-we-5e65d5-achraf-benmoussa-s-projects.vercel.app';
const backend = 'https://iamina-certified-i8v18ds1r-achraf-benmoussa-s-projects.vercel.app';
Object.assign(process.env, {
  VERCEL_ENV: 'preview', VERCEL_PROJECT_ID: 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  VERCEL_GIT_COMMIT_REF: 'cert/d7-web-fue-preview-20261029',
  IAMINA_REVIEW_PREVIEW_API_BASE_URL: backend,
});
function request(path, method = 'GET', origin) {
  const req = Readable.from([]);
  req.url = path; req.method = method;
  req.headers = {host, ...(origin ? {origin} : {})};
  return req;
}
function response() {
  return {
    statusCode: 200, headers: {},
    setHeader(name, value) {this.headers[name.toLowerCase()] = value; return this;},
    status(code) {this.statusCode = code; return this;},
    end() {return this;},
  };
}
test('GET login/logout gets local 405 without upstream or token', async () => {
  const saved = global.fetch;
  let calls = 0;
  global.fetch = async () => {calls++; throw Error('unexpected upstream');};
  try {
    for (const path of ['/api/v1/auth/login', '/api/v1/auth/logout']) {
      const res = response();
      await proxy(request(path), res, () => {throw Error('unexpected token');});
      assert.equal(res.statusCode, 405);
      assert.equal(res.headers.allow, 'POST');
    }
    assert.equal(calls, 0);
  } finally {global.fetch = saved;}
});
test('synthetic POST preserves upstream JSON 401 without forwarding cookies', async () => {
  const saved = global.fetch;
  let calls = 0;
  global.fetch = async (url, options) => {
    calls++;
    assert.equal(url, backend + '/api/v1/auth/login');
    assert.equal(options.method, 'POST');
    assert.equal(options.headers.get('cookie'), null);
    assert.equal(options.headers.get('x-vercel-trusted-oidc-idp-token'), 'test-token');
    return new Response(null, {status: 401, headers: {'content-type': 'application/json'}});
  };
  try {
    const res = response();
    await proxy(request('/api/v1/auth/login', 'POST', 'https://' + host), res, async () => 'test-token');
    assert.equal(calls, 1);
    assert.equal(res.statusCode, 401);
    assert.equal(res.headers['content-type'], 'application/json');
  } finally {global.fetch = saved;}
});
test('upstream HTML protection page stays a 502, not a login success', async () => {
  const saved = global.fetch, savedWarn = console.warn;
  const logs = [];
  global.fetch = async () => new Response('<html>protected</html>', {status: 200, headers: {'content-type': 'text/html'}});
  console.warn = (...args) => logs.push(args);
  try {
    const res = response();
    await proxy(request('/api/v1/auth/login', 'POST', 'https://' + host), res, async () => 'test-token');
    assert.equal(res.statusCode, 502);
    assert.deepEqual(logs[0], ['d7_qa_proxy_upstream_non_api', 200]);
  } finally {global.fetch = saved; console.warn = savedWarn;}
});
test('unlisted routes and cross-origin POST fail closed', async () => {
  let res = response();
  await proxy(request('/api/v1/patient/data'), res, () => {throw Error('unexpected token');});
  assert.equal(res.statusCode, 404);
  res = response();
  await proxy(request('/api/v1/auth/login', 'POST', 'https://untrusted.invalid'), res, () => {throw Error('unexpected token');});
  assert.equal(res.statusCode, 403);
});
