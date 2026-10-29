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
const sameEnvelope = (a, b) => {
  if (a === null || b === null) return a === b;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object' ||
      Array.isArray(a) || Array.isArray(b)) return false;
  const schema = 'ciphertext|format|nonce|revision|version';
  if (Object.keys(a).sort().join('|') !== schema ||
      Object.keys(b).sort().join('|') !== schema) return false;
  return a.format === b.format && a.version === b.version &&
    a.revision === b.revision && a.nonce === b.nonce &&
    a.ciphertext === b.ciphertext;
};


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
  const authenticatedEnvelope = restored?.envelope ?? null;
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

  // Authentication and volatile SQLite loading are NOT in the same IDB
  // transaction. Compare the WHOLE authenticated envelope after memory.open:
  // equal revision alone permits a same-revision ciphertext swap.
  let expectedEnvelope;
  try {
    expectedEnvelope = await store.readEnvelope(slot);
    assertOwner();
    if (!sameEnvelope(expectedEnvelope, authenticatedEnvelope)) deny('concurrent_open');
    // A writer may reserve the next trusted floor before its IDB transaction
    // becomes visible. Do not hand out an already-revoked in-memory revision.
    const latestFloor = await revisionAuthority.getFloor({ vaultId, slot });
    assertOwner();
    if (!revisionOk(latestFloor) || latestFloor !== floor) {
      deny('trusted_revision_changed_during_open');
    }
  } catch (err) {
    await memory.close();
    throw err;
  }
  let sessionClosed = false, poisoned = false, revision = floor;
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
        // sign-out/close during the trusted reservation must stop the write.
        if (sessionClosed) deny('session_closed');
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
