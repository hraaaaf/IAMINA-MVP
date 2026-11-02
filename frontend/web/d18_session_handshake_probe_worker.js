// D18 disposable browser-only key handoff experiment.
// NOT a Drift/sqlite3 worker; NOT production key management.
// Never import this script from the IAMINA application runtime.
'use strict';

let active = null;
let opening = false;
const encoder = new TextEncoder();
const namespace = /^amina_vault_v1_device_[0-9a-f]{32}$/;
const sessionPattern = /^[0-9a-f-]{36}$/;

function answer(port, id, code, more = {}) {
  port.postMessage({id, code, ...more});
}
function hex(input) {
  return Array.from(new Uint8Array(input), b => b.toString(16).padStart(2, '0')).join('');
}

self.addEventListener('message', event => {
  if (event.data?.type !== 'D18_ATTACH' || event.ports.length !== 1) return;
  const port = event.ports[0];
  port.onmessage = async event => {
    const m = event.data;
    if (!m || typeof m !== 'object' || typeof m.id !== 'string') return;
    if (m.op === 'unlock') {
      if (active || opening) return answer(port, m.id, 'SESSION_ACTIVE');
      if (typeof m.scope !== 'string' || !namespace.test(m.scope) ||
          typeof m.session !== 'string' || !sessionPattern.test(m.session)) {
        return answer(port, m.id, 'INVALID_IDENTITY');
      }
      if (!(m.key instanceof ArrayBuffer) || m.key.byteLength !== 32) {
        return answer(port, m.id, 'KEY_LENGTH');
      }
      opening = true;
      try {
        // Raw key only lives transiently in a transferred, detached buffer.
        // The imported CryptoKey is non-extractable and kept in worker RAM.
        const keyBytes = new Uint8Array(m.key);
        const key = await crypto.subtle.importKey(
          'raw', keyBytes, {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']
        );
        keyBytes.fill(0);
        active = {port, key, scope: m.scope, session: m.session};
        answer(port, m.id, 'UNLOCKED');
      } catch (_) {
        answer(port, m.id, 'KEY_IMPORT_FAILED');
      } finally {
        opening = false;
      }
      return;
    }
    if (!active) return answer(port, m.id, 'LOCKED');
    if (port !== active.port) return answer(port, m.id, 'UNAUTHORIZED_PORT');
    if (m.scope !== active.scope) return answer(port, m.id, 'WRONG_SCOPE');
    if (m.session !== active.session) return answer(port, m.id, 'WRONG_SESSION');
    if (m.op === 'lock') {
      active = null;
      return answer(port, m.id, 'LOCKED');
    }
    if (m.op === 'proof') {
      // Protocol test only: HMAC proves receipt of a dynamic key, NOT SQLite encryption.
      if (typeof m.challenge !== 'string' ||
          m.challenge.length < 24 || m.challenge.length > 128) {
        return answer(port, m.id, 'INVALID_CHALLENGE');
      }
      try {
        const signature = await crypto.subtle.sign(
          'HMAC', active.key, encoder.encode(m.challenge)
        );
        return answer(port, m.id, 'PROOF', {mac: hex(signature)});
      } catch (_) {
        return answer(port, m.id, 'PROOF_FAILED');
      }
    }
    answer(port, m.id, 'UNKNOWN_OPERATION');
  };
  port.start();
});
