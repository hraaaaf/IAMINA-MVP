/**
 * W02 OPTION A contract proof — synthetic only, not imported by patient routes.
 * The Django/PG API (through existing same-origin BFF) is the sole monotone
 * revision authority. Browser storage never establishes its own revision floor.
 *
 * A pending server reservation means no ordinary restore/commit. Never auto
 * reset or abort it: after a crash, explicit authenticated recovery is needed.
 * This module does not certify crash recovery, XSS resistance or clinical use.
 */
const deny = code => { throw Object.assign(new Error(code), { code }); };
const encode = new TextEncoder();
const slotRe = /^[A-Za-z0-9_-]{43}$/;
const hashRe = /^[0-9a-f]{64}$/;
const states = new Set(['uninitialized', 'ready', 'pending']);
function requireOwner(ownerSession, vaultId, slot) {
  if (!ownerSession || ownerSession.assertCurrent?.({ vaultId, slot }) !== true) {
    deny('owner_session_changed');
  }
}
function parseState(state, slot, vaultId) {
  if (!state || !states.has(state.status)) deny('invalid_anchor_state');
  if (state.vault_id !== vaultId) deny('verified_owner_scope_mismatch');
  if (state.status === 'uninitialized') {
    if (state.slot !== null || state.committed_revision !== 0 ||
        state.committed_envelope_sha256 !== '' ||
        state.pending_revision !== null || state.pending_ticket !== null) {
      deny('invalid_anchor_state');
    }
    return;
  }
  if (state.slot !== slot || !Number.isSafeInteger(state.committed_revision) ||
      state.committed_revision < 0 ||
      (state.committed_revision === 0
        ? state.committed_envelope_sha256 !== ''
        : !hashRe.test(state.committed_envelope_sha256)) ||
      (state.status === 'ready' && state.committed_revision === 0)) {
    deny('invalid_anchor_state');
  }
  if (state.status === 'pending' &&
      (!Number.isSafeInteger(state.pending_revision) ||
       state.pending_revision !== state.committed_revision + 1 ||
       !slotRe.test(state.pending_ticket))) deny('invalid_anchor_state');
  if (state.status === 'ready' &&
      (state.pending_revision !== null || state.pending_ticket !== null)) deny('invalid_anchor_state');
}
function canonicalEnvelope(envelope) {
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope) ||
      Object.keys(envelope).sort().join('|') !== 'ciphertext|format|nonce|revision|version' ||
      !Number.isSafeInteger(envelope.revision) || envelope.revision < 1 ||
      typeof envelope.format !== 'string' || typeof envelope.version !== 'number' ||
      typeof envelope.nonce !== 'string' || typeof envelope.ciphertext !== 'string') {
    deny('invalid_envelope');
  }
  return [envelope.format, envelope.version, envelope.revision, envelope.nonce, envelope.ciphertext];
}
export async function envelopeSha256(envelope) {
  const digest = new Uint8Array(await crypto.subtle.digest(
    'SHA-256', encode.encode(JSON.stringify(canonicalEnvelope(envelope))),
  ));
  return [...digest].map(x => x.toString(16).padStart(2, '0')).join('');
}

/**
 * Same-origin native bearer adapter; never sends cookies/secret to third-party.
 * Called only from an explicit isolated experiment, not the patient runtime.
 */
