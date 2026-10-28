import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Readable, Writable } from 'node:stream';
import { proxy, safePath, requestPath, previewOnlyAndSameOrigin, resolvePreviewApiOrigin } from '../../frontend/api/preview-proxy.js';

const envKeys = [
  'VERCEL_ENV','VERCEL_PROJECT_ID','IAMINA_REVIEW_PREVIEW_API_BASE_URL',
  'VERCEL_OIDC_TOKEN','VERCEL_GIT_COMMIT_REF','VERCEL_GIT_COMMIT_SHA',
  'IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN',
  'IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA'
];
const origin = 'https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app';
const apiOrigin = 'https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app';
function envSet() {
  process.env.VERCEL_ENV = 'preview';
  process.env.VERCEL_PROJECT_ID = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
  process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL = apiOrigin;
  process.env.VERCEL_OIDC_TOKEN = 'a.test.token';
  // No test inadvertently activates synthetic remote auth by inheritance.
  delete process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN;
  delete process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA;
  delete process.env.VERCEL_GIT_COMMIT_REF;
  delete process.env.VERCEL_GIT_COMMIT_SHA;
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
test('W01 API Preview pin permits only immutable protected-project deployment URL', async () => {
  await withEnv(async () => {
    assert.equal(resolvePreviewApiOrigin(), apiOrigin);
    const nextDeployment =
      'https://iamina-certified-w01synthetic9-achraf-benmoussa-s-projects.vercel.app';
    process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL = nextDeployment;
    assert.equal(resolvePreviewApiOrigin(), nextDeployment);
    let observed = 0;
    globalThis.fetch = async url => {
      observed++;
      assert.equal(url, nextDeployment + '/api/v1/health');
      return new Response('{"status":"ok"}', {status:200,
        headers:{'content-type':'application/json'}});
    };
    const response = streamingResponse();
    await proxy(req('health'), response, async()=> 'synthetic-oidc');
    assert.equal(response.statusCode, 200);
    assert.equal(observed, 1);
  });
});

test('W01 BFF refuses Production alias, cross-project and malformed Preview targets', async () => {
  await withEnv(async () => {
    const bad = [
      '',
      'https://iamina-certified.vercel.app',
      'https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app',
      'https://another-project-a-achraf-benmoussa-s-projects.vercel.app',
      'http://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app/',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app/path',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app?test=1',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app#x',
      'https://u:p@iamina-certified-a-achraf-benmoussa-s-projects.vercel.app',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app:444',
      'https://iamina-certified-a-achraf-benmoussa-s-projects.vercel.app.evil.test',
    ];
    let requests = 0;
    let oidc = 0;
    globalThis.fetch = async () => {requests++; throw Error('forbidden network');};
    for (const invalid of bad) {
      process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL = invalid;
      assert.equal(resolvePreviewApiOrigin(), null, invalid);
      const response = res();
      await proxy(req('health'), response, async () => {oidc++;return 'synthetic-oidc';});
      assert.equal(response.statusCode, 503, invalid);
    }
    assert.equal(requests, 0);
    assert.equal(oidc, 0);
  });
});


test('W01 visitor country suggestion uses Web edge geolocation, not API egress', async () => {
  await withEnv(async () => {
    let upstream = 0;
    globalThis.fetch = async () => { upstream++; throw Error('country must remain at Web edge'); };
    for (const [raw,code,source] of [
      ['MA','MA','ip_estimate'],['FR','FR','ip_estimate'],
      ['ZZ',null,'unavailable'],['ma',null,'unavailable'],
      ['FR,MA',null,'unavailable'],['M',null,'unavailable'],
      ['',null,'unavailable'],[undefined,null,'unavailable'],
    ]) {
      const headers = raw === undefined ? {} : {'x-vercel-ip-country':raw};
      const output = streamingResponse();
      await proxy(req('country/suggestion',{headers}),output,
        async()=>{throw Error('public country must not acquire OIDC');});
      assert.equal(output.statusCode,200);
      assert.equal(output.headers['cache-control'],'private, no-store, max-age=0');
      assert.equal(output.headers['set-cookie'],undefined);
      assert.deepEqual(JSON.parse(output.text()),{country_code:code,source});
    }
    // Even when the protected API's Preview URL is unconfigured, public
    // country is resolved on the Web edge, not through a clinical backend.
    delete process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL;
    const offline = streamingResponse();
    await proxy(req('country/suggestion',{headers:{'x-vercel-ip-country':'MA'}}),
      offline, async()=>{throw Error('must not invoke OIDC');});
    assert.equal(offline.statusCode, 200);
    assert.deepEqual(JSON.parse(offline.text()),
      {country_code:'MA',source:'ip_estimate'});
    assert.equal(upstream,0);
  });
});

test('W01 coarse country is Preview-only; clinical routes still need OIDC', async () => {
  await withEnv(async () => {
    let upstream=0;
    globalThis.fetch=async()=>{upstream++;throw Error('forbidden egress');};
    const cases=[
      [req('country/suggestion',{headers:{origin:'https://attacker.invalid',
        'x-vercel-ip-country':'MA'}}),403],
      [req('country/suggestion',{method:'POST',headers:{
        'x-vercel-ip-country':'MA'}}),403],
    ];
    for (const [request,status] of cases) {
      const output=res();
      await proxy(request,output,async()=> 'synthetic-oidc');
      assert.equal(output.statusCode,status);
    }
    const withoutOidc=streamingResponse();
    await proxy(req('country/suggestion',{headers:{'x-vercel-ip-country':'MA'}}),
      withoutOidc, async()=> null);
    assert.equal(withoutOidc.statusCode,200);
    assert.deepEqual(JSON.parse(withoutOidc.text()),
      {country_code:'MA',source:'ip_estimate'});

    const protectedHealth=res();
    await proxy(req('health'), protectedHealth, async()=> null);
    assert.equal(protectedHealth.statusCode,503);

    // Query-bearing or non-GET variants cannot use the public local handler.
    for (const request of [
      {...req('country/suggestion'),url:'/api/v1/country/suggestion?x=1'},
      req('country/suggestion',{method:'HEAD'}),
      req('country/suggestion',{method:'POST',headers:{origin}}),
    ]) {
      const result=res();
      await proxy(request,result,async()=>null);
      assert.equal(result.statusCode,503);
    }
    process.env.VERCEL_ENV='production';
    const prod=res();
    await proxy(req('country/suggestion',{headers:{'x-vercel-ip-country':'MA'}}),
      prod, async()=> 'synthetic-oidc');
    assert.equal(prod.statusCode,404);
    assert.equal(upstream,0);
  });
});

test('safe fixed origin and path rejects traversals, invalid url segments',()=>{
  for (const bad of ['','/admin','../admin','foo//bar','%2e%2e','foo%2fbar','foo\\bar','https:']) {
    assert.equal(safePath(bad),false,bad);
  }
  assert.equal(safePath('auth/login'),true);
  assert.deepEqual(requestPath(req('health')), {path:'health',search:''});
});
test('slash-terminated Django routes pass BFF without weakening path checks', async () => {
  for (const good of ['documents/', 'kpis/', 'personal-response/']) {
    assert.equal(safePath(good), true, good);
  }
  for (const bad of ['/', 'documents//', 'documents//ingest',
    'documents/../', 'documents/%2e%2e/', 'documents/./']) {
    assert.equal(safePath(bad), false, bad);
  }
  assert.deepEqual(requestPath(req('documents/')), {path:'documents/',search:''});
  assert.deepEqual(requestPath({
    ...req('documents/'), url:'/api/v1/documents/?limit=20',
  }), {path:'documents/',search:'?limit=20'});

  await withEnv(async () => {
    const paths = [
      '/api/v1/documents/?limit=20',
      '/api/v1/kpis/?days=14',
      '/api/v1/personal-response/?days=7',
    ];
    let calls = 0;
    globalThis.fetch = async (url, init) => {
      assert.equal(url, apiOrigin + paths[calls]);
      assert.equal(init.headers.get('authorization'), 'Bearer fixture-A');
      assert.equal(init.headers.get('cookie'), null);
      calls++;
      return new Response(JSON.stringify({ok:true}), {
        status:200, headers:{'content-type':'application/json'},
      });
    };
    for (const url of paths) {
      const incoming = {
        ...req('health', {headers:{
          authorization:'Bearer fixture-A',
          cookie:'_vercel_jwt=not-forwarded',
        }}),
        url,
      };
      const outgoing = streamingResponse();
      await proxy(incoming, outgoing, async () => 'synthetic-oidc');
      assert.equal(outgoing.statusCode, 200);
      assert.equal(JSON.parse(outgoing.text()).ok, true);
    }
    assert.equal(calls, paths.length);
  });
});

test('production and cross-origin requests are rejected before backend',()=>{
  envSet();
  process.env.VERCEL_ENV = 'production';
  assert.equal(previewOnlyAndSameOrigin(req()),404);
  process.env.VERCEL_ENV = 'preview';
  assert.equal(previewOnlyAndSameOrigin(req('health',{headers:{origin:'https://evil.example'}})),403);
  assert.equal(previewOnlyAndSameOrigin(req('health',{method:'POST'})),403);
});
test('Preview forbidden POST returns only classification, preserves rejection and never reaches API', async () => {
  await withEnv(async () => {
    let upstream = 0;
    globalThis.fetch = async () => { upstream++; throw Error('No upstream on guard denial'); };
    for (const [request, expectedReason, expectedSite] of [
      [req('auth/register',{method:'POST',headers:{'sec-fetch-site':'same-site'}}),'origin-absent','same-site'],
      [req('auth/register',{method:'POST',headers:{origin:'https://attacker.example','sec-fetch-site':'cross-site'}}),'origin-mismatch','cross-site'],
      [req('auth/register',{method:'POST',headers:{origin,'host':'attacker.example'}}),'host-rejected','unavailable'],
    ]) {
      const output = res();
      await proxy(request, output, async () => 'synthetic-oidc');
      assert.equal(output.statusCode, 403);
      assert.equal(output.headers['x-iamina-preview-guard'], expectedReason);
      assert.equal(output.headers['x-iamina-fetch-site'], expectedSite);
      assert.equal(output.headers['access-control-allow-origin'], undefined);
      assert.equal(output.headers['cache-control'], 'private, no-store, max-age=0');
      assert.doesNotMatch(JSON.stringify(output.headers), /attacker\.example|Bearer|token/);
    }
    assert.equal(upstream, 0);
  });
});

test('hosted browser same-origin POST can omit Origin, but never bypasses OIDC or forwards cookies', async () => {
  await withEnv(async () => {
    const request = req('auth/register', {method:'POST', headers:{
      'sec-fetch-site':'same-origin', 'content-type':'application/json',
      cookie:'_vercel_jwt=private-sso-cookie',
    }});
    assert.equal(previewOnlyAndSameOrigin(request), 0);

    // Fail closed when Origin is missing and Fetch Metadata is weaker or absent.
    for (const site of [undefined, 'same-site', 'cross-site', 'none', '',
      'same-origin, cross-site']) {
      const headers = site === undefined ? {} : {'sec-fetch-site':site};
      assert.equal(previewOnlyAndSameOrigin(req('auth/register',{
        method:'POST', headers,
      })), 403, 'site=' + String(site));
    }
    // Forged Origin cannot be rescued by apparently same-origin metadata.
    assert.equal(previewOnlyAndSameOrigin(req('auth/register',{method:'POST',headers:{
      origin:'https://attacker.invalid', 'sec-fetch-site':'same-origin',
    }})), 403);

    const body = Buffer.from('{}');
    const incoming = Readable.from([body]);
    Object.assign(incoming, request);
    let calls = 0;
    globalThis.fetch = async (url, options) => {
      calls++;
      assert.equal(url, apiOrigin + '/api/v1/auth/register');
      assert.equal(options.headers.get('x-vercel-trusted-oidc-idp-token'),'synthetic-oidc');
      assert.equal(options.headers.get('origin'),null);
      assert.equal(options.headers.get('cookie'),null);
      assert.equal(options.headers.get('sec-fetch-site'),null);
      assert.deepEqual(options.body,body);
      return new Response(JSON.stringify({detail:'Invalid synthetic payload'}),{
        status:422,headers:{'content-type':'application/json'},
      });
    };
    const output = streamingResponse();
    await proxy(incoming,output,async()=> 'synthetic-oidc');
    assert.equal(calls,1);
    assert.equal(output.statusCode,422);
    assert.equal(output.headers['x-iamina-preview-guard'],undefined);
    assert.equal(JSON.parse(output.text()).detail,'Invalid synthetic payload');

    // Same accepted browser request still cannot reach upstream without OIDC.
    globalThis.fetch=async()=>{throw Error('No egress without OIDC');};
    const denied = res();
    await proxy(req('auth/register',{method:'POST',headers:{
      'sec-fetch-site':'same-origin',
    }}),denied,async()=>null);
    assert.equal(denied.statusCode,503);
  });
});


test('synthetic remote Preview auth is OFF without exact opt-in', async () => {
  await withEnv(async () => {
    let calls = 0;
    globalThis.fetch = async (url) => {
      calls++;
      assert.equal(url, apiOrigin + '/api/v1/auth/login');
      return new Response(JSON.stringify({detail:'synthetic invalid credentials'}),{
        status:401,headers:{'content-type':'application/json'},
      });
    };
    const input = Readable.from([Buffer.from(JSON.stringify({
      email:'legacy@example.test',password:'fixture',
    }))]);
    Object.assign(input,req('auth/login',{method:'POST',headers:{origin}}));
    const output=streamingResponse();
    await proxy(input,output,async()=>'synthetic-oidc');
    assert.equal(output.statusCode,401);
    assert.equal(calls,1,'no identity preflight outside explicit mode');
  });
});

test('opt-in synthetic auth fails closed on wrong Git branch before OIDC or egress', async () => {
  await withEnv(async () => {
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='main';
    let calls=0;
    globalThis.fetch=async()=>{calls++;throw Error('no egress');};
    const output=res();
    await proxy(req('health'),output,async()=>{throw Error('no OIDC');});
    assert.equal(output.statusCode,503);
    assert.equal(calls,0);
    process.env.VERCEL_ENV='production';
    const production=res();
    await proxy(req('health'),production,async()=>{throw Error('no OIDC');});
    assert.equal(production.statusCode,404);
  });
});

test('synthetic mode rejects absent or wrong SHA before OIDC and API egress', async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    let upstream=0;
    globalThis.fetch=async()=>{upstream++;throw Error('must not egress');};
    for(const pinned of [undefined,'b'.repeat(40),'invalid-sha']){
      if(pinned===undefined)delete process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA;
      else process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA=pinned;
      const output=res();
      await proxy(req('health'),output,async()=>{throw Error('no OIDC');});
      assert.equal(output.statusCode,503,String(pinned));
    }
    assert.equal(upstream,0);
  });
});

