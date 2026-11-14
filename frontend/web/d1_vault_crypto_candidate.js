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
  // D1 candidate: no browser-local token can substitute for origin-wide
  // mutual exclusion. Web Locks serializes tabs and workers on this origin.
  // This does NOT stop an already installed offline legacy PWA (which does
  // not participate in this protocol).
  const activeLeases = new Map();
  const ownerPattern = /^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$/;

  async function acquireExclusiveLease(owner) {
    if (typeof owner !== 'string' || !ownerPattern.test(owner)) {
      throw Error('D1_VAULT_LOCK_OWNER_INVALID');
    }
    if (!globalThis.isSecureContext || !navigator.locks?.request ||
        !crypto.randomUUID) {
      throw Error('D1_VAULT_WEB_LOCKS_UNSUPPORTED');
    }
    let grant, deny;
    const acquired = new Promise((resolve, reject) => {
      grant = resolve;
      deny = reject;
    });
    // Deliberately ifAvailable: no queued lock request may wake later with
    // an unexpectedly stale authentication or recovery state.
    let task;
    try {
      task = navigator.locks.request('iamina-d1-exclusive-v1-' + owner,
        {mode: 'exclusive', ifAvailable: true}, (lock) => {
          if (!lock) {
            deny(Error('D1_VAULT_TAB_BUSY'));
            return;
          }
          let unlock;
          const held = new Promise(resolve => { unlock = resolve; });
          const token = crypto.randomUUID();
          activeLeases.set(token, {owner, unlock, done: null});
          grant(token);
          // Hold for the complete SQLite connection lifetime, not only
          // while a SELECT/INSERT is running.
          return held;
        });
      task.catch(deny);
    } catch (error) {
      deny(error);
    }
    const token = await acquired;
    const record = activeLeases.get(token);
    if (!record || !task) throw Error('D1_VAULT_TAB_LEASE_LOST');
    record.done = task;
    return token;
  }

  async function releaseExclusiveLease(owner, token) {
    const record = activeLeases.get(token);
    if (!record || record.owner !== owner) {
      throw Error('D1_VAULT_LEASE_TOKEN_INVALID');
    }
    activeLeases.delete(token);
    record.unlock();
    // Wait for Web Locks to finish releasing before allowing re-enrollment.
    await record.done;
    return 'released';
  }

  async function indexedDbNames() {
    if (typeof indexedDB.databases !== 'function') {
      throw Error('D1_INDEXEDDB_INVENTORY_UNSUPPORTED');
    }
    return JSON.stringify((await indexedDB.databases()).map(x => x.name || ''));
  }
  Object.defineProperty(globalThis, 'IaminaD1CryptoCandidate', {
    value: Object.freeze({encrypt, decrypt, indexedDbNames,
      acquireExclusiveLease, releaseExclusiveLease}),
    configurable: false, writable: false,
  });
})();
