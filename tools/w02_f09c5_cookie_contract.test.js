'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  candidateRefreshCookieHeaders,
  candidateLogoutCookieHeaders,
} = require('../frontend/api/w02_f09c5_cookie_policy.js');

const secret = 'iamina-wr1.' + 'C'.repeat(64);
const csrf = 'c2.1790000000.' + 'W'.repeat(24) + '.' + 'd'.repeat(64);
const candidate = Object.freeze({
  enabled: true, familyId: '42',
  refreshSecret: secret, csrfToken: csrf, maxAgeSeconds: 120,
});

test('C5 cookie contract: refresh and family HttpOnly, Secure, Strict, host-only', () => {
  const rows = candidateRefreshCookieHeaders(candidate);
  assert.equal(rows.length, 3);
  for (const header of rows) {
    assert.match(header, /; Secure; SameSite=Strict; Max-Age=120$/);
    assert.doesNotMatch(header, /(?:^|;\s*)Domain=/i);
    assert.doesNotMatch(header, /SameSite=None|SameSite=Lax/i);
    assert.doesNotMatch(header, /Expires=/i);
  }
  for (const row of rows.slice(0, 2)) {
    assert.match(row, /; Path=\/api\/v1\/auth\/refresh; HttpOnly; Secure/);
  }
  assert.match(rows[2], /^iamina_refresh_csrf=c2\./);
  assert.match(rows[2], /; Path=\/; Secure/);
  assert.doesNotMatch(rows[2], /HttpOnly/);
  assert.ok(!rows[2].includes(secret), 'CSRF cookie must not contain raw refresh');
});

test('C5 policy demands explicit test flag, sane opaque values and finite TTL', () => {
  const bad = [
    { enabled: false }, { enabled: undefined }, { familyId: '0' },
    { familyId: '1; Domain=attacker.invalid' },
    { refreshSecret: secret + '; HttpOnly=false' },
    { csrfToken: 'unsigned' }, { maxAgeSeconds: 0 },
    { maxAgeSeconds: 901 }, { maxAgeSeconds: '120' },
    { maxAgeSeconds: Number.NaN }, { maxAgeSeconds: Infinity },
  ];
  for (const change of bad) {
    assert.throws(
      () => candidateRefreshCookieHeaders({ ...candidate, ...change }),
      /unavailable/,
    );
  }
});

test('C5 logout expires same names, paths and security flags; never returns bearer', () => {
  const rows = candidateLogoutCookieHeaders({ enabled: true });
  assert.equal(rows.length, 3);
  rows.forEach(row => {
    assert.match(row, /; Secure; SameSite=Strict; Max-Age=0$/);
    assert.doesNotMatch(row, /Domain=/i);
    assert.doesNotMatch(row, /iamina-web\.|iamina-wr1\./);
  });
  assert.match(rows[0], /^iamina_refresh=; Path=\/api\/v1\/auth\/refresh; HttpOnly;/);
  assert.match(rows[1], /^iamina_refresh_family=; Path=\/api\/v1\/auth\/refresh; HttpOnly;/);
  assert.match(rows[2], /^iamina_refresh_csrf=; Path=\/; Secure;/);
  assert.throws(() => candidateLogoutCookieHeaders(), /unavailable/);
});

test('C5 cookie policy remains unused by deployed BFF route and auto-deploy stays off', () => {
  const root = path.join(__dirname, '..');
  const live = fs.readFileSync(path.join(root, 'frontend/api/session-refresh.js'), 'utf8');
  assert.doesNotMatch(live, /w02_f09c5_cookie_policy/);
  assert.match(live, /reject\(res, 404\)/);
  const config = JSON.parse(fs.readFileSync(
    path.join(root, 'frontend/vercel.json'), 'utf8',
  ));
  assert.equal(config.git.deploymentEnabled, false);
  assert.equal(config.rewrites[0].source, '/api/v1/auth/refresh');
});