test('synthetic auth rejects real email and Firebase / reset before any upstream egress', async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    let calls=0;
    globalThis.fetch=async()=>{calls++;throw Error('must not egress');};
    for (const email of [
      'patient@gmail.com','someone@example.com','foo@example.invalid.evil',
      'foo+real@example.invalid','REAL@example.invalid','',
    ]) {
      const input=Readable.from([Buffer.from(JSON.stringify({email,password:'synthetic'}))]);
      Object.assign(input,req('auth/register',{method:'POST',headers:{
        origin,'content-type':'application/json',
      }}));
      const output=res();
      await proxy(input,output,async()=>'synthetic-oidc');
      assert.equal(output.statusCode,403,email);
    }
    for (const path of ['auth/firebase','auth/firebase/','auth/password','auth/password/','auth/password/reset/request','auth/password/reset/confirm']) {
      const output=res();
      await proxy(req(path,{method:'POST',headers:{origin}}),output,async()=>'synthetic-oidc');
      assert.equal(output.statusCode,403,path);
    }
    for (const payload of [
      {email:'w01-synthetic@example.invalid',password:'synthetic',first_name:'Real Patient'},
      {email:'w01-synthetic@example.invalid',password:'synthetic',last_name:'Personal Name'},
      {email:'w01-synthetic@example.invalid',password:'synthetic',patient_note:'patient data'},
    ]) {
      const body=Readable.from([Buffer.from(JSON.stringify(payload))]);
      Object.assign(body,req('auth/register',{method:'POST',headers:{origin}}));
      const out=res();
      await proxy(body,out,async()=>'synthetic-oidc');
      assert.equal(out.statusCode,403,'untrusted registration fields forbidden');
    }
    assert.equal(calls,0);
  });
});

