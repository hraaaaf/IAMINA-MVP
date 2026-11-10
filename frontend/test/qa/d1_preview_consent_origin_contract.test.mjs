// IAMINA Preview D1 P0-A: prove login and consent share the exact current
// protected deployment origin before any bearer or consent payload is sent.
// Executes only the environment-selection portion of vercel_build.sh;
// never builds, accesses a backend, or reads secrets.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';

const source = readFileSync(new URL('../../vercel_build.sh', import.meta.url), 'utf8');
const start = source.indexOf('  case "${VERCEL_ENV:-}" in');
const end = source.indexOf('\n  esac', start);
assert.ok(start >= 0 && end > start, 'Preview environment selection must exist');
const previewPolicy = source.slice(start, end + '\n  esac'.length);

function previewFor(branch, {vercelUrl = 'iamina-review-synthetic123-achraf-benmoussa-s-projects.vercel.app'} = {}) {
  const script = `set -euo pipefail
IAMINA_CERTIFIED_API_BASE_URL=https://iamina-certified.vercel.app
IAMINA_D2_PREVIEW_SAME_ORIGIN=false
IAMINA_W01_SESSION_PROBE=false
${previewPolicy}
printf '%s|%s|%s|%s' "$IAMINA_D2_PREVIEW_SAME_ORIGIN" "$API_BASE_URL" "$IAMINA_REMOTE_ACCOUNT_SIGN_IN" "$IAMINA_REMOTE_ACCOUNT_ENROLLMENT"
`;
  const value = execFileSync('bash', ['-c', script], {
    encoding: 'utf8',
    env: {
      ...process.env,
      VERCEL_ENV: 'preview',
      VERCEL_GIT_COMMIT_REF: branch,
      VERCEL_URL: vercelUrl,
      IAMINA_REVIEW_PREVIEW_API_BASE_URL:
        'https://iamina-certified-synthetic-qa-achraf-benmoussa-s-projects.vercel.app',
    },
  }).trim();
  const [sameOrigin, baseUrl, login, enrollment] = value.split('|');
  return {sameOrigin, baseUrl, login, enrollment};
}

test('D1 legacy gate Preview must route consent to exact same origin as login', () => {
  for (const branch of [
    'fix/d1-p0a-legacy-no-cutover-guard-20261110',
    'fix/preview-consent-same-origin-20261110',
  ]) {
    const found = previewFor(branch);
    assert.equal(found.sameOrigin, 'true', branch);
    assert.equal(found.baseUrl,
      'https://iamina-review-synthetic123-achraf-benmoussa-s-projects.vercel.app', branch);
    assert.equal(found.login, 'true');
    assert.equal(found.enrollment, 'false');
  }
});

test('D1 Preview must reject missing or foreign deployment hostnames', () => {
  for (const vercelUrl of [
    '',
    'another-project-synthetic123-achraf-benmoussa-s-projects.vercel.app',
    'iamina-review-synthetic123-attacker.vercel.app',
    'iamina-review-synthetic123-achraf-benmoussa-s-projects.vercel.app.evil.test',
    'https://iamina-review-synthetic123-achraf-benmoussa-s-projects.vercel.app',
  ]) {
    assert.throws(
      () => previewFor('fix/preview-consent-same-origin-20261110', {vercelUrl}),
      /Command failed|refusing|Invalid/i,
    );
  }
});

test('existing D7 and D2 QA overrides retain their intended behavior', () => {
  const d7 = previewFor('qa/d7-hosted-reconcile-20261110');
  assert.equal(d7.sameOrigin, 'true');
  assert.equal(d7.baseUrl, 'https://d7-qa-unrouted.invalid');
  const d2 = previewFor('fix/d2-main-integrated-20261109');
  assert.equal(d2.sameOrigin, 'true');
  assert.match(d2.baseUrl, /^https:\/\/iamina-review-git-preview-/);
});

test('older W01 preview routing remains unchanged', () => {
  const w01 = previewFor('preview/w01-current-main-synthetic-20261104');
  assert.equal(w01.sameOrigin, 'false');
  assert.equal(w01.login, 'true');
  assert.equal(w01.enrollment, 'false');
});

test('Flutter API and auth control planes have a shared same-origin gate', () => {
  const auth = readFileSync(new URL('../../lib/services/auth_service.dart', import.meta.url), 'utf8');
  const api = readFileSync(new URL('../../lib/services/api_client.dart', import.meta.url), 'utf8');
  const consent = readFileSync(new URL('../../lib/services/consent_api_extension.dart', import.meta.url), 'utf8');
  assert.match(auth, /return pageUri\.origin;/);
  assert.match(api, /'IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED'/);
  assert.match(api, /return resolveAuthApiOrigin\(/);
  assert.match(consent, /Uri\.parse\('\/api\/v1\/account\/consent'\)/);
});
