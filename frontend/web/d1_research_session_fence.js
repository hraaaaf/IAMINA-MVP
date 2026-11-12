/* IAMINA D1-6: experimental client session/identity fence.
 * NOT wired into Flutter, WebAuthn, patient routing or clinical storage.
 * It cannot authenticate a Django account, verify a WebAuthn signature,
 * provide cross-tab events, or certify PRF. Those gates remain separate.
 * No KEK/DEK is persisted by this module.
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

  function denied(code) {
    const err = new Error(code);
    err.name = 'D1ResearchSessionFenceDenied';
    return err;
  }

  function validate(snapshot, origin) {
    // Future readServerSession MUST read an authenticated, CSRF-protected
    // Django endpoint over the pinned same-origin; client JSON is not proof.
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
      snapshot.accountId,
      snapshot.sessionStamp,
      snapshot.epoch,
      snapshot.vaultOwner,
      snapshot.credentialId,
      snapshot.origin
    ]);
  }

  function createSessionFence({ readServerSession, prfUnlock, expectedOrigin } = {}) {
    if (typeof readServerSession !== 'function' ||
        typeof prfUnlock !== 'function' ||
        typeof expectedOrigin !== 'string' ||
        !/^https:\/\/[^/?#@]+$/.test(expectedOrigin)) {
      throw denied('D1_RESEARCH_FENCE_BAD_CONFIG');
    }

    let generation = 0;
    let boundScope = null;
    let destroyed = false;
    const active = new Set();

    function clearKeys() {
      for (const key of active) key.fill(0);
      active.clear();
    }
    function invalidate({ forgetScope = true } = {}) {
      generation++;
      clearKeys();
      if (forgetScope) boundScope = null;
    }
    function assertGeneration(ticket) {
      if (destroyed || ticket !== generation) {
        throw denied('D1_RESEARCH_STALE_OPERATION');
      }
    }
    async function liveSnapshot(ticket) {
      assertGeneration(ticket);
      let snapshot;
      try {
        snapshot = await readServerSession();
      } catch (_) {
        throw denied('D1_RESEARCH_SESSION_UNAVAILABLE');
      }
      assertGeneration(ticket);
      const scope = validate(snapshot, expectedOrigin);
      return { snapshot, scope };
    }

    async function withUnlockedKey(operation) {
      if (destroyed || typeof operation !== 'function') {
        throw denied('D1_RESEARCH_FENCE_UNAVAILABLE');
      }
      // One active ceremony at a time. Starting a new one invalidates the
      // previous one, even if the previous one is awaiting Face ID.
      invalidate({ forgetScope: false });
      const ticket = generation;
      let key;
      try {
        const before = await liveSnapshot(ticket);
        if (boundScope !== null && before.scope !== boundScope) {
          invalidate();
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        boundScope = before.scope;
        key = await prfUnlock(before.snapshot.vaultOwner);
        if (!(key instanceof Uint8Array) || key.byteLength !== 32) {
          throw denied('D1_RESEARCH_BAD_KEY_MATERIAL');
        }
        active.add(key);
        assertGeneration(ticket);
        const afterUnlock = await liveSnapshot(ticket);
        if (afterUnlock.scope !== before.scope) {
          invalidate();
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        assertGeneration(ticket);
        // Callback permitted ONLY for nonclinical in-memory fixture operations.
        // It may not persist/copy the key. JS alone cannot enforce this rule.
        await operation(key, Object.freeze({
          accountId: before.snapshot.accountId,
          vaultOwner: before.snapshot.vaultOwner,
          credentialId: before.snapshot.credentialId,
          patientReady: false
        }));
        assertGeneration(ticket);
        const afterOperation = await liveSnapshot(ticket);
        if (afterOperation.scope !== before.scope) {
          invalidate();
          throw denied('D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED');
        }
        assertGeneration(ticket);
        // Never return callback results: they could accidentally leak a DEK.
        return Object.freeze({ status: 'D1_RESEARCH_FIXTURE_COMPLETE', patientReady: false });
      } finally {
        if (key instanceof Uint8Array) {
          key.fill(0);
          active.delete(key);
        }
      }
    }

    // The embedding application MUST invoke this on logout, account switch,
    // credential revocation, cross-tab message, BFCache restore and unload.
    // This module is not linked to any clinical app; missing event wiring is
    // an explicit E2E certification blocker.
    function sessionChanged() { invalidate(); }
    function destroy() { invalidate(); destroyed = true; }

    return Object.freeze({ withUnlockedKey, sessionChanged, destroy });
  }

  return Object.freeze({ createSessionFence });
});