test('synthetic signup fails closed if any Neon identity field changes', async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    const body=Buffer.from(JSON.stringify({
      email:'w01-synthetic@example.invalid',password:'not-a-real-password',
    }));
    const input=Readable.from([body]);
    Object.assign(input,req('auth/register',{method:'POST',headers:{origin}}));
    let calls=0;
    globalThis.fetch=async(url,opts)=>{
      calls++;
      assert.equal(url,apiOrigin+'/api/v1/ops/preview-db-identity');
      assert.equal(opts.headers.get('x-vercel-trusted-oidc-idp-token'),'synthetic-oidc');
      return new Response(JSON.stringify({
        database_name:'iamina925_empty',role_name:'iamina_preview_app',
        neon_project_id:'noisy-truth-00115950',
        neon_branch_id:'WRONG_BRANCH',
      }),{status:200,headers:{'content-type':'application/json'}});
    };
    const output=res();
    await proxy(input,output,async()=>'synthetic-oidc');
    assert.equal(output.statusCode,503);
    assert.equal(calls,1,'must never attempt register if identity differs');
    assert.equal(output.headers['cache-control'],'private, no-store, max-age=0');
  });
});


test('synthetic D2 and logout fail closed on changed Neon before patient egress',async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    let calls=0;
    globalThis.fetch=async(url)=>{
      calls++;
      assert.equal(url,apiOrigin+'/api/v1/ops/preview-db-identity');
      return new Response(JSON.stringify({
        database_name:'WRONG_DB',role_name:'iamina_preview_app',
        neon_project_id:'noisy-truth-00115950',
        neon_branch_id:'br-sweet-frog-b9ok6ptp',
      }),{status:200,headers:{'content-type':'application/json'}});
    };
    for(const [path,opts] of [
      ['account/notification-preview-consent',{method:'GET'}],
      ['auth/me',{method:'GET'}],
      ['auth/logout',{method:'POST',headers:{origin}}],
    ]){
      const incoming=req(path,opts);
      if(opts.method==='POST'){
        // Empty request stream is legitimate for logout.
        Object.assign(Readable.from([]),incoming);
      }
      const input=opts.method==='POST' ? Object.assign(Readable.from([]),incoming) : incoming;
      const out=res();
      await proxy(input,out,async()=>'synthetic-oidc');
      assert.equal(out.statusCode,503,path);
    }
    assert.equal(calls,3,'only identity preflight requests, never clinical egress');
  });
});

