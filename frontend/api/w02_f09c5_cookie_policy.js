'use strict';

// W02-F09-C5: PURE cookie policy candidate, NOT used by a live route.
// It serializes proposed HOST-ONLY cookie attributes but does not set any
// response header, access Django/Neon, perform fetch, or activate refresh.
// TTL is mandatory, and represents a SYNTHETIC test value, not patient policy.
const SECRET = /^iamina-wr1\.[A-Za-z0-9_-]{64}$/;
const CSRF = /^c2\.[0-9]{10}\.[A-Za-z0-9_-]{24}\.[0-9a-f]{64}$/;
const FAMILY = /^[1-9][0-9]{0,15}$/;

function reject() {
  throw new Error('Web refresh cookie candidate unavailable');
}

function candidateRefreshCookieHeaders(options = {}) {
  const { enabled, familyId, refreshSecret, csrfToken, maxAgeSeconds } = options;
  if (enabled !== true || typeof familyId !== 'string' || !FAMILY.test(familyId) ||
      typeof refreshSecret !== 'string' || !SECRET.test(refreshSecret) ||
      typeof csrfToken !== 'string' || !CSRF.test(csrfToken) ||
      !Number.isSafeInteger(maxAgeSeconds) ||
      maxAgeSeconds < 1 || maxAgeSeconds > 900) reject();

  // Explicitly host-only: NEVER include Domain. The refresh secret and family
  // locator are HTTP-only and path-constrained. JavaScript may read ONLY the
  // CSRF token for same-origin double-submit; Django checks its family MAC.
  const common = '; Secure; SameSite=Strict; Max-Age=' + maxAgeSeconds;
  return Object.freeze([
    'iamina_refresh=' + refreshSecret + '; Path=/api/v1/auth/refresh; HttpOnly' + common,
    'iamina_refresh_family=' + familyId + '; Path=/api/v1/auth/refresh; HttpOnly' + common,
    'iamina_refresh_csrf=' + csrfToken + '; Path=/' + common,
  ]);
}

function candidateLogoutCookieHeaders(options = {}) {
  if (options.enabled !== true) reject();
  return Object.freeze([
    'iamina_refresh=; Path=/api/v1/auth/refresh; HttpOnly; Secure; SameSite=Strict; Max-Age=0',
    'iamina_refresh_family=; Path=/api/v1/auth/refresh; HttpOnly; Secure; SameSite=Strict; Max-Age=0',
    'iamina_refresh_csrf=; Path=/; Secure; SameSite=Strict; Max-Age=0',
  ]);
}

module.exports = { candidateRefreshCookieHeaders, candidateLogoutCookieHeaders };
