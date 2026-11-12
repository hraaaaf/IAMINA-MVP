'use strict';
// Synthetic runner-only P256 private key; generated anew on every CI run.
const {webcrypto}=require('node:crypto');
const fs=require('node:fs');
(async()=>{
  const key=await webcrypto.subtle.generateKey({
    name:'ECDSA',namedCurve:'P-256'
  },true,['sign','verify']);
  const jwk=await webcrypto.subtle.exportKey('jwk',key.privateKey);
  const result={
    key:jwk,
    credential_id:Buffer.from('d1-live-http-synthetic-cred-A').toString('base64url'),
    origin:'https://iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app'
  };
  fs.writeFileSync(process.env.D1_KEYS_JSON,JSON.stringify(result),{mode:0o600,flag:'wx'});
  process.stdout.write('D1 synthetic signing key created (private material not printed).\n');
})().catch(e=>{process.stderr.write(String(e.message));process.exitCode=1});
