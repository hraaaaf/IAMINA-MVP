/**
 * W02 SYNTHETIC-ONLY: authenticated snapshot-to-volatile-SQLite coordinator.
 * Not imported by the application, not a patient authorization mechanism.
 *
 * Dependencies are deliberately injected: ownerSession.assertCurrent MUST be
 * bound to a freshly verified account epoch; revisionAuthority MUST be an
 * independently trusted and DURABLE monotone authority (never IndexedDB,
 * localStorage or an envelope field); memoryFactory MUST be memory-only Drift.
 * These requirements are NOT fulfilled by this module.
 *
 * Safety over availability: advance the trusted revision floor BEFORE the
 * IndexedDB CAS write. Crash/quota failure can make the vault unrecoverable
 * until independently authorized recovery. There is no cross-store atomicity.
 */
export class W02SessionError extends Error {
  constructor(code) { super(code); this.name = 'W02SessionError'; this.code = code; }
}
const deny = code => { throw new W02SessionError(code); };
const revisionOk = value => Number.isSafeInteger(value) && value >= 0;

export async function openSyntheticVaultSession({
  store, slot, vaultId, key, ownerSession, revisionAuthority,
  memoryFactory, allowSyntheticEmpty = false,
}) {
  if (!store || typeof store.restore !== 'function' || typeof store.commit !== 'function' ||
      !revisionAuthority || typeof revisionAuthority.getFloor !== 'function' ||
      typeof revisionAuthority.compareAndAdvance !== 'function' ||
      !memoryFactory || typeof memoryFactory.open !== 'function' ||
      !ownerSession || typeof ownerSession.assertCurrent !== 'function') {
    deny('missing_trusted_dependency');
  }
  const assertOwner = () => {
    // Deliberately synchronous: a Promise, undefined or stale epoch NEVER grants access.
    if (ownerSession.assertCurrent({ vaultId, slot }) !== true) deny('owner_session_changed');
  };
  assertOwner();
  const floor = await revisionAuthority.getFloor({ vaultId, slot });
  if (!revisionOk(floor)) deny('untrusted_revision_floor');
  assertOwner();

  let restored = await store.restore({
    slot, vaultId, minimumRevision: Math.max(1, floor), key,
  });
  let bytes = restored?.bytes ?? null;
  let memory;
  try {
    assertOwner();
    if (restored === null) {
      if (floor !== 0) deny('missing_known_snapshot');
      if (allowSyntheticEmpty !== true) deny('synthetic_creation_not_permitted');
    } else {
      if (floor === 0) deny('trusted_revision_floor_missing');
      if (restored.envelope?.revision !== floor || !(bytes instanceof Uint8Array)) {
        deny('revision_floor_out_of_sync');
      }
    }
    memory = await memoryFactory.open({ authenticatedSnapshot: bytes });
    assertOwner();
  } catch (err) {
    if (memory) await memory.close();
    throw err;
  } finally {
    if (bytes instanceof Uint8Array) bytes.fill(0);
    bytes = null;
    restored = null;
  }

  let expectedEnvelope = await store.readEnvelope(slot);
  // A second tab could commit between restore and readEnvelope. Never attach
  // an executor loaded with one version to another version's CAS token.
  let sessionClosed = false, poisoned = false, revision = floor;
  if ((expectedEnvelope?.revision ?? 0) !== floor) {
    await memory.close();
    deny('concurrent_open');
  }
  const assertOpen = () => {
    if (sessionClosed) deny('session_closed');
    if (poisoned) deny('session_poisoned');
    assertOwner();
  };
  return Object.freeze({
    get executor() { assertOpen(); return memory; },
    get revision() { return revision; },
    async commit() {
      assertOpen();
      if (!revisionOk(revision) || revision >= Number.MAX_SAFE_INTEGER) deny('invalid_revision');
      let snapshot;
      try {
        snapshot = memory.exportSnapshot();
        if (!(snapshot instanceof Uint8Array) || snapshot.length === 0) {
          deny('invalid_volatile_snapshot');
        }
        assertOpen();
        const nextRevision = revision + 1;
        // A single-writer CAS in a trusted authority. IDB CAS remains required.
        const advanced = await revisionAuthority.compareAndAdvance({
          vaultId, slot, expectedFloor: revision, nextFloor: nextRevision,
        });
        if (advanced !== true) deny('trusted_revision_conflict');
        // Once advanced, NEVER decrement the floor, even if commit fails.
        poisoned = true;
        assertOwner();
        const nextEnvelope = await store.commit({
          slot, vaultId, expectedEnvelope, minimumRevision: revision,
          bytes: snapshot, key,
        });
        assertOwner();
        if (nextEnvelope?.revision !== nextRevision) deny('invalid_commit_receipt');
        expectedEnvelope = nextEnvelope;
        revision = nextRevision;
        poisoned = false;
        return Object.freeze({ revision: nextRevision });
      } finally {
        if (snapshot instanceof Uint8Array) snapshot.fill(0);
      }
    },
    async close() {
      if (sessionClosed) return;
      sessionClosed = true;
      await memory.close();
      // This session does not own the injected ciphertext store or identity.
    },
  });
}
