import test from 'node:test';
import assert from 'node:assert/strict';
import {
  VaultEnvelopeError, createRecoverySecret, importRecoverySecret,
  sealVaultSnapshot, openVaultSnapshot, rotateVaultSnapshot,
} from '../../frontend/web/iamina_vault_envelope.mjs';

const a = 'amina_vault_v1_native_734';
const b = 'amina_vault_v1_native_812';
const device = 'amina_vault_v1_device_b32afafd8d9d4ad485137dcfb54299a6';
const fixture = new TextEncoder().encode('SQLite format 3\0SYNTHETIC_PATIENT_A_DATA_X42');
async function setup() {
  const secret = createRecoverySecret();
  const key = await importRecoverySecret(secret);
  return { secret, key };
}
const rejectsCode = (code) => (error) => error instanceof VaultEnvelopeError && error.code === code;

test('recovery secret has 256 bits, non-exportable imported key', async () => {
  const { secret, key } = await setup();
  assert.match(secret, /^[A-Za-z0-9_-]{43}$/);
  assert.equal(key.extractable, false);
  await assert.rejects(crypto.subtle.exportKey('raw', key));
});

test('ciphertext persists without plaintext, owner identifier or recovery key', async () => {
  const { secret, key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  const text = JSON.stringify(envelope);
  assert.ok(!text.includes('SYNTHETIC_PATIENT_A'));
  assert.ok(!text.includes(a));
  assert.ok(!text.includes(secret));
  assert.deepEqual(await openVaultSnapshot({ envelope, vaultId: a, minimumRevision: 1, key }), fixture);
});

test('cold reload: same recovery capability restores snapshot', async () => {
  const { secret, key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 3, key });
  const reopenedKey = await importRecoverySecret(secret);
  assert.deepEqual(await openVaultSnapshot({ envelope: structuredClone(envelope), vaultId: a, minimumRevision: 3, key: reopenedKey }), fixture);
});

test('independent recovery secret cannot decrypt ciphertext', async () => {
  const { key } = await setup();
  const other = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  await assert.rejects(openVaultSnapshot({ envelope, vaultId: a, minimumRevision: 1, key: other.key }), rejectsCode('authentication_failed'));
});

test('A ciphertext cannot open in B vault, even with the same key', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  await assert.rejects(openVaultSnapshot({ envelope, vaultId: b, minimumRevision: 1, key }), rejectsCode('authentication_failed'));
});

test('device-local ciphertext cannot open in native patient scope', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: device, revision: 1, key });
  await assert.rejects(openVaultSnapshot({ envelope, vaultId: a, minimumRevision: 1, key }), rejectsCode('authentication_failed'));
});

test('AAD authenticates revision edits and rejects rollback below trusted floor', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 3, key });
  await assert.rejects(openVaultSnapshot({ envelope: { ...envelope, revision: 4 }, vaultId: a, minimumRevision: 1, key }), rejectsCode('authentication_failed'));
  await assert.rejects(openVaultSnapshot({ envelope, vaultId: a, minimumRevision: 4, key }), rejectsCode('rollback_detected'));
});

test('bit flipped ciphertext fails authentication', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  const last = envelope.ciphertext.slice(-1);
  const wrong = last === 'A' ? 'B' : 'A';
  await assert.rejects(openVaultSnapshot({ envelope: { ...envelope, ciphertext: envelope.ciphertext.slice(0, -1) + wrong }, vaultId: a, minimumRevision: 1, key }), rejectsCode('authentication_failed'));
});

test('nonce alteration fails authentication', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  const wrong = envelope.nonce[0] === 'A' ? 'B' : 'A';
  await assert.rejects(openVaultSnapshot({ envelope: { ...envelope, nonce: wrong + envelope.nonce.slice(1) }, vaultId: a, minimumRevision: 1, key }), rejectsCode('authentication_failed'));
});

test('fresh encryption uses unique random nonce per snapshot', async () => {
  const { key } = await setup();
  const nonces = new Set();
  for (let i = 1; i <= 48; i++) {
    const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: i, key });
    nonces.add(envelope.nonce);
  }
  assert.equal(nonces.size, 48);
});

test('invalid schema and extra fields fail closed', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  for (const corrupt of [{ ...envelope, version: 2 }, { ...envelope, origin: 'other' }, { ...envelope, nonce: '' }, { ...envelope, ciphertext: '$' }, { ...envelope, nonce: 'A' }]) {
    await assert.rejects(openVaultSnapshot({ envelope: corrupt, vaultId: a, minimumRevision: 1, key }));
  }
});

test('invalid vault id or revision never encrypts', async () => {
  const { key } = await setup();
  await assert.rejects(sealVaultSnapshot({ bytes: fixture, vaultId: 'amina', revision: 1, key }), rejectsCode('invalid_vault_scope'));
  await assert.rejects(sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 0, key }), rejectsCode('invalid_revision'));
});

test('rejects empty input and malformed recovery key', async () => {
  const { key } = await setup();
  await assert.rejects(sealVaultSnapshot({ bytes: new Uint8Array(), vaultId: a, revision: 1, key }), rejectsCode('invalid_snapshot'));
  await assert.rejects(importRecoverySecret('password'), rejectsCode('invalid_recovery_secret'));
  await assert.rejects(importRecoverySecret('invalid!'), rejectsCode('invalid_encoding'));
});

test('rotation: old recovery credential denied, replacement decrypts new snapshot', async () => {
  const oldKey = (await setup()).key;
  const newKey = (await setup()).key;
  const oldEnvelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key: oldKey });
  const newEnvelope = await rotateVaultSnapshot({ envelope: oldEnvelope, vaultId: a,
    minimumRevision: 1, nextRevision: 2, oldKey, newKey });
  assert.equal(newEnvelope.revision, 2);
  assert.deepEqual(await openVaultSnapshot({ envelope: newEnvelope, vaultId: a, minimumRevision: 2, key: newKey }), fixture);
  await assert.rejects(openVaultSnapshot({ envelope: newEnvelope, vaultId: a, minimumRevision: 2, key: oldKey }), rejectsCode('authentication_failed'));
  await assert.rejects(rotateVaultSnapshot({ envelope: oldEnvelope, vaultId: a,
    minimumRevision: 1, nextRevision: 1, oldKey, newKey }), rejectsCode('invalid_revision'));
});

test('noncanonical base64 encoding rejected', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  await assert.rejects(openVaultSnapshot({
    envelope: { ...envelope, nonce: envelope.nonce + '=' },
    vaultId: a, minimumRevision: 1, key,
  }), rejectsCode('invalid_encoding'));
});

test('no silent fallback to a different patient on corrupt or unknown scope', async () => {
  const { key } = await setup();
  const envelope = await sealVaultSnapshot({ bytes: fixture, vaultId: a, revision: 1, key });
  for (const vaultId of ['amina_vault_v1_audit', 'amina_vault_v1_native_0', '', 'amina']) {
    await assert.rejects(openVaultSnapshot({ envelope, vaultId, minimumRevision: 1, key }), rejectsCode('invalid_vault_scope'));
  }
});