test('synthetic signup with exact Neon identity forwards only after OIDC and body checks', async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    const payload=Buffer.from(JSON.stringify({
      email:'w01-synthetic@example.invalid',password:'not-a-real-password',
    }));
    const input=Readable.from([payload]);
    Object.assign(input,req('auth/register',{method:'POST',headers:{
      origin,'content-type':'application/json',cookie:'SSO=no-egress',
    }}));
    let calls=0;
    globalThis.fetch=async(url,opts)=>{
      calls++;
      if(calls===1){
        assert.equal(url,apiOrigin+'/api/v1/ops/preview-db-identity');
        assert.equal(opts.method,'GET');
        assert.equal(opts.headers.get('cookie'),null);
        return new Response(JSON.stringify({
          database_name:'iamina925_empty',role_name:'iamina_preview_app',
          neon_project_id:'noisy-truth-00115950',
          neon_branch_id:'br-sweet-frog-b9ok6ptp',
        }),{status:200,headers:{'content-type':'application/json'}});
      }
      assert.equal(url,apiOrigin+'/api/v1/auth/register');
      assert.equal(opts.headers.get('cookie'),null);
      assert.equal(opts.headers.get('origin'),null);
      assert.equal(opts.headers.get('x-vercel-trusted-oidc-idp-token'),'synthetic-oidc');
      assert.deepEqual(opts.body,payload);
      return new Response(JSON.stringify({synthetic:true}),{
        status:200,headers:{'content-type':'application/json'},
      });
    };
    const out=streamingResponse();
    await proxy(input,out,async()=>'synthetic-oidc');
    assert.equal(out.statusCode,200);
    assert.equal(JSON.parse(out.text()).synthetic,true);
    assert.equal(calls,2,'identity GET must precede registration POST');
  });
});

test('synthetic mode preserves Django 422 invalid-body preflight after identity proof', async()=>{
  await withEnv(async()=>{
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN='D2_WEB_SYNTHETIC_ONLY_V1';
    process.env.IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_SHA='a'.repeat(40);
    process.env.VERCEL_GIT_COMMIT_REF='integration/w01-d2-preview-only-20261027';
    const input=Readable.from([Buffer.from('{}')]);
    Object.assign(input,req('auth/register',{method:'POST',headers:{
      origin,'content-type':'application/json',
    }}));
    let calls=0;
    globalThis.fetch=async(url)=>{
      calls++;
      if(calls===1){
        assert.equal(url,apiOrigin+'/api/v1/ops/preview-db-identity');
        return new Response(JSON.stringify({
          database_name:'iamina925_empty',role_name:'iamina_preview_app',
          neon_project_id:'noisy-truth-00115950',
          neon_branch_id:'br-sweet-frog-b9ok6ptp',
        }),{status:200,headers:{'content-type':'application/json'}});
      }
      assert.equal(url,apiOrigin+'/api/v1/auth/register');
      return new Response(JSON.stringify({detail:'Invalid body'}),{
        status:422,headers:{'content-type':'application/json'},
      });
    };
    const out=streamingResponse();
    await proxy(input,out,async()=>'synthetic-oidc');
    assert.equal(out.statusCode,422);
    assert.equal(calls,2);
  });
});

test('missing OIDC token returns 503 before any egress',async()=>{
  await withEnv(async()=>{
    delete process.env.VERCEL_OIDC_TOKEN;
    globalThis.fetch = async()=>{ throw Error('Unexpected egress'); };
    const out=res();
    await proxy(req(),out, async()=>process.env.VERCEL_OIDC_TOKEN);
    assert.equal(out.statusCode,503);
  });
});
test('Web password login returns IAMINA bearer but no Django session cookie', async () => {
  await withEnv(async () => {
    const request = Readable.from([Buffer.from(JSON.stringify({
      email:'fixture@example.test', password:'synthetic-only',
    }))]);
    Object.assign(request, req('auth/login', {method:'POST', headers:{
      origin, 'content-type':'application/json',
      cookie:'_vercel_jwt=private-session',
      'x-iamina-stateless-bootstrap':'spoofed',
    }}));
    let calls=0;
    globalThis.fetch = async (url, options) => {
      calls++;
      assert.equal(url, apiOrigin+'/api/v1/auth/login');
      assert.equal(options.headers.get('cookie'), null);
      assert.equal(options.headers.get('origin'), null);
      assert.equal(options.headers.get('x-iamina-stateless-bootstrap'), null);
      assert.equal(options.headers.get('x-vercel-trusted-oidc-idp-token'), 'synthetic-oidc');
      return new Response(JSON.stringify({
        access_token:'iamina.synthetic-bearer',token_type:'Bearer',
      }), {status:200, headers:{
        'content-type':'application/json',
        'set-cookie':'sessionid=django_private; HttpOnly',
        'access-control-allow-origin':'*',
      }});
    };
    const outgoing=streamingResponse();
    await proxy(request,outgoing,async()=> 'synthetic-oidc');
    assert.equal(calls,1);
    assert.equal(outgoing.statusCode,200);
    assert.equal(JSON.parse(outgoing.text()).access_token,'iamina.synthetic-bearer');
    assert.equal(outgoing.headers['set-cookie'],undefined);
    assert.equal(outgoing.headers['access-control-allow-origin'],undefined);
  });
});

