'use strict';

// W02-F09-C2 DRAFT helper only; NEVER imported by a live HTTP handler.
// A separate BFF-to-Django key must be provisioned on BOTH servers, never
// Django SECRET_KEY and never supplied by a browser. This signs an assertion
// about the *request*, not a patient or an authorization to renew.
const { createHash, createHmac, randomBytes } = require('node:crypto');

const WEB_HOST = /^[a-z0-9-]+\.vercel\.app$/;
const SIGNING_KEY = /^[A-Za-z0-9_-]{32,128}$/;
const PATH = '/api/v1/auth/refresh';
const SCOPE = 'iamina.web.refresh.bff.v1';

function signRefreshBoundary({ key, host, body, timestampSeconds, nonceBytes } = {}) {
  if (typeof key !== 'string' || !SIGNING_KEY.test(key)) {
    throw new Error('Refresh BFF signing unavailable');
  }
  if (typeof host !== 'string' || !WEB_HOST.test(host)) {
    throw new Error('Refresh BFF host unavailable');
  }
  if (!Buffer.isBuffer(body)) {
    throw new Error('Refresh BFF body unavailable');
  }
  if (body.length > 4096) {
    throw new Error('Refresh BFF request too large');
  }
  const ts = timestampSeconds === undefined
    ? Math.floor(Date.now() / 1000) : timestampSeconds;
  if (!Number.isSafeInteger(ts) || ts < 1000000000 || ts > 9999999999) {
    throw new Error('Refresh BFF clock unavailable');
  }
  const nonce = nonceBytes === undefined ? randomBytes(32) : nonceBytes;
  if (!Buffer.isBuffer(nonce) || nonce.length !== 32) {
    throw new Error('Refresh BFF nonce unavailable');
  }
  const nonceText = nonce.toString('base64url');
  const origin = 'https://' + host;
  const bodyDigest = createHash('sha256').update(body).digest('hex');
  const canonical = [
    SCOPE, 'POST', PATH, String(ts), nonceText, origin, bodyDigest,
  ].join('\n');
  const mac = createHmac('sha256', key).update(canonical, 'utf8').digest('hex');
  return Object.freeze({
    'x-iamina-bff-timestamp': String(ts),
    'x-iamina-bff-nonce': nonceText,
    'x-iamina-bff-origin': origin,
    'x-iamina-bff-proof': 'v1.' + mac,
  });
}

module.exports = { signRefreshBoundary };
