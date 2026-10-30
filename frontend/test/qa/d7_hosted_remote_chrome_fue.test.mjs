import test from 'node:test';
import assert from 'node:assert/strict';
import {ORIGIN, DEPLOY_SHA, VIEWPORTS, guard, emptyProof,
  ACCOUNT_CHOICE_LABEL, LOGIN_SUBMIT_LABEL, activateFlutterAccountSemantics,
  D7_QA_STAGES, safeBrowserErrorCode, loginRedirectFailureCode,
  classifyLogin401Response}
  from '../../../scripts/d7_hosted_remote_chrome_fue.mjs';
const valid={origin:ORIGIN,sha:DEPLOY_SHA,
  token:'synthetic-share-token-123456',
  email:'qa@example.invalid',password:'not-a-real-password'};
test('exact protected QA host/SHA and synthetic test account are required',()=>{
  assert.equal(guard(valid),true);
  for(const wrong of [
    {origin:'https://iamina-certified.vercel.app'},
    {origin:'https://iamina-review.vercel.app'},
    {sha:'any-other-commit'},{token:''},{email:'patient@gmail.com'},
    {password:''}
  ])assert.throws(()=>guard({...valid,...wrong}),/D7_CHROME_/);
});
test('responsive Chrome viewports are bounded',()=>{
  assert.deepEqual(VIEWPORTS,[[390,844],[768,1024],[1280,900]]);
});
test('hosted login selectors match exact EN/FR/AR UI actions only',()=>{
  for (const label of [
    'Sign in or create an account',
    'Se connecter ou créer un compte',
    'تسجيل الدخول أو إنشاء حساب',
  ]) assert.match(label, ACCOUNT_CHOICE_LABEL);
  for (const label of ['Sign in','Se connecter','الدخول'])
    assert.match(label, LOGIN_SUBMIT_LABEL);
  for (const label of ['Continue without an account','Create account','Sign in'])
    assert.doesNotMatch(label, ACCOUNT_CHOICE_LABEL);
  for (const label of ['Create account','Continue without an account'])
    assert.doesNotMatch(label, LOGIN_SUBMIT_LABEL);
});

test('Flutter semantics activation is required before account click',async()=>{
  const calls=[];
  const account={waitFor:async opts=>{calls.push('wait:'+opts.state);}};
  const page={
    locator:selector=>{
      assert.equal(selector,'flt-semantics-placeholder');
      return {first:()=>({
        count:async()=>1,
        evaluate:async fn=>{
          assert.match(fn.toString(),/dispatchEvent.*MouseEvent/);
          calls.push('activate');
        },
      })};
    },
    getByRole:(role,{name})=>{
      assert.equal(role,'button');
      assert.equal(name,ACCOUNT_CHOICE_LABEL);
      return {first:()=>account};
    },
  };
  assert.equal(await activateFlutterAccountSemantics(page),account);
  assert.deepEqual(calls,['activate','wait:visible']);
});

test('missing Flutter accessibility placeholder fails closed',async()=>{
  const page={locator:()=>({first:()=>({count:async()=>0})})};
  await assert.rejects(activateFlutterAccountSemantics(page),
    /D7_CHROME_ACCESSIBILITY_PLACEHOLDER_MISSING/);
});

test('browser failures report bounded stage only, never raw exception',()=>{
  for(const stage of D7_QA_STAGES){
    const secret='https://private.example.invalid/?_vercel_share=should-not-print';
    const code=safeBrowserErrorCode(new Error(secret),stage);
    assert.equal(code,'D7_CHROME_'+stage+'_FAILED');
    assert.doesNotMatch(code,/private|share|https/);
  }
  assert.equal(safeBrowserErrorCode(new Error('untrusted'), 'made-up'),
    'D7_CHROME_BROWSER_ERROR');
  assert.equal(safeBrowserErrorCode(new Error('D7_CHROME_ACCOUNT_BUTTON_INACCESSIBLE'),
    'ACCOUNT_SEMANTICS'),'D7_CHROME_ACCOUNT_BUTTON_INACCESSIBLE');
});