test('health proxy forwards short-lived OIDC only, excludes cookies and cannot redirect',async()=>{
  await withEnv(async()=>{
    globalThis.fetch=async(url,init)=>{
      assert.equal(url,apiOrigin+'/api/v1/health');
      assert.equal(init.redirect,'manual');
      assert.equal(init.headers.get('x-vercel-trusted-oidc-idp-token'),'a.test.token');
      assert.equal(init.headers.get('x-vercel-protection-bypass'),null);
      assert.equal(init.headers.get('cookie'),null);
      assert.equal(init.headers.get('x-vercel-protection-bypass-client'),null);
      return {status:302,body:{cancel:async()=>{}},headers:new Headers({location:'https://evil.example'})};
    };
    const out=res();
    await proxy(req('health',{headers:{cookie:'SSO=private','x-vercel-protection-bypass-client':'ATTACK'}}),out, async()=>process.env.VERCEL_OIDC_TOKEN);
    assert.equal(out.statusCode,502);
    assert.equal(out.headers['cache-control'],'private, no-store, max-age=0');
    assert.equal(out.headers['set-cookie'],undefined);
  });
});
test('HTML SSO login cannot masquerade as Django API success',async()=>{
  await withEnv(async()=>{
    globalThis.fetch=async()=>({status:200,headers:new Headers({'content-type':'text/html'}),body:{cancel:async()=>{}}});
    const out=res(); await proxy(req(),out,async()=>'a.test.token');
    assert.equal(out.statusCode,502);
  });
});
test('production refuses to run even when OIDC and browser cookies exist',async()=>{
  await withEnv(async()=>{
    process.env.VERCEL_ENV='production';
    globalThis.fetch=async()=>{throw Error('Unexpected egress');};
    const out=res(); await proxy(req(),out, async()=>process.env.VERCEL_OIDC_TOKEN);
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
      const out=res(); await proxy(r,out, async()=>process.env.VERCEL_OIDC_TOKEN);
      assert.equal(out.statusCode,status);
    }
  });
});

function streamingResponse() {
  const chunks = [];
  const response = new Writable({
    write(chunk, _encoding, callback) {
      chunks.push(Buffer.from(chunk));
      callback();
    },
  });
  response.statusCode = 200;
  response.headers = {};
  response.setHeader = (name, value) => {
    response.headers[name.toLowerCase()] = value;
    return response;
  };
  response.status = (statusCode) => {
    response.statusCode = statusCode;
    return response;
  };
  response.text = () => Buffer.concat(chunks).toString('utf8');
  return response;
}

test('synthetic 200 JSON from Django streams without leaking CORS or Set-Cookie', async () => {
  await withEnv(async () => {
    let upstreamCalls = 0;
    globalThis.fetch = async (url, init) => {
      upstreamCalls += 1;
      assert.equal(url, apiOrigin + '/api/v1/health');
      assert.equal(init.headers.get('x-vercel-trusted-oidc-idp-token'), 'synthetic-oidc');
      assert.equal(init.headers.get('authorization'), 'Bearer synthetic');
      assert.equal(init.headers.get('cookie'), null);
      assert.equal(init.headers.get('origin'), null);
      assert.equal(init.redirect, 'manual');
      return new Response(JSON.stringify({status:'ok',db:'ok'}), {
        status: 200,
        headers: {
          'content-type':'application/json',
          'set-cookie':'sessionid=NEVER_FORWARD',
          'access-control-allow-origin':'*',
          'cache-control':'public, max-age=3600',
        },
      });
    };
    const output = streamingResponse();
    await proxy(req('health', {headers: {
      origin,
      authorization:'Bearer synthetic',
      cookie:'SSO=must_not_forward; sessionid=never_forward',
    }}), output, async () => 'synthetic-oidc');
    assert.equal(upstreamCalls, 1);
    assert.equal(output.statusCode, 200);
    assert.deepEqual(JSON.parse(output.text()), {status:'ok',db:'ok'});
    assert.equal(output.headers['content-type'], 'application/json');
    assert.equal(output.headers['set-cookie'], undefined);
    assert.equal(output.headers['access-control-allow-origin'], undefined);
    assert.equal(output.headers['cache-control'], 'private, no-store, max-age=0');
  });
});

test('Django 401 remains 401, cannot be misreported as 200 health', async () => {
  await withEnv(async () => {
    globalThis.fetch = async () => new Response(
      JSON.stringify({detail:'Unauthorized'}), {
        status: 401,
        headers: {'content-type':'application/json'},
      }
    );
    const output = streamingResponse();
    await proxy(req('profile'), output, async () => 'synthetic-oidc');
    assert.equal(output.statusCode, 401);
    assert.equal(JSON.parse(output.text()).detail, 'Unauthorized');
  });
});

