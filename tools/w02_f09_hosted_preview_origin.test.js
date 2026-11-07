'use strict';

// W02-F09 Preview origin / hosted local-only browser probe contracts.
// NO secrets, network calls, clinical APIs or patient data in these tests.
const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const resolver = path.join(root, 'frontend/scripts/w02_preview_origin.sh');
const build = fs.readFileSync(path.join(root, 'frontend/vercel_build.sh'), 'utf8');
const previewId = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const trusted = 'iamina-review-ntzu0e1iz-achraf-benmoussa-s-projects.vercel.app';

function resolve(host, project = previewId, environment = 'preview') {
  return spawnSync('bash', ['-c',
    'source "$1"; iamina_w02_preview_origin "$2" "$3" "$4"',
    '--', resolver, host, project, environment,
  ], { cwd: root, encoding: 'utf8', timeout: 6000 });
}

test('Preview: immutable host resolves to the active same-origin backend base', () => {
  const p = resolve(trusted);
  assert.equal(p.status, 0, p.stderr);
  assert.equal(p.stdout.trim(), 'https://' + trusted);
  assert.equal(p.stderr, '');
});

test('Preview: other Vercel branch aliases, other apps and injection denied', () => {
  const bad = [
    'iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app',
    'iamina-certified-ntzu0e1iz-achraf-benmoussa-s-projects.vercel.app',
    'iamina-review-ntzu0e1iz-attacker-projects.vercel.app',
    'iamina-review-ntzu0e1iz-achraf-benmoussa-s-projects.vercel.app.evil.test',
    'https://' + trusted, trusted + '/api/v1',
    trusted + '\nAPI_BASE_URL=https://evil.test',
    'iamina-review-ntzu0e1iz-achraf-benmoussa-s-projects.vercelXapp',
    '', 'localhost', 'iamina-review-☃-achraf-benmoussa-s-projects.vercel.app',
  ];
  for (const host of bad) {
    const result = resolve(host);
    assert.equal(result.status, 64, 'Unexpectedly allowed: ' + host);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /immutable Preview origin unavailable/);
  }
});

test('Preview: wrong project, Production, absent or malformed env denied', () => {
  for (const [project, environment] of [
    [previewId, 'production'],
    [previewId, 'staging'],
    [previewId, ''],
    ['prj_other_project', 'preview'],
    ['', 'preview'],
  ]) {
    const r = resolve(trusted, project, environment);
    assert.equal(r.status, 64);
    assert.equal(r.stdout, '');
  }
});

test('Build uses VERCEL_URL, not the stale W01 browser API alias', () => {
  assert.match(build, /source "\$\(dirname "\$0"\)\/scripts\/w02_preview_origin\.sh"/);
  assert.match(build, /API_BASE_URL="\$\(iamina_w02_preview_origin/);
  assert.doesNotMatch(build, /API_BASE_URL="https:\/\/iamina-review-git-preview-w0/);
  assert.match(build, /case "\$\{VERCEL_ENV:-\}" in/);
  assert.match(build, /production\)[\s\S]*?API_BASE_URL="\$IAMINA_CERTIFIED_API_BASE_URL"/);
  assert.match(build, /echo "ERROR: refusing IAMINA Web build for unknown Vercel environment"/);
});

test('C9 synthetic probe is branch- and Preview-gated, never clinical main', () => {
  assert.match(build, /VERCEL_ENV:-}" = "preview"/);
  assert.match(build, /VERCEL_GIT_COMMIT_REF:-}" = "test\/w02-f09-hosted-preview-e2e-20261107"/);
  assert.match(build, /--base-href=\/__w02_f09_probe\//);
  assert.match(build, /--target=lib\/ui_w02_c9_two_tab_probe_main\.dart/);
  assert.match(build, /--output=build\/w02_f09_probe/);
  assert.match(build, /cp -R build\/w02_f09_probe\/\. build\/web\/__w02_f09_probe\//);
  const probe = fs.readFileSync(
    path.join(root, 'frontend/lib/ui_w02_c9_two_tab_probe_main.dart'), 'utf8',
  );
  assert.match(probe, /synthetic test precondition, NOT attestation/);
  assert.match(probe, /WebRefreshC8Coordinator/);
  assert.doesNotMatch(probe, /HTTP_COOKIE|DATABASE_URL|FirebaseAuth|BasePatientProfile/);
});

test('No clinical login/refresh route activated by this preview-only change', () => {
  const vercel = JSON.parse(fs.readFileSync(
    path.join(root, 'frontend/vercel.json'), 'utf8',
  ));
  assert.equal(vercel.git.deploymentEnabled, false);
  assert.equal(vercel.rewrites[0].source, '/api/v1/auth/refresh');
  assert.equal(vercel.rewrites[0].destination, '/api/session-refresh.js');
  const live = fs.readFileSync(
    path.join(root, 'frontend/api/session-refresh.js'), 'utf8',
  );
  assert.match(live, /ALWAYS deny/);
  assert.match(live, /reject\(res, 404\)/);
  assert.doesNotMatch(live, /w02_f09c7_verify_reply|w02_f09c6_response_candidate/);
});
