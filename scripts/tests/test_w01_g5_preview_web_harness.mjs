import assert from 'node:assert/strict';
import test from 'node:test';
import vm from 'node:vm';
import {
  isSyntheticPreview, renderPreviewHtml, default as handler,
  TEST_WEB_PROJECT, TEST_BRANCH,
} from '../../frontend/api/w01-g5-e2e.js';

const HOST = 'iamina-review-example12-achraf-benmoussa-s-projects.vercel.app';
const ENV = {
  VERCEL:'1', VERCEL_ENV:'preview', VERCEL_PROJECT_ID:TEST_WEB_PROJECT,
  VERCEL_GIT_COMMIT_REF:TEST_BRANCH, VERCEL_URL:HOST,
};
function call(method='GET',host=HOST,env=ENV) {
  const res={code:200,headers:{},body:null,setHeader(k,v){this.headers[k]=v;},
    status(c){this.code=c;return this;},end(v){this.body=v??null;return this;}};
  const old={};
  for(const key of Object.keys(ENV)){old[key]=process.env[key];delete process.env[key];}
  Object.assign(process.env,env);
  try{handler({method,headers:{host}},res);}
  finally{for(const key of Object.keys(ENV)){
    if(old[key]===undefined) delete process.env[key]; else process.env[key]=old[key];
  }}
  return res;
}

test('synthetic Preview guard fails closed for wrong project, environment, branch and host',()=>{
  assert.equal(isSyntheticPreview({method:'GET',headers:{host:HOST}},ENV),true);
  for(const [key,v] of [
    ['VERCEL','0'],['VERCEL_ENV','production'],['VERCEL_PROJECT_ID','prj_other'],['VERCEL_GIT_COMMIT_REF','main'],
    ['VERCEL_URL','another.vercel.app'],
  ]){
    assert.equal(isSyntheticPreview({method:'GET',headers:{host:HOST}},{...ENV,[key]:v}),false,key);
  }
  for(const host of ['iamina-review.vercel.app',HOST+'.evil.test','localhost',
    'iamina-certified-example12-achraf-benmoussa-s-projects.vercel.app','']){
    assert.equal(isSyntheticPreview({method:'GET',headers:{host}},ENV),false);
  }
  assert.equal(isSyntheticPreview({method:'POST',headers:{host:HOST}},ENV),false);
});

test('non-Preview host and write methods are 404 before any HTML',()=>{
  for(const [method,host,env] of [
    ['POST',HOST,ENV],['GET',HOST,{...ENV,VERCEL_ENV:'production'}],
    ['GET','iamina-review.vercel.app',ENV]
  ]){
    const result=call(method,host,env);
    assert.equal(result.code,404);
    assert.equal(result.body,null);
    assert.match(result.headers['Cache-Control'],/no-store/);
  }
});

test('Preview HTML requires explicit consent and is CSP nonce protected',()=>{
  const r=call();
  assert.equal(r.code,200);
  assert.match(r.headers['Content-Type'],/text\/html/);
  assert.equal(r.headers['X-Frame-Options'],'DENY');
  const csp=r.headers['Content-Security-Policy'];
  assert.match(csp,/connect-src 'self'/);
  assert.match(csp,/default-src 'none'/);
  assert.doesNotMatch(csp,/unsafe-inline|https:\/\//);
  const nonce=csp.match(/script-src 'nonce-([^']+)'/)[1];
  assert.ok(nonce.length>=20);
  assert.ok(r.body.includes('<script nonce="'+nonce+'">'));
  assert.ok(r.body.includes('<style nonce="'+nonce+'">'));
  assert.ok(r.body.includes('id="launch" type="button" aria-describedby="state"'));
  assert.ok(!r.body.includes('id="launch" type="button" disabled'));
  assert.ok(r.body.includes('id="mobile-hint"'));
  assert.ok(r.body.includes('id="consent"'));
  assert.ok(r.body.includes('iamina:w01:safe-summary'));
  assert.ok(r.body.includes("await request('ops/preview-db-identity')"));
  assert.ok(r.body.includes('neon_postcondition_required'));
  assert.ok(!r.body.includes('DATABASE_URL='));
});