test('host spoof, cross-site state mutation and hostile method never fetch API', async () => {
  await withEnv(async () => {
    let called = 0;
    globalThis.fetch = async () => {called++; throw Error('egress forbidden');};
    const cases = [
      [req('health',{headers:{host:'attacker.example'}}),403],
      [req('health',{headers:{host:'iamina-review.vercel.app'}}),403],
      [req('auth/login',{method:'POST',headers:{origin:'https://attacker.example'}}),403],
      [req('auth/login',{method:'POST'}),403],
      [req('health',{method:'TRACE'}),403], // Origin gate rejects unsafe methods first
    ];
    for (const [request, expected] of cases) {
      const result = res();
      await proxy(request, result, async()=> 'synthetic-oidc');
      assert.equal(result.statusCode, expected);
    }
    assert.equal(called,0);
  });
});


// No Content-Length header can authorize more bytes than the actual cap.
// Reject even chunked requests without Content-Length *before* egress.
test('chunked request above 4 MiB cannot reach protected Django', async () => {
  await withEnv(async () => {
    let calls = 0;
    globalThis.fetch = async () => { calls++; throw Error('unexpected API egress'); };
    const chunks = [Buffer.alloc(3 * 1024 * 1024), Buffer.alloc(2 * 1024 * 1024)];
    const incoming = Readable.from(chunks);
    Object.assign(incoming, req('auth/login', {
      method: 'POST',
      headers: {origin, 'content-type':'application/json'},
    }));
    const output = res();
    await proxy(incoming, output, async () => 'synthetic-oidc');
    assert.equal(output.statusCode, 413);
    assert.equal(calls, 0);
  });
});

test('misleading Content-Length cannot bypass actual stream size', async () => {
  await withEnv(async () => {
    let calls = 0;
    globalThis.fetch = async () => { calls++; throw Error('unexpected API egress'); };
    const incoming = Readable.from([Buffer.alloc(4 * 1024 * 1024 + 1)]);
    Object.assign(incoming, req('auth/login', {
      method:'POST',
      headers: {origin, 'content-type':'application/json', 'content-length':'1'},
    }));
    const output=res();
    await proxy(incoming, output, async () => 'synthetic-oidc');
    assert.equal(output.statusCode, 413);
    assert.equal(calls, 0);
  });
});

test('small POST forwards exact bytes and Bearer without browser SSO cookies',async()=>{
  await withEnv(async()=>{
    const body = Buffer.from(JSON.stringify({event:'synthetic'}));
    const incoming = Readable.from([body]);
    Object.assign(incoming, req('auth/login', {
      method:'POST',
      headers:{origin,'content-type':'application/json',authorization:'Bearer synthetic',cookie:'_vercel_jwt=do_not_pass'},
    }));
    let calls=0;
    globalThis.fetch = async(url,opts)=>{
      calls++;
      assert.equal(url,apiOrigin+'/api/v1/auth/login');
      assert.deepEqual(opts.body,body);
      assert.equal(opts.headers.get('authorization'),'Bearer synthetic');
      assert.equal(opts.headers.get('cookie'),null);
      return new Response(JSON.stringify({ok:true}),{status:200,headers:{'content-type':'application/json'}});
    };
    const output=streamingResponse();
    await proxy(incoming,output,async()=> 'synthetic-oidc');
    assert.equal(calls,1);
    assert.equal(output.statusCode,200);
    assert.equal(JSON.parse(output.text()).ok,true);
  });
});

test('synthetic Django 403 is preserved and does not expose upstream session cookies', async () => {
  await withEnv(async () => {
    globalThis.fetch = async () => new Response(
      JSON.stringify({detail:'Forbidden'}),
      {status:403,headers:{'content-type':'application/json','set-cookie':'sessionid=secret'}}
    );
    const output = streamingResponse();
    await proxy(req('account/consent',{headers:{authorization:'Bearer synthetic'}}),
      output,async()=> 'synthetic-oidc');
    assert.equal(output.statusCode,403);
    assert.equal(output.headers['set-cookie'],undefined);
    assert.equal(JSON.parse(output.text()).detail,'Forbidden');
  });
});

test('synthetic bearer A-B-A forwarding never inherits a browser SSO cookie', async () => {
  await withEnv(async () => {
    const users={'Bearer fixture-A':'A','Bearer fixture-B':'B'};
    globalThis.fetch=async (_url, init) => {
      assert.equal(init.headers.get('cookie'),null);
      assert.equal(init.headers.get('x-csrftoken'),null);
      const who=users[init.headers.get('authorization')];
      return new Response(JSON.stringify(who?{patient:who}:{detail:'Unauthorized'}), {
        status:who?200:401,headers:{'content-type':'application/json'}
      });
    };
    for (const [credential,who] of [
      ['Bearer fixture-A','A'],['Bearer fixture-B','B'],['Bearer fixture-A','A'],
    ]) {
      const output=streamingResponse();
      await proxy(req('profile',{headers:{
        authorization:credential,cookie:'_vercel_jwt=must-not-cross-patient',
      }}),output,async()=> 'synthetic-oidc');
      assert.equal(output.statusCode,200);
      assert.equal(JSON.parse(output.text()).patient,who);
    }
    const missing=streamingResponse();
    await proxy(req('profile',{headers:{cookie:'_vercel_jwt=not-identity'}}),
      missing,async()=> 'synthetic-oidc');
    assert.equal(missing.statusCode,401);
  });
});


