import test from 'node:test';
import assert from 'node:assert/strict';
import {ORIGIN, DEPLOY_SHA, VIEWPORTS, guard, emptyProof,
  ACCOUNT_CHOICE_LABEL, LOGIN_SUBMIT_LABEL}
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
