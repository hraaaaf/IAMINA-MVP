/**
 * W02 PREVIEW-ONLY: an encrypted-blob persistence primitive, NOT a Drift
 * SQLite connector and NOT an authorization, recovery or antirollback system.
 * All writes are AES-GCM ciphertext; no patient identity is stored in the key.
 * The caller must verify its envelope and hold an independent revision floor.
 */
import { openVaultSnapshot, sealVaultSnapshot } from './iamina_vault_envelope.mjs';

const DATABASE = 'iamina_w02_ciphertext_only_v1';
const STORE = 'sealed_snapshots';
const VERSION = 1;
const SLOT_RE = /^[A-Za-z0-9_-]{43}$/;
const MAX_REVISION = Number.MAX_SAFE_INTEGER;

export class CiphertextStoreError extends Error {
  constructor(code) { super(code); this.code = code; this.name = 'CiphertextStoreError'; }
}
function error(code) { throw new CiphertextStoreError(code); }
function requireSlot(slot) {
  if (typeof slot !== 'string' || !SLOT_RE.test(slot)) error('invalid_slot');
}
function requireRevision(revision) {
  if (!Number.isSafeInteger(revision) || revision < 0 || revision > MAX_REVISION) error('invalid_revision');
}
function compareEnvelope(a, b) {
  if (a === null || b === null) return a === b;
  return a?.format === b?.format && a?.version === b?.version &&
    a?.revision === b?.revision && a?.nonce === b?.nonce &&
    a?.ciphertext === b?.ciphertext &&
    Object.keys(a).length === 5 && Object.keys(b).length === 5;
}
function validatedRecord(value, slot) {
  if (value === undefined) return null;
  if (!value || typeof value !== 'object' || value.slot !== slot ||
      Object.keys(value).sort().join('|') !== 'envelope|slot' ||
      !value.envelope || typeof value.envelope !== 'object') {
    error('invalid_record');
  }
  return value.envelope;
}

/** Generate a random 256-bit opaque ID, never a user id or clinical scope. */
export function createRandomVaultSlot() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  try {
    let text = '';
    for (const b of bytes) text += String.fromCharCode(b);
    return btoa(text).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  } finally { bytes.fill(0); }
}

/**
 * Opens a dedicated DB. Does not open, migrate, delete or read any legacy
 * 'amina' or drift physical databases. Failure never falls back to plaintext.
 */
export function openCiphertextStore({ indexedDb = globalThis.indexedDB } = {}) {
  if (!indexedDb || typeof indexedDb.open !== 'function') {
    return Promise.reject(new CiphertextStoreError('indexeddb_unavailable'));
  }
  return new Promise((resolve, reject) => {
    let request;
    let completed = false;
    const fail = (code) => {
      if (completed) return;
      completed = true;
      reject(new CiphertextStoreError(code));
    };
    try { request = indexedDb.open(DATABASE, VERSION); }
    catch (_) { fail('indexeddb_open_failed'); return; }
    request.onblocked = () => fail('indexeddb_blocked');
    request.onerror = () => fail('indexeddb_open_failed');
    request.onupgradeneeded = () => {
      try {
        if (!request.result.objectStoreNames.contains(STORE)) {
          request.result.createObjectStore(STORE, { keyPath: 'slot' });
        }
      } catch (_) { fail('indexeddb_schema_failed'); }
    };
    request.onsuccess = () => {
      const db = request.result;
      if (completed) { db.close(); return; }
      if (!db.objectStoreNames.contains(STORE)) {
        db.close(); fail('indexeddb_schema_failed'); return;
      }
      db.onversionchange = () => db.close();
      completed = true;
      resolve(new CiphertextVaultStore(db));
    };
  });
}

