/* IAMINA D1 research-only WebAuthn PRF vault-wrap candidate.
 * No patient app integration or patient data. Passkey PRF is not a server
 * account login; no signed assertion server-verification is implemented.
 * Browser support alone is never considered evidence of usable PRF.
 * NO FALLBACK to IndexedDB device KEK or password/passcode.
 */
(function(global){
'use strict';
const FORMAT='IAMINA_D1_WEBAUTHN_PRF_ENVELOPE';
const VERSION=1,STORE='vaultPrf',DBNAME='iamina_d1_prf_research_v1';
const OWNER=/^amina_vault_v1_(?:native_[1-9]\d*|device_[a-f0-9]{32})$/;
const enc=new TextEncoder();
const random=n=>crypto.getRandomValues(new Uint8Array(n));
const b64=bytes=>{
 let s='';for(const x of bytes)s+=String.fromCharCode(x);return btoa(s);
};
const raw=(s,len)=>{
 if(typeof s!=='string'||!/^([A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
  throw Error('D1_PRF_INVALID_B64');
 const a=Uint8Array.from(atob(s),c=>c.charCodeAt(0));
 if(len!==undefined&&a.length!==len)throw Error('D1_PRF_INVALID_LENGTH');
 return a;
};
// WebAuthn clientDataJSON encodes the challenge in base64url, not base64.
const rawUrl=s=>{
 if(typeof s!=='string'||!/^[A-Za-z0-9_-]+$/.test(s))
  throw Error('D1_PRF_BAD_URL_CHALLENGE');
 const padded=s.replace(/-/g,'+').replace(/_/g,'/');
 return raw(padded+'='.repeat((4-padded.length%4)%4));
};
const equal=(a,b)=>{
 if(a.length!==b.length)return false;
 let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];
 return diff===0;
};
function demand(owner){
 if(typeof owner!=='string'||!OWNER.test(owner))
  throw Error('D1_PRF_INVALID_OWNER');
 if(!global.isSecureContext||!crypto?.subtle||
    !global.PublicKeyCredential||!navigator.credentials||
    !navigator.credentials.create||!navigator.credentials.get)
  throw Error('D1_PRF_BROWSER_UNAVAILABLE');
 if(navigator.userActivation && !navigator.userActivation.isActive)
  throw Error('D1_PRF_USER_GESTURE_REQUIRED');
}
const aad=(owner,recordId,credentialId,origin,purpose)=>enc.encode(
 JSON.stringify([FORMAT,VERSION,owner,recordId,credentialId,origin,purpose,'HKDF-SHA256','AES-256-GCM']));
async function hkdf(prfOutput,salt,owner){
 const seed=await crypto.subtle.importKey('raw',prfOutput,'HKDF',false,['deriveKey']);
 return crypto.subtle.deriveKey({
  name:'HKDF',hash:'SHA-256',salt,
  info:enc.encode('IAMINA|D1|PRF_PASSKEY_KEK|v1|'+owner),
 },seed,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
function store(){
 return new Promise((resolve,reject)=>{
  const q=indexedDB.open(DBNAME,1);
  q.onupgradeneeded=()=>q.result.createObjectStore(STORE,{keyPath:'owner'});
  q.onsuccess=()=>resolve(q.result);
  q.onerror=()=>reject(Error('D1_PRF_STORAGE_ERROR'));
  q.onblocked=()=>reject(Error('D1_PRF_STORAGE_BLOCKED'));
 });
}
function read(db,owner){
 return new Promise((resolve,reject)=>{
  const tx=db.transaction(STORE,'readonly');
  const q=tx.objectStore(STORE).get(owner);
  q.onsuccess=()=>resolve(q.result||null);
  q.onerror=()=>reject(Error('D1_PRF_READ_FAILED'));
 });
}
function add(db,row){
 return new Promise((resolve,reject)=>{
  const tx=db.transaction(STORE,'readwrite');
  tx.objectStore(STORE).add(row);
  tx.oncomplete=()=>resolve();
  tx.onerror=()=>reject(Error('D1_PRF_ENROLLED_OR_WRITE_FAILED'));
  tx.onabort=()=>reject(Error('D1_PRF_ENROLLED_OR_ABORTED'));
 });
}
async function withDb(fn){
 const db=await store();try{return await fn(db)}finally{db.close()}
}
function assertUV(credential,expectedId,expectedChallenge){
 if(!credential||credential.type!=='public-key'||!credential.rawId)
  throw Error('D1_PRF_BAD_ASSERTION');
 const id=new Uint8Array(credential.rawId);
 if(!equal(id,expectedId))throw Error('D1_PRF_WRONG_CREDENTIAL');
 const data=credential.response?.authenticatorData;
 const bytes=data&&new Uint8Array(data);
 if(!bytes||bytes.length<37||(bytes[32]&0x01)!==0x01||(bytes[32]&0x04)!==0x04)
  throw Error('D1_PRF_USER_VERIFICATION_REQUIRED');
 let cd;
 try{cd=JSON.parse(new TextDecoder().decode(credential.response.clientDataJSON))}
 catch{throw Error('D1_PRF_BAD_CLIENTDATA')}
 if(cd.type!=='webauthn.get'||cd.origin!==location.origin||
   cd.crossOrigin===true||!equal(rawUrl(cd.challenge),expectedChallenge))
  throw Error('D1_PRF_ORIGIN_CHALLENGE_MISMATCH');
 const out=credential.getClientExtensionResults()?.prf?.results?.first;
 if(!(out instanceof ArrayBuffer)||out.byteLength!==32)
  throw Error('D1_PRF_ACTUAL_OUTPUT_REQUIRED');
 return new Uint8Array(out);
}
async function prfAssertion(credentialId,input){
 const challenge=random(32);
 const assertion=await navigator.credentials.get({publicKey:{
  challenge,timeout:45000,rpId:location.hostname,
  allowCredentials:[{type:'public-key',id:credentialId,transports:['internal']}],
  userVerification:'required',extensions:{prf:{eval:{first:input}}},
 }});
 return assertUV(assertion,credentialId,challenge);
}
function scopeRecord(rec,owner){
 if(!rec||rec.format!==FORMAT||rec.version!==VERSION||
   rec.owner!==owner||rec.origin!==location.origin||
   rec.rpId!==location.hostname||typeof rec.credentialId!=='string'||
   typeof rec.ciphertext!=='string')
  throw Error('D1_PRF_MISSING_OR_FOREIGN');
 return rec;
}
async function enroll(owner,dek){
 demand(owner);
 if(!(dek instanceof Uint8Array)||dek.length!==32||dek.every(x=>x===0))
  throw Error('D1_PRF_INVALID_DEK');
 const snapshot=Uint8Array.from(dek);
 try{
  return await withDb(async db=>{
   if(await read(db,owner))throw Error('D1_PRF_ALREADY_ENROLLED');
   const prfInput=random(32);
   const create=await navigator.credentials.create({publicKey:{
    challenge:random(32),
    rp:{name:'IAMINA D1 research only',id:location.hostname},
    user:{id:random(32),name:'research-key-only',displayName:'Research key only'},
    pubKeyCredParams:[{type:'public-key',alg:-7},{type:'public-key',alg:-257}],
    timeout:45000,attestation:'none',
    authenticatorSelection:{
      authenticatorAttachment:'platform',residentKey:'required',
      requireResidentKey:true,userVerification:'required',
    },
    extensions:{prf:{eval:{first:prfInput}}},
   }});
   if(!create||create.type!=='public-key'||!create.rawId)
    throw Error('D1_PRF_CREATION_INVALID');
   if(create.authenticatorAttachment==='cross-platform')
    throw Error('D1_PRF_PLATFORM_AUTHENTICATOR_REQUIRED');
   const regPrf=create.getClientExtensionResults()?.prf;
   if(regPrf?.enabled!==true)
    throw Error('D1_PRF_NOT_ENABLED_ON_CREDENTIAL');
   const credentialId=new Uint8Array(create.rawId);
   const prf=await prfAssertion(credentialId,prfInput);
   const recordId=b64(random(16)),salt=random(16),nonce=random(12);
   try{
    const kek=await hkdf(prf,salt,owner);
    const sealed=await crypto.subtle.encrypt({
     name:'AES-GCM',iv:nonce,tagLength:128,
     additionalData:aad(owner,recordId,b64(credentialId),location.origin,'dek'),
    },kek,snapshot);
    const row={format:FORMAT,version:VERSION,owner,recordId,
      origin:location.origin,rpId:location.hostname,
      credentialId:b64(credentialId),prfInput:b64(prfInput),salt:b64(salt),
      nonce:b64(nonce),ciphertext:b64(new Uint8Array(sealed))};
    await add(db,row);
    return Object.freeze({owner,status:'prf_enrolled',version:VERSION});
   }finally{prf.fill(0)}
  });
 }finally{snapshot.fill(0);dek.fill(0)}
}
async function unlock(owner){
 demand(owner);
 return withDb(async db=>{
  const row=scopeRecord(await read(db,owner),owner);
  const credentialId=raw(row.credentialId),input=raw(row.prfInput,32);
  const prf=await prfAssertion(credentialId,input);
  try{
   const kek=await hkdf(prf,raw(row.salt,16),owner);
   let bytes;
   try{
    bytes=new Uint8Array(await crypto.subtle.decrypt({
      name:'AES-GCM',iv:raw(row.nonce,12),tagLength:128,
      additionalData:aad(owner,row.recordId,row.credentialId,location.origin,'dek'),
    },kek,raw(row.ciphertext,48)));
   }catch{throw Error('D1_PRF_AUTH_FAILED')}
   if(bytes.length!==32||bytes.every(x=>x===0))
    throw Error('D1_PRF_WRONG_KEY_MATERIAL');
   return bytes;
  }finally{prf.fill(0)}
 });
}
async function inspect(owner){
 if(typeof owner!=='string'||!OWNER.test(owner))
  throw Error('D1_PRF_INVALID_OWNER');
 const info=await withDb(db=>read(db,owner));
 return Object.freeze({enrolled:!!info,owner,
  hasPrfWrap:!!info?.ciphertext,version:info?.version??null});
}
async function capability(){
 const secure=!!global.isSecureContext;
 const api=!!global.PublicKeyCredential&&!!navigator.credentials;
 let uvPlatform=null,clientPrf=null;
 if(api&&PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable){
  try{uvPlatform=await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()}
  catch{uvPlatform=null}
 }
 if(api&&PublicKeyCredential.getClientCapabilities){
  try{clientPrf=(await PublicKeyCredential.getClientCapabilities()).prf??null}
  catch{clientPrf=null}
 }
 // Never mark actual PRF support from capability hints alone.
 return Object.freeze({secure,api,uvPlatform,clientPrf,
   provenPrfCredential:false,patientReady:false});
}
global.iaminaD1PrfGate=Object.freeze({enroll,unlock,inspect,capability});
})(window);
