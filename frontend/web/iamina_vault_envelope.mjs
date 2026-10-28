/**
 * W02 browser-only cryptographic envelope for an already-serialized SQLite file.
 * NOT a SQLite executor, key custodian, atomic store or clinical activation gate.
 * Never persist raw SQLite bytes, recovery secrets, or imported keys with this API.
 */

const FORMAT = 'iamina-w02-encrypted-sqlite-snapshot';
const VERSION = 1;
const NONCE_BYTES = 12;
const KEY_BYTES = 32;
const TAG_BYTES = 16;
const MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024;
const encoder = new TextEncoder();

export class VaultEnvelopeError extends Error {
  constructor(code) {
    super(code);
    this.name = 'VaultEnvelopeError';
    this.code = code;
  }
}

function fail(code) { throw new VaultEnvelopeError(code); }
function bytesToBase64Url(bytes) {
  const parts = [];
  for (let i = 0; i < bytes.length; i += 0x4000) {
    parts.push(String.fromCharCode(...bytes.subarray(i, i + 0x4000)));
  }
  return btoa(parts.join('')).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
function base64UrlToBytes(value, maxBytes) {
  if (typeof value !== 'string' || value.length === 0 ||
      value.length > Math.ceil(maxBytes / 3) * 4 + 4 ||
      !/^[A-Za-z0-9_-]+$/.test(value)) fail('invalid_encoding');
  let decoded;
  try {
    const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
    decoded = atob(normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '='));
  } catch (_) { fail('invalid_encoding'); }
  if (decoded.length > maxBytes) fail('invalid_encoding');
  const bytes = Uint8Array.from(decoded, (character) => character.charCodeAt(0));
  if (bytesToBase64Url(bytes) !== value) fail('invalid_encoding');
  return bytes;
}
function requireScope(vaultId) {
  if (typeof vaultId !== 'string' || vaultId.length < 4 || vaultId.length > 160 ||
      !/^amina_vault_v1_(?:native_[1-9]\d*|device_[0-9a-f]{32})$/.test(vaultId)) {
    fail('invalid_vault_scope');
  }
}
function requireRevision(revision) {
  if (!Number.isSafeInteger(revision) || revision < 1) fail('invalid_revision');
}
function requireKey(key) {
  if (!key || key.type !== 'secret' || key.extractable !== false ||
      key.algorithm?.name !== 'AES-GCM' || key.algorithm?.length !== 256 ||
      !key.usages?.includes('encrypt') || !key.usages?.includes('decrypt')) {
    fail('invalid_key');
  }
}
function associatedData(vaultId, revision) {
  // Version, vault namespace and monotonic revision are authenticated but not
  // serialized in the envelope, so switching account namespaces cannot decrypt.
  return encoder.encode(JSON.stringify([FORMAT, VERSION, vaultId, revision]));
}

/** Creates a 256-bit recovery capability for the user to keep OUTSIDE browser storage. */
export function createRecoverySecret() {
  const secret = new Uint8Array(KEY_BYTES);
  crypto.getRandomValues(secret);
  try { return bytesToBase64Url(secret); }
  finally { secret.fill(0); }
}

/** Import a previously generated high-entropy recovery capability as a NON-exportable key. */
export async function importRecoverySecret(recoverySecret) {
  const raw = base64UrlToBytes(recoverySecret, KEY_BYTES);
  if (raw.length !== KEY_BYTES) fail('invalid_recovery_secret');
  try {
    return await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt', 'decrypt']);
  } finally { raw.fill(0); }
}

/** Encrypt SQLite snapshot bytes. Returns ONLY an authenticated ciphertext envelope. */
export async function sealVaultSnapshot({ bytes, vaultId, revision, key }) {
  requireScope(vaultId);
  requireRevision(revision);
  requireKey(key);
  if (!(bytes instanceof Uint8Array) || bytes.length === 0 ||
      bytes.length > MAX_SNAPSHOT_BYTES) fail('invalid_snapshot');
  const nonce = new Uint8Array(NONCE_BYTES);
  crypto.getRandomValues(nonce);
  const ciphertext = new Uint8Array(await crypto.subtle.encrypt({
    name: 'AES-GCM', iv: nonce, tagLength: 128,
    additionalData: associatedData(vaultId, revision),
  }, key, bytes));
  return Object.freeze({
    format: FORMAT,
    version: VERSION,
    revision,
    nonce: bytesToBase64Url(nonce),
    ciphertext: bytesToBase64Url(ciphertext),
  });
}

/**
 * Decrypt after verifying schema and AAD; caller must provide an INDEPENDENT
 * trusted revision floor to detect rollback. Without it, rollback is NOT solved.
 * Returned bytes are transient plaintext; caller must not write them unencrypted.
 */
export async function openVaultSnapshot({ envelope, vaultId, minimumRevision, key }) {
  requireScope(vaultId);
  requireKey(key);
  requireRevision(minimumRevision);
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope) ||
      Object.keys(envelope).sort().join('|') !==
      'ciphertext|format|nonce|revision|version' ||
      envelope.format !== FORMAT || envelope.version !== VERSION) fail('invalid_envelope');
  requireRevision(envelope.revision);
  if (envelope.revision < minimumRevision) fail('rollback_detected');
  const nonce = base64UrlToBytes(envelope.nonce, NONCE_BYTES);
  const ciphertext = base64UrlToBytes(envelope.ciphertext, MAX_SNAPSHOT_BYTES + TAG_BYTES);
  if (nonce.length !== NONCE_BYTES || ciphertext.length <= TAG_BYTES) fail('invalid_envelope');
  try {
    const plaintext = new Uint8Array(await crypto.subtle.decrypt({
      name: 'AES-GCM', iv: nonce, tagLength: 128,
      additionalData: associatedData(vaultId, envelope.revision),
    }, key, ciphertext));
    if (plaintext.length === 0 || plaintext.length > MAX_SNAPSHOT_BYTES) {
      plaintext.fill(0);
      fail('invalid_snapshot');
    }
    return plaintext;
  } catch (error) {
    if (error instanceof VaultEnvelopeError) throw error;
    fail('authentication_failed');
  }
}

/** Re-encrypt a verified snapshot under a different recovery capability. */
export async function rotateVaultSnapshot({
  envelope, vaultId, minimumRevision, nextRevision, oldKey, newKey,
}) {
  requireRevision(nextRevision);
  if (!envelope || !Number.isSafeInteger(envelope.revision) ||
      nextRevision <= envelope.revision) fail('invalid_revision');
  const plaintext = await openVaultSnapshot({
    envelope, vaultId, minimumRevision, key: oldKey,
  });
  try {
    return await sealVaultSnapshot({
      bytes: plaintext, vaultId, revision: nextRevision, key: newKey,
    });
  } finally {
    plaintext.fill(0);
  }
}