export function makePreviewRevisionApi({ token, fetchImpl = fetch, origin = globalThis.location?.origin }) {
  if (typeof token !== 'string' || !/^iamina\.[A-Za-z0-9_.:-]+$/.test(token) ||
      typeof origin !== 'string' || !origin.startsWith('https://') ||
      (globalThis.location && globalThis.location.origin !== origin)) {
    deny('invalid_native_preview_context');
  }
  const base = new URL('/api/v1/w02/vault-revision/', origin);
  const request = async (action, method, data) => {
    const uri = new URL(action, base);
    const response = await fetchImpl(uri, {
      method, credentials: 'omit', redirect: 'error', cache: 'no-store',
      headers: {
        Authorization: 'Bearer ' + token,
        Accept: 'application/json',
        ...(data === undefined ? {} : {'Content-Type': 'application/json'}),
      },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    if (!response.ok) deny('revision_authority_unavailable');
    return response.json();
  };
  return Object.freeze({
    state: () => request('state', 'GET'),
    reserve: data => request('reserve', 'POST', data),
    finalize: data => request('finalize', 'POST', data),
  });
}

/** Open only when PG says no reservation is pending and floor is committed. */
export async function openOptionASyntheticSession({
  api, store, vaultId, slot, key, ownerSession, allowSyntheticEmpty = false,
}) {
  if (!slotRe.test(slot) || typeof vaultId !== 'string' ||
      !api || !store || !key) deny('missing_anchor_dependency');
  requireOwner(ownerSession, vaultId, slot);
  const state = await api.state();
  requireOwner(ownerSession, vaultId, slot);
  parseState(state, slot, vaultId);
  if (state.status === 'pending') deny('pending_recovery_required');
  if (state.status === 'uninitialized' && allowSyntheticEmpty !== true) {
    deny('enrollment_not_authorized');
  }
  const previous = await store.readEnvelope(slot);
  let snapshot = null;
  try {
    if (state.status === 'uninitialized') {
      if (previous !== null) deny('unanchored_browser_ciphertext');
    } else {
      if (state.committed_revision < 1 || previous === null ||
          previous.revision !== state.committed_revision ||
          await envelopeSha256(previous) !== state.committed_envelope_sha256) {
        deny('rollback_or_ciphertext_mismatch');
      }
      const restored = await store.restore({
        slot, vaultId, minimumRevision: state.committed_revision, key,
      });
      if (!restored || !(restored.bytes instanceof Uint8Array)) {
        deny('invalid_restored_snapshot');
      }
      // Take ownership of the plaintext BEFORE any further async work.
      // Even a digest-parse error or logout during restore must scrub bytes.
      snapshot = restored.bytes;
      if (await envelopeSha256(restored.envelope) !== state.committed_envelope_sha256) {
        deny('concurrent_restore');
      }
    }
    requireOwner(ownerSession, vaultId, slot);
  } catch (error) {
    snapshot?.fill(0);
    throw error;
  }
  let revision = state.committed_revision;
  let expectedEnvelope = previous;
  let closed = false, poisoned = false, busy = false;
  return Object.freeze({
    get revision() { return revision; },
    takeSnapshot() {
      if (closed || poisoned) deny('session_not_available');
      requireOwner(ownerSession, vaultId, slot);
      return snapshot === null ? null : Uint8Array.from(snapshot);
    },
    async commit(bytes) {
      if (closed || poisoned || busy) deny('session_not_available');
      requireOwner(ownerSession, vaultId, slot);
      if (!(bytes instanceof Uint8Array) || bytes.length === 0) deny('invalid_snapshot');
      // Prevent caller mutating input across asynchronous network operations.
      const copy = Uint8Array.from(bytes);
      busy = true;
      try {
        const reservation = await api.reserve({ slot, expected_revision: revision });
        poisoned = true; // Ever after reserve: failures require recovery.
        if (!reservation || reservation.vault_id !== vaultId ||
            reservation.revision !== revision + 1 ||
            !slotRe.test(reservation.ticket)) deny('invalid_reservation_receipt');
        if (closed) deny('session_closed');
        requireOwner(ownerSession, vaultId, slot);
        const envelope = await store.commit({
          slot, vaultId, expectedEnvelope, minimumRevision: revision,
          bytes: copy, key,
        });
        if (envelope.revision !== reservation.revision) deny('invalid_ciphertext_receipt');
        const digest = await envelopeSha256(envelope);
        if (closed) deny('session_closed');
        requireOwner(ownerSession, vaultId, slot);
        const final = await api.finalize({
          slot, revision: reservation.revision,
          ticket: reservation.ticket, envelope_sha256: digest,
        });
        if (final?.vault_id !== vaultId ||
            final?.status !== 'ready' ||
            final.committed_revision !== reservation.revision ||
            final.committed_envelope_sha256 !== digest) {
          deny('invalid_finalization_receipt');
        }
        expectedEnvelope = envelope;
        revision = final.committed_revision;
        snapshot?.fill(0);
        snapshot = Uint8Array.from(copy);
        poisoned = false;
        return Object.freeze({ revision, envelope_sha256: digest });
      } finally {
        copy.fill(0);
        busy = false;
      }
    },
    close() {
      if (closed) return;
      closed = true;
      snapshot?.fill(0);
      snapshot = null;
    },
  });
}

/**
 * Explicit recovery after browser crash: requires exact pending revision,
 * local authenticated AES-GCM ciphertext and verified principal.
 * If the local new ciphertext is missing, NEVER clear the server reservation.
 */
export async function finalizePendingSynthetic({
  api, store, vaultId, slot, key, ownerSession,
}) {
  requireOwner(ownerSession, vaultId, slot);
  const state = await api.state();
  requireOwner(ownerSession, vaultId, slot);
  parseState(state, slot, vaultId);
  if (state.status !== 'pending') deny('no_pending_recovery');
  const record = await store.readEnvelope(slot);
  if (!record || record.revision !== state.pending_revision) {
    deny('pending_ciphertext_missing');
  }
  const restored = await store.restore({
    slot, vaultId, minimumRevision: state.pending_revision, key,
  });
  if (!restored || await envelopeSha256(restored.envelope) !== await envelopeSha256(record)) {
    restored?.bytes?.fill(0);
    deny('pending_ciphertext_changed');
  }
  restored.bytes.fill(0);
  requireOwner(ownerSession, vaultId, slot);
  const digest = await envelopeSha256(record);
  const final = await api.finalize({
    slot, revision: state.pending_revision,
    ticket: state.pending_ticket, envelope_sha256: digest,
  });
  if (final?.vault_id !== vaultId ||
      final?.status !== 'ready' || final.committed_revision !== state.pending_revision ||
      final.committed_envelope_sha256 !== digest) deny('invalid_finalization_receipt');
  return Object.freeze({ revision: state.pending_revision, envelope_sha256: digest });
}