export class CiphertextVaultStore {
  #db;
  #closed = false;
  constructor(db) { this.#db = db; }
  close() { if (!this.#closed) { this.#closed = true; this.#db.close(); } }
  #transaction(mode) {
    if (this.#closed) error('store_closed');
    try {
      // IDB transactions serialize competing writers to the same object store.
      // The strict durability hint avoids silently accepting relaxed/default
      // persistence for irreplaceable patient snapshots on supported browsers.
      const tx = mode === 'readwrite'
        ? this.#db.transaction(STORE, mode, { durability: 'strict' })
        : this.#db.transaction(STORE, mode);
      if (mode === 'readwrite' && tx.durability !== 'strict') {
        try { tx.abort(); } catch (_) { /* never continue */ }
        error('strict_durability_unavailable');
      }
      return tx;
    } catch (reason) {
      if (reason instanceof CiphertextStoreError) throw reason;
      error('indexeddb_transaction_failed');
    }
  }

  /** Returns an opaque authenticated envelope, NOT decrypted SQLite bytes. */
  async readEnvelope(slot) {
    requireSlot(slot);
    const tx = this.#transaction('readonly');
    return new Promise((resolve, reject) => {
      let outcome, rejection;
      tx.oncomplete = () => rejection ? reject(rejection) : resolve(outcome);
      tx.onabort = tx.onerror = () => reject(rejection || new CiphertextStoreError('indexeddb_read_failed'));
      try {
        const request = tx.objectStore(STORE).get(slot);
        request.onsuccess = () => {
          try {
            outcome = validatedRecord(request.result, slot);
          } catch (err) {
            rejection = err;
            tx.abort();
          }
        };
        request.onerror = () => { rejection = new CiphertextStoreError('indexeddb_read_failed'); };
      } catch (_) { rejection = new CiphertextStoreError('indexeddb_read_failed'); tx.abort(); }
    });
  }

  /** Authenticate/restore with an external, independently trusted floor. */
  async restore({ slot, vaultId, minimumRevision, key }) {
    const envelope = await this.readEnvelope(slot);
    if (envelope === null) {
      if (!Number.isSafeInteger(minimumRevision) || minimumRevision < 0) error('invalid_revision');
      if (minimumRevision > 0) error('missing_known_snapshot');
      return null;
    }
    return {
      envelope,
      bytes: await openVaultSnapshot({ envelope, vaultId, minimumRevision, key }),
    };
  }

  /**
   * CAS commit. AES-GCM encryption runs BEFORE opening the IDB transaction;
   * every get+put is in the SAME readwrite transaction, without awaits.
   * This routine independently authenticates expectedEnvelope with the same
   * key AND patient scope before opening IDB; it never trusts a caller-asserted
   * earlier read. minimumRevision MUST be an external, independently trusted
   * floor, not a revision obtained from this same mutable IndexedDB database.
   * If null, a new empty slot is required. Never silently overwrite.
   */
  async commit({ slot, vaultId, expectedEnvelope, minimumRevision, bytes, key }) {
    requireSlot(slot);
    requireRevision(minimumRevision);
    if (expectedEnvelope !== null && (!expectedEnvelope || typeof expectedEnvelope !== 'object')) error('invalid_expected_envelope');
    const expectedRevision = expectedEnvelope?.revision ?? 0;
    requireRevision(expectedRevision);
    if (expectedRevision < minimumRevision) error('rollback_detected');
    // Never use a caller-supplied prior envelope as an authorization to mutate
    // unless it authenticates under the same key/scope. This check runs before
    // any persistent transaction; the CAS then verifies it is still current.
    if (expectedEnvelope !== null) {
      const verified = await openVaultSnapshot({
        envelope: expectedEnvelope, vaultId,
        minimumRevision: Math.max(1, minimumRevision), key,
      });
      verified.fill(0);
    }
    if (expectedRevision === MAX_REVISION) error('invalid_revision');
    const revision = expectedRevision + 1;
    const nextEnvelope = await sealVaultSnapshot({ bytes, vaultId, revision, key });
    const tx = this.#transaction('readwrite');
    return new Promise((resolve, reject) => {
      let rejection;
      tx.oncomplete = () => rejection ? reject(rejection) : resolve(nextEnvelope);
      tx.onabort = tx.onerror = () => reject(rejection || new CiphertextStoreError('indexeddb_commit_failed'));
      try {
        const store = tx.objectStore(STORE);
        const read = store.get(slot);
        read.onerror = () => { rejection = new CiphertextStoreError('indexeddb_commit_failed'); };
        read.onsuccess = () => {
          try {
            const actual = validatedRecord(read.result, slot);
            if (!compareEnvelope(actual, expectedEnvelope)) {
              rejection = new CiphertextStoreError('concurrent_update');
              tx.abort();
              return;
            }
            const write = store.put({ slot, envelope: nextEnvelope });
            write.onerror = () => { rejection = new CiphertextStoreError('indexeddb_commit_failed'); };
          } catch (err) { rejection = err; tx.abort(); }
        };
      } catch (_) { rejection = new CiphertextStoreError('indexeddb_commit_failed'); tx.abort(); }
    });
  }
}
