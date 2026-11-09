import test from 'node:test';
import assert from 'node:assert/strict';
import {runHostedAuthGate} from '../../../scripts/d7_qa_hosted_auth_gate.mjs';

const origin = 'https://iamina-review-ggdtqis0g-achraf-benmoussa-s-projects.vercel.app';
const creds = Object.freeze({
  aEmail: 'local-a@example.invalid', aPassword: 'fake-secret-a',
  bEmail: 'local-b@example.invalid', bPassword: 'fake-secret-b',
  accessBypass: 'fake-share-token-for-tests',
});
function makeFetcher({invalidCookie = false, htmlChallenge = false,
                      nonDjango401 = false, sameOwner = false} = {}) {
  const seen = [];
  const fetcher = async (url, options) => {
    assert.equal(options.redirect, 'manual');
    if (url.startsWith(origin + '/?_vercel_share=')) {
      assert.equal(options.method, 'GET');
      assert.equal(new URL(url).searchParams.get('_vercel_share'), creds.accessBypass);
      seen.push('share');
      return new Response(null, {status: 302, headers: {
        location: origin + '/',
        ...(invalidCookie ? {} : {'set-cookie': '_vercel_jwt=synthetic-cookie; Path=/; Secure; HttpOnly'}),
      }});
    }
    if (url === origin + '/') {
      seen.push('app');
      assert.equal(options.headers.cookie, '_vercel_jwt=synthetic-cookie');
      return new Response('<title>IAMINA</title><script src="flutter_bootstrap.js"></script>', {
        status: 200, headers: {'content-type': 'text/html'},
      });
    }
    assert.equal(url, origin + '/api/v1/auth/login');
    assert.equal(options.headers.cookie, '_vercel_jwt=synthetic-cookie');
    assert.equal(options.headers['x-vercel-protection-bypass'], undefined);
    if (htmlChallenge) {
      seen.push('sso');
      return new Response('<html>SSO</html>', {status: 200, headers: {'content-type': 'text/html'}});
    }
    const body = JSON.parse(options.body);
    seen.push(body.email);
    if (body.email.startsWith('nonexistent-')) {
      return new Response(JSON.stringify({detail: nonDjango401 ? 'Access denied' : 'Invalid authentication credential'}), {
        status: 401, headers: {'content-type': 'application/json'},
      });
    }
    const user = {id: sameOwner ? 11 : body.email === creds.bEmail ? 22 : 11, email: body.email};
    return new Response(JSON.stringify({
      user, token_type: 'Bearer', access_token: 'iamina.synthetic-token-only',
    }), {status: 200, headers: {'content-type': 'application/json'}});
  };
  return {fetcher, seen};
}
test('scoped share-cookie bootstrap and real Django A-B-A shape; secrets absent from result', async () => {
  const {fetcher, seen} = makeFetcher();
  const result = await runHostedAuthGate({fetcher, origin, creds});
  assert.equal(result.verdict, 'AUTH_ONLY_PASS');
  assert.equal(result.negative_login, 'DJANGO_401_JSON');
  assert.equal(result.distinct_owners, true);
  assert.equal(result.browser_profile_and_treatment_fue, 'NOT_RUN');
  assert.deepEqual(seen, ['share', 'app', 'nonexistent-d7-probe@example.invalid',
    creds.aEmail, creds.bEmail, creds.aEmail]);
  assert.doesNotMatch(JSON.stringify(result), /fake-secret|fake-share|@example|synthetic-cookie/);
});
test('missing/expired Share Link fails before any QA password is sent', async () => {
  const {fetcher, seen} = makeFetcher({invalidCookie: true});
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_SHARE_COOKIE_UNAVAILABLE/);
  assert.deepEqual(seen, ['share']);
});
test('Vercel SSO challenge cannot masquerade as Django 401', async () => {
  const {fetcher, seen} = makeFetcher({htmlChallenge: true});
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_NEGATIVE_NON_JSON_200/);
  assert.deepEqual(seen, ['share', 'app', 'sso']);
});
test('non-Django JSON 401 cannot masquerade as successful auth preflight', async () => {
  const {fetcher, seen} = makeFetcher({nonDjango401: true});
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_NEGATIVE_NOT_DJANGO_AUTH/);
  assert.deepEqual(seen, ['share', 'app', 'nonexistent-d7-probe@example.invalid']);
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
test('B returning same owner as A fails closed', async () => {
  const {fetcher} = makeFetcher({sameOwner: true});
  await assert.rejects(runHostedAuthGate({fetcher, origin, creds}),
    /D7_QA_OWNER_A_B_A_MISMATCH/);
});
