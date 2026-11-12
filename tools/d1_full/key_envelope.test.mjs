import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {generateDbKey,wrapDbKey,unwrapDbKey} from './key_envelope.mjs';
const a='amina_vault_v1_native_734',b='amina_vault_v1_native_812';
const recovery=generateDbKey(webcrypto);
const dbKey=generateDbKey(webcrypto);
const wrap=()=>wrapDbKey(webcrypto,{owner:a,dbKey,recoveryKey:recovery});
const unwrap=(envelope,extras={})=>unwrapDbKey(webcrypto,{
 expectedOwner:a,envelope,recoveryKey:recovery,...extras});
test('D1 keys: unique cryptographic DB keys, owner A cold recovery',async()=>{
 const d=generateDbKey(webcrypto);assert.equal(d.length,32);
 assert.notDeepEqual(d,dbKey);
 const blob=await wrap();
 assert.equal(blob.includes(Array.from(dbKey).join(',')),false);
 const restored=await unwrap(blob);
 assert.deepEqual(restored,dbKey);
});
test('D1 keys: wrong recovery, owner B or spoofed identity fails',async()=>{
 const blob=await wrap();
 await assert.rejects(unwrap(blob,{expectedOwner:b}),/MISMATCH/);
 await assert.rejects(unwrap(blob,{recoveryKey:generateDbKey(webcrypto)}),/AUTH_FAILED/);
 const obj=JSON.parse(blob);
 await assert.rejects(unwrap(JSON.stringify({...obj,owner:b})),/MISMATCH/);
 await assert.rejects(unwrap(JSON.stringify({...obj,keyId:'AAAAAAAAAAAAAAAAAAAAAA=='})),/AUTH_FAILED/);
});
test('D1 keys: tamper, replay version and corrupt IV denied',async()=>{
 const blob=await wrap(),obj=JSON.parse(blob);
 await assert.rejects(unwrap(JSON.stringify({...obj,version:2})),/MISMATCH/);
 await assert.rejects(unwrap(JSON.stringify({...obj,nonce:'AA=='})),/MALFORMED_LENGTH/);
 const changed={...obj,ciphertext:(obj.ciphertext[0]==='A'?'B':'A')+obj.ciphertext.slice(1)};
 await assert.rejects(unwrap(JSON.stringify(changed)),/AUTH_FAILED/);
});
test('D1 keys: reject deterministic/invalid keys and audit namespace',async()=>{
 const zero=new Uint8Array(32);
 assert.throws(()=>generateDbKey(null),/CRYPTO_UNAVAILABLE/);
 await assert.rejects(wrapDbKey(webcrypto,{owner:a,dbKey:zero,recoveryKey:recovery}),/RANDOM_256_BIT_KEY_REQUIRED/);
 await assert.rejects(wrapDbKey(webcrypto,{owner:'amina_vault_v1_audit',dbKey,recoveryKey:recovery}),/CLINICAL_OWNER_REQUIRED/);
 const d='amina_vault_v1_device_ab23456712344abc8def123456789abc';
 const blob=await wrapDbKey(webcrypto,{owner:d,dbKey,recoveryKey:recovery});
 const opened=await unwrapDbKey(webcrypto,{expectedOwner:d,envelope:blob,recoveryKey:recovery});
 assert.deepEqual(opened,dbKey);
});
