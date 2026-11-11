import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {encryptBackup,decryptBackup} from './backup_codec.mjs';
const ownerA='amina_vault_v1_native_734';
const ownerB='amina_vault_v1_native_812';
const secret=webcrypto.getRandomValues(new Uint8Array(32));
const fake='{"marker":"D1_SYNTHETIC_ONLY_731","bloodSugar":117}';
const seal=() => encryptBackup(webcrypto,{owner:ownerA,schema:12,plaintext:fake,recoveryKey:secret});
const open=(envelope,extras={})=>decryptBackup(webcrypto,{
  expectedOwner:ownerA,expectedSchema:12,envelope,recoveryKey:secret,...extras,
});
test('D1 B: authenticated roundtrip, no clear marker, randomized salt and nonce', async()=>{
  const a=await seal(),b=await seal();
  assert.ok(!a.includes('D1_SYNTHETIC_ONLY_731'));
  assert.notEqual(a,b);
  assert.equal(await open(a),fake);
  const ea=JSON.parse(a),eb=JSON.parse(b);
  assert.notEqual(ea.nonce,eb.nonce);
  assert.notEqual(ea.salt,eb.salt);
});
test('D1 B: reject wrong owner before any restore',async()=>{
 const a=await seal();
 await assert.rejects(open(a,{expectedOwner:ownerB}),/MISMATCH/);
 await assert.rejects(open(JSON.stringify({...JSON.parse(a),owner:ownerB})),/MISMATCH/);
});
test('D1 B: reject wrong recovery key, tampered ciphertext and header',async()=>{
 const a=await seal();
 const wrong=webcrypto.getRandomValues(new Uint8Array(32));
 await assert.rejects(open(a,{recoveryKey:wrong}),/AUTHENTICATION_FAILED/);
 const e=JSON.parse(a);
 const corrupt=JSON.stringify({...e,ciphertext:(e.ciphertext[0]==='A'?'B':'A')+e.ciphertext.slice(1)});
 await assert.rejects(open(corrupt),/AUTHENTICATION_FAILED/);
 await assert.rejects(open(JSON.stringify({...e,version:2})),/MISMATCH/);
 await assert.rejects(open(JSON.stringify({...e,schema:11})),/MISMATCH/);
 await assert.rejects(open(JSON.stringify({...e,nonce:e.nonce.slice(0,-4)})),/MALFORMED/);
});
test('D1 B: fail closed on invalid crypto, key, and legacy plain backup',async()=>{
 await assert.rejects(encryptBackup(null,{owner:ownerA,schema:12,plaintext:fake,recoveryKey:secret}),/WEBCRYPTO_REQUIRED/);
 await assert.rejects(encryptBackup(webcrypto,{owner:ownerA,schema:12,plaintext:fake,recoveryKey:new Uint8Array(32)}),/INVALID_RECOVERY_KEY/);
 await assert.rejects(open(fake),/MISMATCH/);
 await assert.rejects(open('not json'),/INVALID_ENVELOPE/);
});
