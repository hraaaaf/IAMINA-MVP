import test from 'node:test';
import assert from 'node:assert/strict';
import handler, { safePath, requestPath, previewOnlyAndSameOrigin } from '../../frontend/api/preview-proxy.js';

const envKeys = [
  'VERCEL_ENV','VERCEL_PROJECT_ID','IAMINA_REVIEW_PREVIEW_API_BASE_URL',
  'IAMINA_W01_API_PROTECTION_BYPASS'
];
const origin = 'https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app';
const apiOrigin = 'https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app';
function envSet() {
  process.env.VERCEL_ENV = 'preview';
  process.env.VERCEL_PROJECT_ID = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
  process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL = apiOrigin;
  process.env.IAMINA_W01_API_PROTECTION_BYPASS = 'a'.repeat(32);
}
function req(path='health', opts={}) {
  return {
    method: opts.method || 'GET',
    url: '/api/preview-proxy?path=' + path,
    query: {path},
    headers: {'host':new URL(origin).host, ...opts.headers},
  };
}
function res() {
  return {
    statusCode: 200, headers: {}, headersSent: false,
    setHeader(k,v) { this.headers[k.toLowerCase()] = v; return this; },
    status(v) { this.statusCode = v; return this; },
    end() { this.headersSent = true; return this; },
  };
}
async function withEnv(fn) {
  const before = Object.fromEntries(envKeys.map(k => [k,process.env[k]]));
  const oldFetch = globalThis.fetch;
  try { envSet(); await fn(); } finally {
    globalThis.fetch = oldFetch;
    for (const k of envKeys) {
      if (before[k] === undefined) delete process.env[k];
      else process.env[k] = before[k];
    }
  }
}
test('safe fixed origin and path rejects traversals, invalid url segments',()=>{
  for (const bad of ['','/admin','../admin','foo//bar','%2e%2e','foo%2fbar','foo\\bar','https:']) {
    assert.equal(safePath(bad),false,bad);
  }
  assert.equal(safePath('auth/login'),true);
  assert.deepEqual(requestPath(req('health')), {path:'health',search:''});
});
test('production and cross-origin requests are rejected before backend',()=>{
  envSet();
  process.env.VERCEL_ENV = 'production';
  assert.equal(previewOnlyAndSameOrigin(req()),404);
  process.env.VERCEL_ENV = 'preview';
  assert.equal(previewOnlyAndSameOrigin(req('health',{headers:{origin:'https://evil.example'}})),403);
  assert.equal(previewOnlyAndSameOrigin(req('health',{method:'POST'})),403);
});
test('secret missing returns 503 before any egress',async()=>{
  await withEnv(async()=>{
    delete process.env.IAMINA_W01_API_PROTECTION_BYPASS;
    globalThis.fetch = async()=>{ throw Error('Unexpected egress'); };
    const out=res();
    await handler(req(),out);
    assert.equal(out.statusCode,503);
  });
});
test('health proxy sends fixed-host server secret, excludes client cookies and cannot follow redirects',async()=>{
  await withEnv(async()=>{
    globalThis.fetch=async(url,init)=>{
      assert.equal(url,apiOrigin+'/api/v1/health');
      assert.equal(init.redirect,'manual');
      assert.equal(init.headers.get('x-vercel-protection-bypass'),'a'.repeat(32));
      assert.equal(init.headers.get('cookie'),null);
      assert.equal(init.headers.get('x-vercel-protection-bypass-client'),null);
      return {status:302,body:{cancel:async()=>{}},headers:new Headers({location:'https://evil.example'})};
    };
    const out=res();
    await handler(req('health',{headers:{cookie:'SSO=private','x-vercel-protection-bypass-client':'ATTACK'}}),out);
    assert.equal(out.statusCode,502);
    assert.equal(out.headers['cache-control'],'private, no-store, max-age=0');
    assert.equal(out.headers['set-cookie'],undefined);
  });
});
test('production refuses to run even when secret and browser cookies exist',async()=>{
  await withEnv(async()=>{
    process.env.VERCEL_ENV='production';
    globalThis.fetch=async()=>{throw Error('Unexpected egress');};
    const out=res(); await handler(req(),out);
    assert.equal(out.statusCode,404);
  });
});
test('invalid cross-origin origin, body-size, path and methods fail closed',async()=>{
  await withEnv(async()=>{
    globalThis.fetch=async()=>{ throw Error('Unexpected egress'); };
    for(const [r,status] of [
      [req('health',{headers:{origin:'https://attacker.example'}}),403],
      [req('health',{headers:{'content-length':'99999999'}}),413],
      [req('../admin'),400],
      [req('health',{method:'OPTIONS'}),405],
    ]) {
      const out=res(); await handler(r,out);
      assert.equal(out.statusCode,status);
    }
  });
});
