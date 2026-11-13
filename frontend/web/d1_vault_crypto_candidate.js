// D1 candidate only. No patient admission, no key telemetry or storage here.
// Native browser WebCrypto (PBKDF2 SHA-256 and AES-256-GCM), owner-bound AAD.
(() => {
  'use strict';
  const format = 'iamina-d1-aes-gcm-owner-bound-v1';
  const iterations = 310000;
  const enc = new TextEncoder();
  function decode(text) {
    const s = text.replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(s + '='.repeat((4 - s.length % 4) % 4));
    return Uint8Array.from(bin, x => x.charCodeAt(0));
  }
  function encode(bytes) {
    let s = '';
    for (const byte of bytes) s += String.fromCharCode(byte);
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  }
  async function wrapper(recovery, salt) {
    if (!globalThis.isSecureContext) throw Error('D1_REQUIRES_SECURE_CONTEXT');
    const base = await crypto.subtle.importKey(
      'raw', decode(recovery), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey(
      {name: 'PBKDF2', salt: decode(salt), iterations, hash: 'SHA-256'},
      base, {name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']);
  }
  function params(iv, owner) {
    return {name: 'AES-GCM', iv: decode(iv),
      additionalData: enc.encode(format + '/' + owner), tagLength: 128};
  }
  async function encrypt(recovery, key, salt, iv, owner) {
    const wrapping = await wrapper(recovery, salt);
    const out = await crypto.subtle.encrypt(params(iv, owner), wrapping, decode(key));
    return encode(new Uint8Array(out));
  }
  async function decrypt(recovery, ciphertext, salt, iv, owner) {
    const wrapping = await wrapper(recovery, salt);
    const out = await crypto.subtle.decrypt(
      params(iv, owner), wrapping, decode(ciphertext));
    return encode(new Uint8Array(out));
  }
  async function indexedDbNames() {
    if (typeof indexedDB.databases !== 'function') {
      throw Error('D1_INDEXEDDB_INVENTORY_UNSUPPORTED');
    }
    return JSON.stringify((await indexedDB.databases()).map(x => x.name || ''));
  }
  Object.defineProperty(globalThis, 'IaminaD1CryptoCandidate', {
    value: Object.freeze({encrypt, decrypt, indexedDbNames}),
    configurable: false, writable: false,
  });
})();
