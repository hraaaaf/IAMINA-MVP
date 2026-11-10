// D7 hosted Preview routing safety contract (source-only, no credentials).
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const build = readFileSync(new URL('../../vercel_build.sh', import.meta.url), 'utf8');
const auth = readFileSync(new URL('../../lib/services/auth_service.dart', import.meta.url), 'utf8');
const api = readFileSync(new URL('../../lib/services/api_client.dart', import.meta.url), 'utf8');
const proxy = readFileSync(new URL('../../api/index.js', import.meta.url), 'utf8');

test('D7-only Preview enables exact-page-origin login and denies stale W01 fallback', () => {
  assert.match(build, /VERCEL_ENV:-.*preview|preview\)/);
  assert.match(build, /if \[ "\$\{VERCEL_GIT_COMMIT_REF:-\}" = "qa\/d7-hosted-reconcile-20261110" \]; then\s+IAMINA_D2_PREVIEW_SAME_ORIGIN=true\s+API_BASE_URL="https:\/\/d7-qa-unrouted\.invalid"/);
  assert.match(build, /--dart-define=IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED=/);
  assert.match(build, /IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false/);
  assert.match(build, /IAMINA_REMOTE_ACCOUNT_SIGN_IN=true/);
  assert.match(build, /"fix\/d2-main-integrated-20261109"/);
});

test('Web patient account and consent resolve to the current exact HTTPS origin', () => {
  assert.match(auth, /String resolveAuthApiOrigin\(/);
  assert.match(auth, /if \(!isWeb \|\| !remoteAccountLogin\) return configuredBaseUrl;/);
  assert.match(auth, /return pageUri\.origin;/);
  assert.match(api, /remoteAccountLogin: const bool\.fromEnvironment\(/);
  assert.match(api, /'IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED'/);
  assert.match(api, /return resolveAuthApiOrigin\(/);
});

test('same-origin proxy retains immutable synthetic API and OIDC fail-closed boundary', () => {
  assert.match(proxy, /env\.VERCEL_ENV !== 'preview'/);
  assert.match(proxy, /env\.VERCEL_PROJECT_ID !== EXPECTED_PROJECT/);
  assert.match(proxy, /validTarget\(env\.IAMINA_REVIEW_PREVIEW_API_BASE_URL\)/);
  assert.match(proxy, /headers\.set\('x-vercel-trusted-oidc-idp-token', issuedToken\)/);
  assert.match(proxy, /if \(typeof issuedToken !== 'string' \|\| !issuedToken\)/);
  assert.match(proxy, /redirect: 'manual'/);
  assert.doesNotMatch(proxy, /headers\.set\('cookie'/);
});
