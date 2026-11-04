'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { Readable } = require('node:stream');
const proxy = require('./index.js');
const ENV = {
  VERCEL_ENV: 'preview',
  VERCEL_PROJECT_ID: 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  IAMINA_REVIEW_PREVIEW_API_BASE_URL: 'https://iamina-certified-hmmwtj2iu-achraf-benmoussa-s-projects.vercel.app',
};
function response() {
  return {
    statusCode: 200,
    headers: {},
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    end(bytes) { this.body = bytes; this.done = true; },
  };
}
function request(path='auth/login', token='web-oidc') {
  const req = Readable.from([Buffer.from('{"email":"synthetic@example.invalid","password":"synthetic"}')]);
  req.url = '/api/index.js?forward=' + path;
  req.method = 'POST';
  req.query = { forward: path };
  req.headers = {
    'x-vercel-oidc-token': token,
    'content-type': 'application/json',
    authorization: 'Bearer synthetic-test',
    cookie: 'never-forwarded',
    'x-vercel-protection-bypass': 'must-not-forward',
  };
  return req;
}
test('same-origin preview proxy targets only immutable synthetic API with short-lived OIDC and no browser cookies', async () => {
  const res = response(); let didFetch = false;
  await proxy(request(), res, { env: ENV, fetchImpl: async (url, opts) => {
    didFetch = true;
    assert.equal(url, `${ENV.IAMINA_REVIEW_PREVIEW_API_BASE_URL}/api/v1/auth/login`);
    assert.equal(opts.headers.get('x-vercel-trusted-oidc-idp-token'), 'web-oidc');
    assert.equal(opts.headers.get('cookie'), null);
    assert.equal(opts.headers.get('x-vercel-protection-bypass'), null);
    assert.equal(opts.headers.get('authorization'), 'Bearer synthetic-test');
    assert.equal(opts.redirect, 'manual');
    assert.equal(opts.duplex, 'half');
    return new Response('{"detail":"Authenticated"}', {status: 200, headers: {'content-type':'application/json'}});
  }});
  assert.equal(didFetch, true); assert.equal(res.statusCode, 200);
  assert.equal(String(res.body), '{"detail":"Authenticated"}');
});
test('fails closed in Production or wrong Vercel project', async () => {
  for (const env of [{...ENV, VERCEL_ENV:'production'}, {...ENV, VERCEL_PROJECT_ID:'other'}]) {
    const r=response();await proxy(request(),r,{env,fetchImpl:()=>{throw Error('Must not fetch');}});
    assert.equal(r.statusCode,404);
  }
});
test('fails closed for missing OIDC, invalid origin, traversal, and upstream redirect', async () => {
  for (const [req,env,expected] of [
    [request('auth/login',''),ENV,503],
    [request(),{...ENV,IAMINA_REVIEW_PREVIEW_API_BASE_URL:'https://iamina-certified.vercel.app'},503],
    [request('../auth/login'),ENV,400],
    [request('https://malicious.example'),ENV,400],
  ]) {
    const r=response();await proxy(req,r,{env,fetchImpl:()=>{throw Error('Must not fetch');}});
    assert.equal(r.statusCode,expected);
  }
  const r=response(); await proxy(request(),r,{env:ENV,fetchImpl:async()=>new Response(null,{status:302,headers:{location:'https://other.example/'}})});
  assert.equal(r.statusCode,502);assert.equal(r.headers.location,undefined);
});
test('forwards real backend authentication denial (401) without misclassifying status', async () => {
  const r=response();await proxy(request(),r,{env:ENV,fetchImpl:async()=>new Response('{"detail":"Invalid authentication credential"}',{status:401,headers:{'content-type':'application/json'}})});
  assert.equal(r.statusCode,401);
});
test('preserves query parameters but removes proxy-only path parameter', async () => {
  const q=request('measurements');q.method='GET';q.url='/api/index.js?forward=measurements&page=2';
  const r=response();await proxy(q,r,{env:ENV,fetchImpl:async url=>{
    assert.equal(url,ENV.IAMINA_REVIEW_PREVIEW_API_BASE_URL+'/api/v1/measurements?page=2');
    return new Response('[]',{status:200});
  }});
  assert.equal(r.statusCode,200);
});