test('W01 Vercel API rewrite includes terminal slashes and never falls through to SPA', () => {
  const frontend = JSON.parse(readFileSync(
    new URL('../../frontend/vercel.json', import.meta.url), 'utf8'));
  const monorepo = JSON.parse(readFileSync(
    new URL('../../vercel.json', import.meta.url), 'utf8'));

  assert.deepEqual(frontend.rewrites, [
    {source:'/api/v1/:path(.*)', destination:'/api/preview-proxy?path=:path'},
    {source:'/:path((?!api(?:/|$)).*)', destination:'/index.html'},
  ]);
  assert.deepEqual(monorepo.rewrites, [
    {source:'/:path((?!api(?:/|$)).*)', destination:'/index.html'},
  ]);

  // Test the documented regex semantics independently of Django, without
  // assuming the serverless proxy is invoked by Vercel for an unmatched URL.
  const apiPrefix = /^\/api\/v1\/(.*)$/;
  const spaFallback = /^\/(?!api(?:\/|$)).*$/;
  for (const path of [
    '/api/v1/documents/', '/api/v1/documents',
    '/api/v1/logs/', '/api/v1/logs', '/api/v1/profile/',
    '/api/v1/account/consent', '/api/v1/', '/api/other',
  ]) {
    assert.equal(spaFallback.test(path), false, path);
  }
  for (const [url,tail] of [
    ['/api/v1/documents/', 'documents/'],
    ['/api/v1/documents', 'documents'],
    ['/api/v1/logs/', 'logs/'],
    ['/api/v1/profile', 'profile'],
  ]) {
    assert.equal(apiPrefix.exec(url)?.[1], tail);
    assert.deepEqual(requestPath({...req(tail),url}), {path:tail,search:''});
  }
  for (const path of ['/', '/dashboard', '/preferences']) {
    assert.equal(spaFallback.test(path), true, path);
  }
});

test('W01 slash-terminated documents route keeps bearer-only 401, never HTML', async () => {
  await withEnv(async () => {
    let calls = 0;
    globalThis.fetch = async(url,init) => {
      calls++;
      assert.equal(url, apiOrigin + '/api/v1/documents/');
      assert.equal(init.headers.get('cookie'), null);
      return new Response(JSON.stringify({detail:'Unauthorized'}), {
        status:401,headers:{'content-type':'application/json'},
      });
    };
    const output = streamingResponse();
    await proxy({...req('documents/'),url:'/api/v1/documents/'},
      output,async()=> 'synthetic-oidc');
    assert.equal(calls,1);
    assert.equal(output.statusCode,401);
    assert.match(output.headers['content-type'],/application\/json/);
    assert.deepEqual(JSON.parse(output.text()),{detail:'Unauthorized'});
  });
});


test('W01 G5 synthetic Web BFF PATCH A-B-A remains account-scoped and rejects anonymous mutation', async () => {
  // This is a proxy contract against an explicit synthetic upstream, not proof
  // of IAMINA identity on hosted Vercel / Neon.
  await withEnv(async () => {
    const state = {A: 'fr', B: 'ar'};
    const principals = {'Bearer fixture-A': 'A', 'Bearer fixture-B': 'B'};
    let upstreamCalls = 0;
    globalThis.fetch = async (url, options) => {
      upstreamCalls++;
      assert.equal(url, apiOrigin + '/api/v1/profile');
      assert.equal(options.headers.get('cookie'), null);
      assert.equal(options.headers.get('x-csrftoken'), null);
      assert.equal(options.headers.get('x-vercel-trusted-oidc-idp-token'), 'synthetic-oidc');
      const who = principals[options.headers.get('authorization')];
      if (!who) return new Response(JSON.stringify({detail:'Unauthorized'}), {
        status:401,headers:{'content-type':'application/json'},
      });
      if (options.method === 'PATCH') {
        const data = JSON.parse(options.body.toString());
        state[who] = data.preferred_language;
      }
      return new Response(JSON.stringify({patient: who, preferred_language: state[who]}), {
        status:200,headers:{'content-type':'application/json','set-cookie':'sessionid=not-forwarded'},
      });
    };
    async function mutation(authorization, preferred_language) {
      const incoming = Readable.from([Buffer.from(JSON.stringify({preferred_language}))]);
      Object.assign(incoming, req('profile', {method:'PATCH',headers:{
        origin,authorization,'content-type':'application/json',
        cookie:'_vercel_jwt=never-patient-identity',
        'x-csrftoken':'forged-browser-session-csrf',
      }}));
      const output = streamingResponse();
      await proxy(incoming,output,async()=> 'synthetic-oidc');
      assert.equal(output.headers['set-cookie'],undefined);
      return {status:output.statusCode,body:JSON.parse(output.text())};
    }
    for (const [bearer,patient,language] of [
      ['Bearer fixture-A','A','ar'],
      ['Bearer fixture-B','B','fr'],
      ['Bearer fixture-A','A','fr'],
    ]) {
      const result = await mutation(bearer,language);
      assert.equal(result.status,200);
      assert.deepEqual(result.body,{patient,preferred_language:language});
    }
    const forged = await mutation('Bearer tampered-A','en');
    assert.equal(forged.status,401);
    assert.equal(forged.body.detail,'Unauthorized');
    const blank = await mutation(undefined,'en');
    assert.equal(blank.status,401);
    assert.deepEqual(state,{A:'fr',B:'fr'});
    const before = upstreamCalls;
    const hostile = Readable.from([Buffer.from('{"preferred_language":"en"}')]);
    Object.assign(hostile, req('profile', {method:'PATCH',headers:{
      origin:'https://attacker.example',authorization:'Bearer fixture-A',
      'content-type':'application/json',
    }}));
    const denied = streamingResponse();
    await proxy(hostile,denied,async()=> 'synthetic-oidc');
    assert.equal(denied.statusCode,403);
    assert.equal(upstreamCalls,before);
    assert.deepEqual(state,{A:'fr',B:'fr'});
  });
});

test('W01 G5 Web body-size boundary: 4 MiB exact, +1 and 15 MiB fail closed', async () => {
  await withEnv(async () => {
    const limit = 4 * 1024 * 1024;
    let calls = 0;
    globalThis.fetch = async (url,opts) => {
      calls++;
      assert.equal(url,apiOrigin + '/api/v1/documents/');
      assert.equal(opts.body.length,limit);
      assert.equal(opts.headers.get('cookie'),null);
      return new Response('{"ok":true}',{
        status:200,headers:{'content-type':'application/json'},
      });
    };
    async function upload(bytes) {
      const incoming = Readable.from([Buffer.alloc(bytes,65)]);
      Object.assign(incoming,req('documents/',{method:'POST',headers:{
        origin,'content-type':'application/octet-stream',
        authorization:'Bearer fixture-A',
        cookie:'_vercel_jwt=do-not-forward',
      }}));
      const output=streamingResponse();
      await proxy(incoming,output,async()=> 'synthetic-oidc');
      return output;
    }
    const exact=await upload(limit);
    assert.equal(exact.statusCode,200);
    assert.equal(JSON.parse(exact.text()).ok,true);
    assert.equal(calls,1);
    const tooLarge=await upload(limit+1);
    assert.equal(tooLarge.statusCode,413);
    const clinicalMax=await upload(15*1024*1024);
    assert.equal(clinicalMax.statusCode,413);
    assert.equal(calls,1); // no upstream clinical egress on oversize.
  });
});

