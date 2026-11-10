// D18 CI ONLY: Web Locks lease held for actual sqlite3mc worker lifetime.
// Never ship or reference from the clinical application.
(() => {
  'use strict';
  const valid = /^amina_vault_v1_device_[0-9a-f]{32}_d18_ci_dynamic$/;
  globalThis.__d18AcquireWorkerLock = async name => {
    if (typeof name !== 'string' || !valid.test(name) ||
        !navigator.locks || typeof navigator.locks.request !== 'function') {
      return {ok: false};
    }
    let grant, release;
    const granted = new Promise(resolve => { grant = resolve; });
    const held = new Promise(resolve => { release = resolve; });
    const task = navigator.locks.request('iamina:d18:ci:v1:' + name, {
      mode: 'exclusive', ifAvailable: true,
    }, async lock => {
      if (!lock) { grant(false); return; }
      grant(true);
      await held;
    }).catch(() => { grant(false); });
    if (!await granted) {
      await task;
      return {ok: false};
    }
    let closed = false;
    return {
      ok: true,
      release: async () => {
        if (closed) return;
        closed = true;
        release();
        await task;
      },
    };
  };
})();
