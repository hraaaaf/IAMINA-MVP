import test from 'node:test';
import assert from 'node:assert/strict';
import {ORIGIN, DEPLOY_SHA, VIEWPORTS, guard, emptyProof}
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
test('real hosted browser smoke cannot claim clinical FUE certification',()=>{
  const proof=emptyProof();
  assert.equal(proof.steps.treatment_change_and_persistence,'NOT_RUN');
  assert.equal(proof.steps.clinical_privacy_review,'NOT_RUN');
  assert.equal(proof.result,'NOT_RUN');
  assert.doesNotMatch(JSON.stringify(proof),/share-token|patient@gmail.com|@example/);
});