test('nonce changes every GET, rendering is deterministic for same nonce',()=>{
  const a=call(),b=call();
  assert.notEqual(a.headers['Content-Security-Policy'],b.headers['Content-Security-Policy']);
  assert.ok(renderPreviewHtml('test-nonce').includes('nonce="test-nonce"'));
  const newCommit = '0123456789abcdef0123456789abcdef01234567';
  assert.ok(renderPreviewHtml('test-nonce',newCommit).includes('"deployment_head"') === false);
  assert.ok(renderPreviewHtml('test-nonce',newCommit).includes("deployment_head: '"+newCommit+"'"));
  assert.ok(renderPreviewHtml('test-nonce','invalid').includes("deployment_head: 'unavailable'"));
  assert.ok(!renderPreviewHtml('test-nonce',newCommit).includes('source_head'));
});

test('iPhone-sized Web control gives feedback without consent and creates no accounts', async () => {
  const html = renderPreviewHtml('safe-nonce');
  const source = html.match(/<script nonce="safe-nonce">([\s\S]*?)<\/script>/)?.[1];
  assert.ok(source);
  assert.doesNotThrow(() => new vm.Script(source));
  assert.match(html, /name="viewport" content="width=device-width,initial-scale=1"/);
  const listeners = new Map();
  const el = (id) => ({
    id, checked: false, disabled: false, textContent: '',
    listeners: {},
    focused: false,
    addEventListener(type, cb) { this.listeners[type] = cb; },
    focus() { this.focused = true; },
  });
  const elements = new Map(['consent', 'launch', 'state', 'report', 'origin'].map(id => [id, el(id)]));
  const observedRequests = [];
  const context = {
    document: { getElementById(id) { return elements.get(id); } },
    location: {
      origin: 'https://' + HOST,
      hostname: HOST,
      pathname: '/api/w01-g5-e2e',
      protocol: 'https:',
    },
    window: {
      addEventListener(type, cb) { listeners.set(type, cb); },
      dispatchEvent(event) { listeners.get(event.type)?.(event); },
    },
    CustomEvent: class { constructor(type, { detail }) { this.type = type; this.detail = detail; } },
    fetch: async url => {
      observedRequests.push(String(url));
      return {
        status: 200, headers: { get: () => 'application/json' },
        json: async () => ({ database_name: 'other-db' }), // fail closed before any registration
      };
    },
    console: { log() {}, error() {} },
  };
  vm.runInNewContext(source, context, { timeout: 1000 });
  const checkbox = elements.get('consent'), launch = elements.get('launch'), status = elements.get('state');
  assert.equal(launch.disabled, false, 'button must not be inert on iPhone');
  await launch.listeners.click();
  assert.match(status.textContent, /coche d’abord la case/);
  assert.equal(checkbox.focused, true);
  assert.equal(observedRequests.length, 0, 'never touch API without consent');
  checkbox.checked = true;
  checkbox.listeners.change();
  assert.match(status.textContent, /Autorisation cochée/);
  await launch.listeners.click();
  assert.equal(observedRequests.length, 1);
  assert.match(observedRequests[0], /\/api\/v1\/ops\/preview-db-identity$/);
  assert.equal(launch.disabled, true, 'no repeated synthetic test after failure');
  const report = elements.get('report').textContent;
  assert.match(report, /FAIL_OR_BLOCKED/);
  assert.match(report, /not_created/);
  assert.doesNotMatch(report, /password|access_token|bearer/i);
  assert.equal(observedRequests.some(x => /register|login/i.test(x)), false);
  checkbox.checked = true;
  await launch.listeners.click();
  assert.equal(observedRequests.length, 1, 'at most one attempt per load');
});
