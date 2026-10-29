import test from 'node:test';
import assert from 'node:assert/strict';
import {runHostedAuthGate} from '../../../scripts/d7_qa_hosted_auth_gate.mjs';

const origin = 'https://iamina-review-ggdtqis0g-achraf-benmoussa-s-projects.vercel.app';
const creds = Object.freeze({
  aEmail: 'local-a@example.invalid', aPassword: 'fake-secret-a',
  bEmail: 'local-b@example.invalid', bPassword: 'fake-secret-b',
  accessBypass: 'fake-bypass-just-for-tests',
});

test('A-B-A contract preserves A identity and distinct B; no tokens in result', async () => {
  const seen = [];
  const fetcher = async (url, options) => {
    assert.equal(url, origin + '/api/v1/auth/login');
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers['x-vercel-protection-bypass'], creds.accessBypass);
    const body = JSON.parse(options.body);
    seen.push(body.email);
    if (body.email.startsWith('nonexistent-')) {
      return new Response('{"detail":"denied"}',
        {status: 401, headers: {'content-type': 'application/json'}});
    }
    const user = body.email === creds.bEmail ? {id: 22, email: creds.bEmail}
      : {id: 11, email: creds.aEmail};
    return new Response(JSON.stringify({
      user, token_type: 'Bearer', access_token: 'iamina.synthetic-token-only',
    }), {status: 200, headers: {'content-type': 'application/json'}});
  };
  const result = await runHostedAuthGate({fetcher, origin, creds});
  assert.equal(result.verdict, 'AUTH_ONLY_PASS');
  assert.equal(result.distinct_owners, true);
  assert.equal(result.browser_profile_and_treatment_fue, 'NOT_RUN');
  assert.deepEqual(seen, ['nonexistent-d7-probe@example.invalid',
    creds.aEmail, creds.bEmail, creds.aEmail]);
  assert.doesNotMatch(JSON.stringify(result), /fake-secret|fake-bypass|@example/);
});

test('SSO HTML challenge fails before real credentials are attempted', async () => {
  let calls = 0;
  const fetcher = async () => {
    calls++;
    return new Response('<html>login</html>', {
      status: 200, headers: {'content-type': 'text/html'},
    });
  };
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_NEGATIVE_NON_JSON_200/);
  assert.equal(calls, 1);
});

test('same identity and missing secret fail closed without network', async () => {
  let calls = 0;
  const fetcher = async () => {calls++; throw Error('unexpected');};
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds: {...creds, bEmail: creds.aEmail}}),
    /D7_QA_SAME_QA_IDENTITY/);
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds: {...creds, aPassword: ''}}),
    /D7_QA_REQUIRED_SECRET_MISSING/);
  assert.equal(calls, 0);
});

test('B returning same owner as A fails fail-closed', async () => {
  const fetcher = async (url, options) => {
    const body = JSON.parse(options.body);
    if (body.email.startsWith('nonexistent-')) return new Response('{}', {
      status: 401, headers: {'content-type': 'application/json'},
    });
    return new Response(JSON.stringify({
      user: {id: 1, email: body.email},
      token_type: 'Bearer', access_token: 'iamina.synthetic',
    }), {status: 200, headers: {'content-type': 'application/json'}});
  };
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_OWNER_A_B_A_MISMATCH/);
});
