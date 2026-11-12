/* IAMINA D1-6 — single research-only client session fence.
 * NOT mounted by Flutter/PWA and NOT authorized for patient data.
 * readServerSession must eventually call a SAME-ORIGIN authenticated Django
 * session-context endpoint; an injected JS object is NOT authentication.
 * prfUnlock must eventually use WebAuthn PRF output tied to a server-verified
 * assertion for that same credential; no such E2E wiring exists today.
 * No KEK, DEK or PRF output may be persisted/transmitted by this module.
 * Zeroization is best effort: JS callbacks/XSS can copy or misuse raw bytes.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.iaminaD1ResearchSessionFence = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';

  const OWNER = /^amina_vault_v1_(?:native_[1-9]\d*|device_[a-f0-9]{32})$/;
  const HEX64 = /^[a-f0-9]{64}$/;
  const CREDENTIAL = /^[A-Za-z0-9_-]{2,1024}$/;
  const INVALIDATION = 'IAMINA_D1_RESEARCH_INVALIDATE_V1';

  function denied(code) {
    const err = new Error(code);
    err.name = 'D1ResearchSessionFenceDenied';
    return err;
  }

  function validate(snapshot, origin) {
    if (!snapshot || typeof snapshot !== 'object' ||
        snapshot.authenticated !== true || snapshot.patientReady !== false ||
        !Number.isSafeInteger(snapshot.epoch) || snapshot.epoch < 0 ||
        typeof snapshot.accountId !== 'string' ||
        !/^[1-9]\d{0,18}$/.test(snapshot.accountId) ||
        typeof snapshot.sessionStamp !== 'string' ||
        !HEX64.test(snapshot.sessionStamp) ||
        typeof snapshot.vaultOwner !== 'string' ||
        !OWNER.test(snapshot.vaultOwner) ||
        typeof snapshot.credentialId !== 'string' ||
        !CREDENTIAL.test(snapshot.credentialId) ||
        snapshot.origin !== origin) {
      throw denied('D1_RESEARCH_UNTRUSTED_SESSION');
    }
    return JSON.stringify([
      snapshot.accountId, snapshot.sessionStamp, snapshot.epoch,
      snapshot.vaultOwner, snapshot.credentialId, snapshot.origin
    ]);
  }

  function createSessionFence({
    readServerSession, prfUnlock, expectedOrigin, channel, lifecycle
  } = {}) {
    if (typeof readServerSession !== 'function' ||
        typeof prfUnlock !== 'function' ||
        typeof expectedOrigin !== 'string' ||
        !/^https:\/\/[a-zA-Z0-9.-]+$/.test(expectedOrigin) ||
        !channel || typeof channel.postMessage !== 'function' ||
        typeof channel.addEventListener !== 'function' ||
        typeof channel.removeEventListener !== 'function' ||
        !lifecycle || typeof lifecycle.addEventListener !== 'function' ||
        typeof lifecycle.removeEventListener !== 'function') {
      throw denied('D1_RESEARCH_FENCE_BAD_CONFIG');
    }

    let generation = 0;
    let boundScope = null;
    let destroyed = false;
    let busy = false;
    let activeKey = null;
    let activeAbort = null;

    function wipe() {
      if (activeAbort) activeAbort.abort();
      if (activeKey) activeKey.fill(0);
      activeKey = null;
    }
    function invalidate(broadcast = false) {
      generation++;
      wipe();
      boundScope = null;
      if (broadcast) channel.postMessage({type: INVALIDATION, origin: expectedOrigin});
    }
    function onMessage(event) {
      if (event?.data?.type === INVALIDATION &&
          event.data.origin === expectedOrigin) invalidate(false);
    }
    function onPageHide() { invalidate(true); }
    function onPageShow(event) {
      if (event?.persisted === true) invalidate(true);
    }
    channel.addEventListener('message', onMessage);
    lifecycle.addEventListener('pagehide', onPageHide);
    lifecycle.addEventListener('pageshow', onPageShow);

    function assertCurrent(ticket, signal) {
      if (destroyed || ticket !== generation || signal.aborted) {
        throw denied('D1_RESEARCH_STALE_OPERATION');
      }
    }
    async function liveSnapshot(ticket, signal) {
      assertCurrent(ticket, signal);
      let snapshot;
      try {
        snapshot = await readServerSession();
      } catch (_) {
        throw denied('D1_RESEARCH_SESSION_UNAVAILABLE');
      }
      assertCurrent(ticket, signal);
      return {snapshot, scope: validate(snapshot, expectedOrigin)};
    }

    async function withUnlockedKey(operation) {
      if (destroyed || typeof operation !== 'function') {
        throw denied('D1_RESEARCH_FENCE_UNAVAILABLE');
      }
      // Never produce simultaneous Face ID prompts or share a DEK between
      // overlapping research operations. A second request is rejected.
      if (busy) throw denied('D1_RESEARCH_FENCE_BUSY');
      busy = true;
      const ticket = ++generation;
      const abort = new AbortController();
      activeAbort = abort;
      let key;
      try {
        const before = await liveSnapshot(ticket, abort.signal);
        if (boundScope !== null && before.scope !== boundScope) {
          invalidate(true);
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        boundScope = before.scope;
        key = await prfUnlock(before.snapshot.vaultOwner, {signal: abort.signal});
        if (!(key instanceof Uint8Array) || key.byteLength !== 32 ||
            key.every(x => x === 0)) {
          throw denied('D1_RESEARCH_BAD_KEY_MATERIAL');
        }
        activeKey = key;
        assertCurrent(ticket, abort.signal);
        const afterUnlock = await liveSnapshot(ticket, abort.signal);
        if (afterUnlock.scope !== before.scope) {
          invalidate(true);
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        // Nonclinical in-memory callback only; caller can copy the key, so
        // this is NOT a malicious-JS/XSS security boundary.
        await operation(key, Object.freeze({
          accountId: before.snapshot.accountId,
          vaultOwner: before.snapshot.vaultOwner,
          credentialId: before.snapshot.credentialId,
          signal: abort.signal,
          patientReady: false
        }));
        assertCurrent(ticket, abort.signal);
        const afterOperation = await liveSnapshot(ticket, abort.signal);
        if (afterOperation.scope !== before.scope) {
          invalidate(true);
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        assertCurrent(ticket, abort.signal);
        // Intentionally discard callback results, especially byte arrays.
        return Object.freeze({
          status: 'D1_RESEARCH_FIXTURE_COMPLETE', patientReady: false
        });
      } finally {
        if (key instanceof Uint8Array) key.fill(0);
        if (activeKey === key) activeKey = null;
        if (activeAbort === abort) activeAbort = null;
        busy = false;
      }
    }

    // The eventual app must trigger these on logout, account switch,
    // revocation, BroadcastChannel message, pagehide and BFCache restore.
    function sessionChanged() {
      if (!destroyed) invalidate(true);
    }
    function destroy() {
      if (destroyed) return;
      invalidate(true);
      destroyed = true;
      channel.removeEventListener('message', onMessage);
      lifecycle.removeEventListener('pagehide', onPageHide);
      lifecycle.removeEventListener('pageshow', onPageShow);
    }
    return Object.freeze({withUnlockedKey, sessionChanged, destroy});
  }

  return Object.freeze({createSessionFence, INVALIDATION});
});
