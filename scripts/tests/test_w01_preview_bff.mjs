import test from 'node:test';
import assert from 'node:assert/strict';
import { Readable, Writable } from 'node:stream';
import { proxy, safePath, requestPath, previewOnlyAndSameOrigin } from '../../frontend/api/preview-proxy.js';

const envKeys = [
  'VERCEL_ENV','VERCEL_PROJECT_ID','IAMINA_REVIEW_PREVIEW_API_BASE_URL',
  'VERCEL_OIDC_TOKEN'
];
const origin = 'https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app';
const apiOrigin = 'https://iamina-certified-1mrvxnuk9-achraf-benmoussa-s-projects.vercel.app';
function envSet() {
  process.env.VERCEL_ENV = 'preview';
  process.env.VERCEL_PROJECT_ID = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
  process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL = apiOrigin;
  process.env.VERCEL_OIDC_TOKEN = 'a.test.token';
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