test('W01 G5 real multipart framing counts toward 4 MiB Web body cap', async () => {
  await withEnv(async () => {
    const cap = 4 * 1024 * 1024;
    const boundary = 'w01-synthetic-boundary';
    const prefix = Buffer.from(
      '--' + boundary + '\r\n' +
      'Content-Disposition: form-data; name="file"; filename="synthetic.pdf"\r\n' +
      'Content-Type: application/pdf\r\n\r\n'
    );
    const suffix = Buffer.from('\r\n--' + boundary + '--\r\n');
    const framing = prefix.length + suffix.length;
    assert.ok(framing > 0 && framing < 1024);

    let upstreamCalls = 0;
    globalThis.fetch = async (url, options) => {
      upstreamCalls++;
      assert.equal(url, apiOrigin + '/api/v1/documents/ingest');
      assert.equal(options.body.length, cap);
      assert.equal(options.headers.get('authorization'), 'Bearer synthetic-A');
      assert.equal(options.headers.get('cookie'), null);
      assert.equal(
        options.headers.get('content-type'),
        'multipart/form-data; boundary=' + boundary
      );
      return new Response('{"ok":true}', {
        status: 200,
        headers: {'content-type': 'application/json'},
      });
    };

    async function upload(fileBytes) {
      const incoming = Readable.from([
        prefix, Buffer.alloc(fileBytes, 65), suffix,
      ]);
      Object.assign(incoming, req('documents/ingest', {
        method: 'POST',
        headers: {
          origin,
          'content-type': 'multipart/form-data; boundary=' + boundary,
          authorization: 'Bearer synthetic-A',
          cookie: '_vercel_jwt=private-not-forwarded',
        },
      }));
      const output = streamingResponse();
      await proxy(incoming, output, async () => 'synthetic-oidc');
      return output;
    }

    // The 4 MiB cap applies to *whole multipart body*, not just file bytes.
    const fitting = await upload(cap - framing);
    assert.equal(fitting.statusCode, 200);
    assert.deepEqual(JSON.parse(fitting.text()), {ok:true});
    assert.equal(upstreamCalls, 1);

    const oneByteOver = await upload(cap - framing + 1);
    assert.equal(oneByteOver.statusCode, 413);
    const fileExactlyCap = await upload(cap);
    assert.equal(fileExactlyCap.statusCode, 413);
    const clinical15MiB = await upload(15 * 1024 * 1024);
    assert.equal(clinical15MiB.statusCode, 413);
    assert.equal(upstreamCalls, 1, 'Oversized multipart never reaches Django');
  });
});

test('W01 G5 unavailable API and leaked SSO challenge never confirm a mutation', async () => {
  await withEnv(async () => {
    const input=req('profile',{headers:{authorization:'Bearer fixture-A',
      cookie:'_vercel_jwt=SSO',origin}});
    const upstreams=[
      async ()=>new Response('{"detail":"Service Unavailable"}',{status:503,
        headers:{'content-type':'application/json','set-cookie':'sessionid=secret'}}),
      async ()=>new Response('<html>SSO login</html>',{status:200,
        headers:{'content-type':'text/html','set-cookie':'_vercel_jwt=secret'}}),
      async ()=>{throw Error('synthetic upstream outage with a secret token');},
    ];
    for (const [idx,server] of upstreams.entries()) {
      globalThis.fetch=server;
      const output=streamingResponse();
      await proxy(input,output,async()=> 'synthetic-oidc');
      assert.equal(output.statusCode,idx===0?503:502);
      assert.equal(output.headers['set-cookie'],undefined);
      assert.ok(!output.text().includes('synthetic upstream outage'));
      assert.ok(!output.text().includes('_vercel_jwt'));
    }
  });
});


test('W01 G5 must not relay forged client IP assertions to the protected API', async () => {
  // This deliberately does NOT solve client attribution across two Vercel
  // proxies. A trusted end-user rate-limit identity needs separately
  // authenticated design and hosted negative proofs. Raw forwarded IP
  // headers from the Web visitor must never become Django identity.
  await withEnv(async () => {
    let calls=0;
    globalThis.fetch=async (_url,init)=>{
      calls++;
      for (const header of [
        'x-forwarded-for','x-real-ip','x-vercel-forwarded-for',
        'x-iamina-client-ip','x-iamina-client-ip-hash',
      ]) {
        assert.equal(init.headers.get(header),null,header);
      }
      assert.equal(init.headers.get('cookie'),null);
      assert.equal(init.headers.get('authorization'),'Bearer synthetic');
      return new Response('{"detail":"accepted"}',{
        status:200,headers:{'content-type':'application/json'},
      });
    };
    const output=streamingResponse();
    await proxy(req('auth/me',{headers:{
      authorization:'Bearer synthetic',
      cookie:'_vercel_jwt=not-an-iamina-identity',
      'x-forwarded-for':'203.0.113.66',
      'x-real-ip':'198.51.100.77',
      'x-vercel-forwarded-for':'198.51.100.88',
      'x-iamina-client-ip':'spoofed-by-visitor',
      'x-iamina-client-ip-hash':'attacker',
    }}),output,async()=> 'synthetic-oidc');
    assert.equal(output.statusCode,200);
    assert.equal(JSON.parse(output.text()).detail,'accepted');
    assert.equal(calls,1);
  });
});
