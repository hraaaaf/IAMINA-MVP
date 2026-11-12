// D1 experimental owner-bound DB key envelope: NOT connected to patient runtime.
// RecoveryKey MUST be random 32-byte secret secured outside this application.
// WebCrypto HKDF derives wrapping subkey; AES-GCM authenticates envelope metadata.
// Does NOT implement key persistence, human password KDF, escrow or anti-rollback.
const enc = new TextEncoder();
const fmt = 'IAMINA_D1_DB_KEY_ENVELOPE';
const v = 1;
function check(crypto, owner, bytes) {
  if(!crypto?.subtle || !crypto?.getRandomValues)throw Error('CRYPTO_UNAVAILABLE');
  if(typeof owner!=='string'||!/^amina_vault_v1_(native_[1-9]\d*|device_[a-f0-9]{32})$/.test(owner))
    throw Error('CLINICAL_OWNER_REQUIRED');
  if(!(bytes instanceof Uint8Array)||bytes.length!==32||bytes.every(x=>x===0))
    throw Error('RANDOM_256_BIT_KEY_REQUIRED');
}
const b64 = a => {let s='';for(const b of a)s+=String.fromCharCode(b);return btoa(s);};
const raw = (s,length) => {
 if(typeof s!=='string'||!/^([A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
  throw Error('MALFORMED_ENVELOPE');
 const v=Uint8Array.from(atob(s),c=>c.charCodeAt(0));
 if(length!==undefined&&v.length!==length)throw Error('MALFORMED_LENGTH');
 return v;
};
const aad=(owner,keyId)=>enc.encode(JSON.stringify([fmt,v,owner,keyId,'AES-256-GCM','HKDF-SHA-256']));
async function kek(crypto,recoveryKey,owner,salt) {
 const base=await crypto.subtle.importKey('raw',recoveryKey,{name:'HKDF'},false,['deriveKey']);
 return crypto.subtle.deriveKey({
   name:'HKDF',hash:'SHA-256',salt,info:enc.encode('IAMINA|D1|DB_KEK|v1|'+owner),
 },base,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
export function generateDbKey(crypto) {
 if(!crypto?.subtle||!crypto?.getRandomValues)throw Error('CRYPTO_UNAVAILABLE');
 return crypto.getRandomValues(new Uint8Array(32));
}
export async function wrapDbKey(crypto,{owner,dbKey,recoveryKey}){
 check(crypto,owner,dbKey);check(crypto,owner,recoveryKey);
 const salt=crypto.getRandomValues(new Uint8Array(16));
 const nonce=crypto.getRandomValues(new Uint8Array(12));
 const keyId=b64(crypto.getRandomValues(new Uint8Array(16)));
 const key=await kek(crypto,recoveryKey,owner,salt);
 const ciphertext=new Uint8Array(await crypto.subtle.encrypt({
  name:'AES-GCM',iv:nonce,additionalData:aad(owner,keyId),tagLength:128,
 },key,dbKey));
 return JSON.stringify({format:fmt,version:v,owner,keyId,
  salt:b64(salt),nonce:b64(nonce),ciphertext:b64(ciphertext)});
}
export async function unwrapDbKey(crypto,{expectedOwner,envelope,recoveryKey}){
 check(crypto,expectedOwner,recoveryKey);
 let obj;try{obj=JSON.parse(envelope)}catch{throw Error('MALFORMED_ENVELOPE')}
 if(!obj||Array.isArray(obj)||obj.format!==fmt||obj.version!==v||
    obj.owner!==expectedOwner)throw Error('OWNER_OR_VERSION_MISMATCH');
 const salt=raw(obj.salt,16),nonce=raw(obj.nonce,12),
       keyId=raw(obj.keyId,16),ciphertext=raw(obj.ciphertext,48);
 const wrap=await kek(crypto,recoveryKey,expectedOwner,salt);
 try{
  const clear=await crypto.subtle.decrypt({
    name:'AES-GCM',iv:nonce,additionalData:aad(expectedOwner,b64(keyId)),tagLength:128,
  },wrap,ciphertext);
  const dbKey=new Uint8Array(clear);
  check(crypto,expectedOwner,dbKey);
  return dbKey;
 }catch{throw Error('KEY_ENVELOPE_AUTH_FAILED')}
}
