import assert from 'node:assert/strict';
import test from 'node:test';
import { default as handler, renderCleanupHtml } from '../../frontend/api/w01-g5-cleanup.js';

const HOST='iamina-review-example12-achraf-benmoussa-s-projects.vercel.app';
const BASE={
  VERCEL:'1',VERCEL_ENV:'preview',VERCEL_PROJECT_ID:'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
  VERCEL_GIT_COMMIT_REF:'feat/w01-preview-same-origin-bff-20261017',VERCEL_URL:HOST
};
function run(method='GET',host=HOST,env=BASE){
 const previous={...process.env};for(const k of Object.keys(process.env))delete process.env[k];
 Object.assign(process.env,env);
 const response={statusCode:200,headers:{},body:null,
   setHeader(k,v){this.headers[k]=v;},status(c){this.statusCode=c;return this;},
   end(v){this.body=v??null;return this;}};
 try{handler({method,headers:{host}},response);}finally{
   for(const k of Object.keys(process.env))delete process.env[k];Object.assign(process.env,previous);
 }
 return response;
}
test('exact Preview only, POST and Production must 404 without HTML',()=>{
 for(const [method,host,env] of [
  ['POST',HOST,BASE],['GET',HOST,{...BASE,VERCEL_ENV:'production'}],
  ['GET','iamina-review.vercel.app',BASE],
 ]){
  const r=run(method,host,env);assert.equal(r.statusCode,404);assert.equal(r.body,null);
 }
});
test('UI demands two real operator clicks and never deletes on page load',()=>{
 const r=run();assert.equal(r.statusCode,200);
 assert.match(r.body,/id="preflight"/);
 assert.match(r.body,/id="erase" disabled/);
 assert.match(r.body,/id="consent" disabled/);
 assert.match(r.body,/addEventListener\('click'/);
 assert.match(r.body,/challenge/);
 assert.match(r.body,/DELETE TWO W01 SYNTHETIC ACCOUNTS/);
 assert.match(r.body,/neon_independent_check_required/);
 assert.doesNotMatch(r.body,/DATABASE_URL|Bearer \w+/);
});
test('non-cacheable nonce CSP and no cross-origin egress',()=>{
 const a=run(),b=run();
 assert.match(a.headers['Content-Security-Policy'],/connect-src 'self'/);
 assert.match(a.headers['Cache-Control'],/no-store/);
 assert.notEqual(a.headers['Content-Security-Policy'],b.headers['Content-Security-Policy']);
 assert.doesNotMatch(a.headers['Content-Security-Policy'],/unsafe-inline/);
 assert.match(renderCleanupHtml('test-nonce'),/nonce="test-nonce"/);
 assert.match(a.body,/credentials:'same-origin'/);
 assert.match(a.body,/\/api\/v1\/ops\/w01-g5-synthetic-cleanup/);
});