test('login redirect timeout reports only bounded HTTP status class',()=>{
  for(const [status,want] of [
    [undefined,'D7_CHROME_LOGIN_NO_HTTP_RESPONSE'],
    [null,'D7_CHROME_LOGIN_NO_HTTP_RESPONSE'],
    [200,'D7_CHROME_LOGIN_HTTP_2XX_NO_REDIRECT'],
    [201,'D7_CHROME_LOGIN_HTTP_2XX_NO_REDIRECT'],
    [401,'D7_CHROME_LOGIN_HTTP_401'],
    [403,'D7_CHROME_LOGIN_HTTP_403'],
    [404,'D7_CHROME_LOGIN_HTTP_4XX'],
    [502,'D7_CHROME_LOGIN_HTTP_5XX'],
    [302,'D7_CHROME_LOGIN_HTTP_OTHER_NO_REDIRECT'],
  ]) assert.equal(loginRedirectFailureCode(status),want);
});

test('login 401 classifier distinguishes Django credential rejection from other gates',async()=>{
  const response=(type,body,status=401)=>({
    status:()=>status,
    headerValue:async()=>type,
    json:async()=>body,
  });
  assert.equal(await classifyLogin401Response(
    response('application/json',{detail:'Invalid authentication credential'})),
    'D7_CHROME_LOGIN_DJANGO_CREDENTIAL_REJECTED');
  assert.equal(await classifyLogin401Response(
    response('text/html','<private>')),
    'D7_CHROME_LOGIN_HTTP_401_OTHER');
  assert.equal(await classifyLogin401Response(
    response('application/json',{detail:'Other authentication failure'})),
    'D7_CHROME_LOGIN_HTTP_401_OTHER');
  assert.equal(await classifyLogin401Response(
    response('application/json',{detail:'Invalid authentication credential'},403)),
    null);
  assert.equal(await classifyLogin401Response({
    status:()=>401,headerValue:async()=>{throw new Error('private value');},
  }), 'D7_CHROME_LOGIN_HTTP_401_OTHER');
  assert.equal(await classifyLogin401Response(
    response('application/json',{detail:'Invalid authentication credential',
      extra:'private value'})),
    'D7_CHROME_LOGIN_HTTP_401_OTHER');
});

test('login errors remain single-prefixed, without raw response content',()=>{
  const e=new Error(loginRedirectFailureCode(401));
  assert.equal(safeBrowserErrorCode(e,'LOGIN_REDIRECT'),
    'D7_CHROME_LOGIN_HTTP_401');
  assert.equal(safeBrowserErrorCode(
    new Error('D7_CHROME_LOGIN_DJANGO_CREDENTIAL_REJECTED'),'LOGIN_REDIRECT'),
    'D7_CHROME_LOGIN_DJANGO_CREDENTIAL_REJECTED');
});

test('real hosted browser smoke cannot claim clinical FUE certification',()=>{
  const proof=emptyProof();
  assert.equal(proof.steps.treatment_change_and_persistence,'NOT_RUN');
  assert.equal(proof.steps.clinical_privacy_review,'NOT_RUN');
  assert.equal(proof.result,'NOT_RUN');
  assert.doesNotMatch(JSON.stringify(proof),/share-token|patient@gmail.com|@example/);
});

test('protected QA secrets exist only in the Chrome execution step', async () => {
  const {readFileSync} = await import('node:fs');
  const workflow = readFileSync('.github/workflows/d7-hosted-remote-chrome-fue.yml', 'utf8');
  const before = workflow.split('      - name: Run real Chrome against Vercel-protected QA Web')[0];
  assert.doesNotMatch(before, /secrets\.D7_QA_/);
  assert.match(workflow, /Run real Chrome against Vercel-protected QA Web\n        env:/);
  assert.match(workflow, /actions\/checkout@11bd71901bbe5b1630ceea73d27597364c9af683/);
  assert.match(workflow, /actions\/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02/);
});
