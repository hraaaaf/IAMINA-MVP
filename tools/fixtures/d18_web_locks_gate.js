// D18 CI ONLY. Synthetic multi-tab Web Locks gate, never imported by app.
// This is an arbitration test, NOT enforcement in the clinical SQLite runtime.
(() => {
  'use strict';
  const namePattern = /^amina_vault_v1_device_[0-9a-f]{32}_d18_ci_dynamic$/;

  async function acquire(vaultName) {
    if (typeof vaultName !== 'string' || !namePattern.test(vaultName)) {
      return {ok: false, reason: 'INVALID_SCOPE'};
    }
    if (!navigator.locks || typeof navigator.locks.request !== 'function') {
      return {ok: false, reason: 'UNSUPPORTED'};
    }

    let resolveGranted;
    let resolveRelease;
    const granted = new Promise(resolve => { resolveGranted = resolve; });
    const held = new Promise(resolve => { resolveRelease = resolve; });
    let closed = false;
    const name = 'iamina:d18:ci:v1:' + vaultName;
    const task = navigator.locks.request(name, {
      mode: 'exclusive',
      ifAvailable: true,
    }, async lock => {
      if (!lock) {
        resolveGranted(false);
        return;
      }
      resolveGranted(true);
      await held;
    }).catch(() => {
      resolveGranted(false);
    });

    if (!await granted) {
      await task;
      return {ok: false, reason: 'LOCK_UNAVAILABLE'};
    }

    return {
      ok: true,
      release: async () => {
        if (closed) return;
        closed = true;
        resolveRelease();
        await task;
      },
    };
  }

  Object.defineProperty(globalThis, 'D18SyntheticVaultLockGate', {
    value: Object.freeze({acquire}),
    configurable: false,
    writable: false,
  });
})();
