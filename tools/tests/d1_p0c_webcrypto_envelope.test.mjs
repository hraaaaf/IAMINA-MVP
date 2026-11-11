import test from 'node:test';
import assert from 'node:assert/strict';
import {
  encryptSyntheticPayload, decryptSyntheticPayload,
} from '../d1_p0c_webcrypto_envelope.mjs';

const ownerA = 'amina_vault_v1_native_12';
const ownerB = 'amina_vault_v1_native_34';
const secret = 'SYNTHETIC-only-recovery-secret-43';
const data = 'SYNTHETIC_D1_NO_PATIENT_DATA_TEST_CASE_42';

test('D1-P0C: authenticated envelope roundtrip and zero plaintext leakage', async () => {
  const envelope = await encryptSyntheticPayload({
    ownerScope:ownerA,plaintext:data,passphrase:secret,
  });
  assert.equal(envelope.format, 'iamina-d1-synthetic-envelope-v1');
  assert.equal(JSON.stringify(envelope).includes(data),false);
  const decoded = await decryptSyntheticPayload({
    envelope,expectedOwner:ownerA,passphrase:secret,
  });
  assert.equal(decoded,data);
});

test('D1-P0C: owner B cannot decrypt an A envelope', async () => {
  const envelope = await encryptSyntheticPayload({
    ownerScope:ownerA,plaintext:data,passphrase:secret,
  });
  await assert.rejects(decryptSyntheticPayload({
    envelope,expectedOwner:ownerB,passphrase:secret,
  }), /foreign vault envelope/);
  await assert.rejects(decryptSyntheticPayload({
    envelope:{...envelope,ownerScope:ownerB},
    expectedOwner:ownerB,passphrase:secret,
  }));
});

test('D1-P0C: wrong passphrase and ciphertext tampering fail closed', async () => {
  const envelope = await encryptSyntheticPayload({
    ownerScope:ownerA,plaintext:data,passphrase:secret,
  });
  await assert.rejects(decryptSyntheticPayload({
    envelope,expectedOwner:ownerA,passphrase:secret+'incorrect',
  }));
  const first = envelope.ciphertext[0] === 'A' ? 'B' : 'A';
  await assert.rejects(decryptSyntheticPayload({
    envelope:{...envelope,ciphertext:first+envelope.ciphertext.slice(1)},
    expectedOwner:ownerA,passphrase:secret,
  }));
});

test('D1-P0C: fresh random salt and AES-GCM nonce every attempt', async () => {
  const args={ownerScope:ownerA,plaintext:data,passphrase:secret};
  const a=await encryptSyntheticPayload(args);
  const b=await encryptSyntheticPayload(args);
  assert.notEqual(a.salt,b.salt);
  assert.notEqual(a.iv,b.iv);
  assert.notEqual(a.ciphertext,b.ciphertext);
});

test('D1-P0C: insecure secret and extra untrusted fields are refused', async () => {
  await assert.rejects(encryptSyntheticPayload({
    ownerScope:ownerA,plaintext:data,passphrase:'weak',
  }), /strong recovery secret/);
  const envelope=await encryptSyntheticPayload({
    ownerScope:ownerA,plaintext:data,passphrase:secret,
  });
  await assert.rejects(decryptSyntheticPayload({
    envelope:{...envelope,plaintext:data},
    expectedOwner:ownerA,passphrase:secret,
  }), /untrusted/);
});
