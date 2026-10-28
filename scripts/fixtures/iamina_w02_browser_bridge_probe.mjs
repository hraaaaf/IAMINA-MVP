/**
 * W02 browser E2E TEST FIXTURE only. It never loads in the Flutter application.
 * Restricted to explicit synthetic principal IDs; lacks genuine owner proof and
 * an independently durable revision floor. NEVER use with clinical records.
 *
 * Real IndexedDB AES-256-GCM CAS is exercised across the Dart JS-interop boundary.
 * Dart passes actual Drift/SQLite WASM bytes as Uint8Array (never JSON plaintext).
 */
import { createRecoverySecret, importRecoverySecret } from './iamina_vault_envelope.mjs';
import { createRandomVaultSlot, openCiphertextStore } from './iamina_vault_ciphertext_store.mjs';

const TEST_SCOPES = new Set(['amina_vault_v1_native_734', 'amina_vault_v1_native_812']);
export function createSyntheticSecret() { return createRecoverySecret(); }
export function createSyntheticSlot() { return createRandomVaultSlot(); }

export async function openSyntheticBrowserBridge(vaultId, slot, secret, minimumRevision, allowEmpty) {
  if (!TEST_SCOPES.has(vaultId)) throw Error('w02_synthetic_scope_only');
  if (!Number.isSafeInteger(minimumRevision) || minimumRevision < 0 ||
      typeof allowEmpty !== 'boolean') throw Error('w02_invalid_revision_or_creation');
  const key = await importRecoverySecret(secret);
  const store = await openCiphertextStore();
  let restored;
  let originalEnvelope;
  try {
    restored = await store.restore({
      slot, vaultId, minimumRevision: Math.max(1, minimumRevision), key,
    });
    if (restored === null) {
      if (minimumRevision !== 0) throw Error('w02_missing_known_snapshot');
      if (!allowEmpty) throw Error('w02_synthetic_creation_denied');
    } else if (minimumRevision === 0 || restored.envelope.revision !== minimumRevision) {
      restored.bytes.fill(0);
      throw Error('w02_untrusted_revision_floor');
    }
    originalEnvelope = await store.readEnvelope(slot);
    // No revised/tampered ciphertext is accepted between authenticated restore
    // and acquiring a CAS token for a volatile SQLite executor.
    const a = restored?.envelope ?? null;
    const b = originalEnvelope;
    if (JSON.stringify(a) !== JSON.stringify(b)) throw Error('w02_concurrent_open');
  } catch (cause) {
    restored?.bytes?.fill(0);
    store.close();
    throw cause;
  }

  let closed = false;
  let expectedEnvelope = originalEnvelope;
  let revision = minimumRevision;
  let snapshot = restored?.bytes ?? null;
  return Object.freeze({
    get snapshot() {
      if (closed) throw Error('w02_browser_bridge_closed');
      return snapshot;
    },
    get revision() { return revision; },
    async commit(inputBytes) {
      if (closed) throw Error('w02_browser_bridge_closed');
      if (!(inputBytes instanceof Uint8Array) || inputBytes.length === 0) {
        throw Error('w02_invalid_snapshot');
      }
      // This is synthetic. Caller-provided floor is NOT a trusted patient floor.
      const next = await store.commit({
        slot, vaultId, expectedEnvelope, minimumRevision: revision,
        bytes: inputBytes, key,
      });
      if (next.revision !== revision + 1) throw Error('w02_invalid_commit_receipt');
      expectedEnvelope = next;
      revision = next.revision;
      return revision;
    },
    close() {
      if (closed) return;
      closed = true;
      snapshot?.fill(0);
      snapshot = null;
      store.close();
    },
  });
}
