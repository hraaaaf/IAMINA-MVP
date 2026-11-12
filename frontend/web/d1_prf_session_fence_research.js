/* IAMINA D1-6 — research-only Web client session fence.
 * NO patient wiring, NO backend route, NO Vercel deploy, NO clinical authorization.
 *
 * getVerifiedScope MUST eventually call an authenticated same-origin Django
 * endpoint and MUST NOT trust browser-provided owner/account/session fields.
 * That endpoint does NOT exist in this branch: this module cannot establish
 * identity or authorize a patient vault on its own.
 *
 * This fence handles cancellation, stale async WebAuthn results and best-effort
 * zeroization of its own typed-array view. It cannot defend against XSS,
 * copied keys, malicious callbacks, or vault mutations performed in a callback.
 * readOnly is intended exclusively for synthetic and nonmutating operations.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IaminaD1SessionFenceResearch = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const EVENT_TYPE = 'IAMINA_D1_RESEARCH_INVALIDATE_V1';
  const OWNER_PATTERN = /^amina_vault_v1_(?:native_[1-9]\d*|device_[a-f0-9]{32})$/;
  const FAIL = 'D1_RESEARCH_SESSION_FENCE_DENIED';

  function denied() { throw new Error(FAIL); }
  function plainObject(x) {
    return x !== null && typeof x === 'object' && !Array.isArray(x);
  }
  function validateScope(x, origin) {
    // All fields are meant to originate from an authenticated, CSRF-aware
    // Django identity endpoint. A JS object itself proves NOTHING.
    if (!plainObject(x) ||
        typeof x.accountId !== 'string' || !/^[1-9]\d{0,18}$/.test(x.accountId) ||
        typeof x.owner !== 'string' || !OWNER_PATTERN.test(x.owner) ||
        typeof x.sessionBinding !== 'string' || !/^[a-f0-9]{64}$/.test(x.sessionBinding) ||
        !Number.isSafeInteger(x.accountEpoch) || x.accountEpoch < 0 ||
        typeof x.credentialId !== 'string' || !/^[A-Za-z0-9_-]{2,1024}$/.test(x.credentialId) ||
        x.origin !== origin || typeof x.authenticated !== 'boolean' || !x.authenticated) denied();
    // Normalize and copy only non-secret scope metadata.
    return Object.freeze({
      accountId: x.accountId, owner: x.owner,
      sessionBinding: x.sessionBinding, accountEpoch: x.accountEpoch,
      credentialId: x.credentialId, origin: x.origin,
    });
  }
  function same(a, b) {
    return a && b && a.accountId === b.accountId && a.owner === b.owner &&
      a.sessionBinding === b.sessionBinding && a.accountEpoch === b.accountEpoch &&
      a.credentialId === b.credentialId && a.origin === b.origin;
  }

  function create({getVerifiedScope, gate, origin, channel, lifecycle}) {
    if (typeof getVerifiedScope !== 'function' ||
        !gate || typeof gate.unlock !== 'function' ||
        typeof origin !== 'string' || !/^https:\/\/[a-zA-Z0-9.-]+$/.test(origin) ||
        !channel || typeof channel.postMessage !== 'function' ||
        typeof channel.addEventListener !== 'function' ||
        typeof channel.removeEventListener !== 'function' ||
        !lifecycle || typeof lifecycle.addEventListener !== 'function' ||
        typeof lifecycle.removeEventListener !== 'function') denied();

    let generation = 0;
    let closed = false;
    let busy = false;
    let heldKey = null;
    let controller = null;

    function localInvalidate(broadcast) {
      generation++;
      if (controller) controller.abort();
      if (heldKey) heldKey.fill(0);
      heldKey = null;
      if (broadcast) channel.postMessage({type: EVENT_TYPE, origin});
    }
    function onMessage(event) {
      if (event && event.data && event.data.type === EVENT_TYPE && event.data.origin === origin)
        localInvalidate(false);
    }
    function onPageHide() { localInvalidate(false); }
    function onPageShow(event) { if (event && event.persisted) localInvalidate(false); }
    channel.addEventListener('message', onMessage);
    lifecycle.addEventListener('pagehide', onPageHide);
    lifecycle.addEventListener('pageshow', onPageShow);

    async function scope() {
      try { return validateScope(await getVerifiedScope(), origin); }
      catch (_) { denied(); }
    }
    function assertCurrent(mark, signal) {
      if (closed || generation !== mark || signal.aborted) denied();
    }
    async function readOnly(operation) {
      if (closed || busy || typeof operation !== 'function') denied();
      busy = true;
      const mark = generation;
      const cancel = new AbortController();
      controller = cancel;
      let key;
      try {
        const before = await scope();
        assertCurrent(mark, cancel.signal);
        key = await gate.unlock(before.owner); // Face ID/PRF must be implemented by the gate.
        if (!(key instanceof Uint8Array) || key.length !== 32) denied();
        heldKey = key;
        assertCurrent(mark, cancel.signal);
        const after = await scope();
        assertCurrent(mark, cancel.signal);
        if (!same(before, after)) denied();
        const result = await operation(key, Object.freeze({
          accountId: before.accountId, owner: before.owner,
          credentialId: before.credentialId, signal: cancel.signal,
        }));
        assertCurrent(mark, cancel.signal);
        const final = await scope();
        assertCurrent(mark, cancel.signal);
        if (!same(before, final)) denied();
        // Do not let a caller accidentally return a buffer containing a copy
        // of key material. This is not a general-purpose data leak filter.
        if (result instanceof Uint8Array || result instanceof ArrayBuffer) denied();
        return result;
      } finally {
        if (key instanceof Uint8Array) key.fill(0);
        heldKey = null;
        if (controller === cancel) controller = null;
        busy = false;
      }
    }
    function invalidate() {
      if (closed) return;
      localInvalidate(true);
    }
    function close() {
      if (closed) return;
      localInvalidate(true);
      closed = true;
      channel.removeEventListener('message', onMessage);
      lifecycle.removeEventListener('pagehide', onPageHide);
      lifecycle.removeEventListener('pageshow', onPageShow);
    }
    return Object.freeze({readOnly, invalidate, close});
  }
  return Object.freeze({create, EVENT_TYPE});
});
