'use strict';

// W02 C7: unmounted signed Django -> BFF reply verifier.
// This module NEVER makes fetch, sets real cookies, or imports a Vercel route.
// The BFF response secret is separated from the BFF request/CSRF keys.
const {createHash, createHmac, timingSafeEqual} = require('node:crypto');
const {
  composeCandidateBffRefreshResult,
} = require('./w02_f09c6_response_candidate.js');

const SCOPE = 'iamina.web.c7.signed-response.v1';
const HEX_PROOF = /^v1\.[0-9a-f]{64}$/;
const KEY = /^[A-Za-z0-9_-]{32,128}$/;
const NONCE = /^[A-Za-z0-9_-]{43}$/;
const TIMESTAMP = /^[1-9][0-9]{9}$/;
const FIELDS = [
  'accessBearer', 'accessMaxAgeSeconds', 'cookieMaxAgeSeconds',
  'csrfToken', 'familyId', 'refreshSecret',
];

function deny() {
  throw new Error('Signed Web refresh result unavailable');
}

function verifyCandidateC7BackendResult({
  enabled,
  upstream,
  originalSignedHeaders,
  responseHmacKey,
} = {}) {
  if (enabled !== true || !upstream ||
      upstream.status !== 200 || !Buffer.isBuffer(upstream.body) ||
      upstream.body.length < 1 || upstream.body.length > 4096 ||
      !upstream.headers || !originalSignedHeaders ||
      typeof responseHmacKey !== 'string' || !KEY.test(responseHmacKey)) deny();

  const h = upstream.headers;
  if (h['content-type'] !== 'application/json' ||
      h['cache-control'] !== 'no-store' ||
      h['set-cookie'] !== undefined ||
      h['authorization'] !== undefined ||
      !HEX_PROOF.test(h['x-iamina-c7-reply-proof'] || '')) deny();

  const nonce = originalSignedHeaders['x-iamina-bff-nonce'];
  const ts = originalSignedHeaders['x-iamina-bff-timestamp'];
  if (!NONCE.test(nonce || '') || !TIMESTAMP.test(ts || '')) deny();

  const canonical = [
    SCOPE, 'POST', '/api/v1/auth/refresh', ts, nonce,
    createHash('sha256').update(upstream.body).digest('hex'),
  ].join('\n');
  const expected = 'v1.' + createHmac('sha256', responseHmacKey)
    .update(canonical, 'ascii').digest('hex');
  const received = h['x-iamina-c7-reply-proof'];
  if (!timingSafeEqual(
    Buffer.from(expected, 'ascii'), Buffer.from(received, 'ascii'),
  )) deny();

  // Accept only the canonical exact JSON encoding. Duplicate keys, unknown
  // fields, whitespace variants and other parsing ambiguities are rejected.
  let data;
  try {
    const raw = upstream.body.toString('utf8');
    data = JSON.parse(raw);
    if (!data || Array.isArray(data) || typeof data !== 'object' ||
        Object.keys(data).join('|') !== FIELDS.join('|') ||
        raw !== JSON.stringify(data)) deny();
  } catch {
    deny();
  }

  try {
    return composeCandidateBffRefreshResult(data, {enabled: true});
  } catch {
    deny();
  }
}

module.exports = {verifyCandidateC7BackendResult};
