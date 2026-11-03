// D18 source interlock CANARY — cooperative locks only, NOT a patient cutover.
// Old tabs without this code remain non-cooperative; no migration is authorized.
(() => {
  'use strict';
  const root = 'iamina:d18:precutover:source:v1:';
  const patientName = /^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$/;
  const held = new Map();

  async function acquire(requests) {
    if (!navigator.locks || typeof navigator.locks.request !== 'function' ||
        !globalThis.crypto || typeof crypto.randomUUID !== 'function') {
      throw Error('D18_SOURCE_LOCK_UNSUPPORTED');
    }
    let grant, release;
    const granted = new Promise(resolve => { grant = resolve; });
    const untilReleased = new Promise(resolve => { release = resolve; });
    let notified = false;
    let unexpectedlyEnded = false;
    const notify = accepted => {
      if (!notified) { notified = true; grant(accepted); }
    };
    async function nested(index) {
      if (index === requests.length) {
        notify(true);
        await untilReleased;
        return;
      }
      const [name, mode] = requests[index];
      await navigator.locks.request(name, {mode, ifAvailable: true}, async lock => {
        if (!lock) { notify(false); return; }
        await nested(index + 1);
      });
    }
    const running = nested(0).catch(() => {
      unexpectedlyEnded = true;
      notify(false);
    });
    if (!await granted) {
      await running;
      throw Error('D18_SOURCE_LOCK_DENIED');
    }
    const slot = crypto.randomUUID();
    held.set(slot, {
      release,
      running,
      failed: () => unexpectedlyEnded,
    });
    return slot;
  }

  globalThis.IAMINA_D18_SOURCE_BARRIER = Object.freeze({
    acquireLegacy: () => acquire([[root + 'legacy', 'shared']]),
    // Synthetic guest audit namespace is a physical SQLite writer, never a
    // clinical patient source; it must participate in canary lock discipline.
    acquireAuditGuest: () => acquire([[root + 'audit-guest', 'shared']]),
    acquirePatient: scope => {
      if (typeof scope !== 'string' || !patientName.test(scope)) {
        throw Error('D18_SOURCE_SCOPE_DENIED');
      }
      return acquire([[root + 'patient:' + scope, 'shared']]);
    },
    release: async slot => {
      if (typeof slot !== 'string' || !held.has(slot)) {
        throw Error('D18_SOURCE_INVALID_RELEASE');
      }
      const lease = held.get(slot);
      held.delete(slot);
      lease.release();
      await lease.running;
      if (lease.failed()) throw Error('D18_SOURCE_LOCK_LOST');
      return true;
    },
  });
})();
