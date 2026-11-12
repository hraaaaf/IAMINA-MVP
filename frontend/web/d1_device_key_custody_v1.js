/* D1 EXPERIMENTAL: per-owner 256-bit DEK, non-exportable WebCrypto KEK
 * persisted via IndexedDB + separate patient-held 256-bit recovery secret.
 * NON-PRODUCTION: a same-origin script / XSS may USE an IndexedDB CryptoKey.
 * This is not hardware protection, WebAuthn PRF, independent audit or proof
 * of resistance to a compromised browser profile.
 * No patient data, passwords, recovery secrets or DEK are intentionally stored.
 */
(function(global){
'use strict';
const FORMAT='IAMINA_D1_DEVICE_DEK',VERSION=1,DBNAME='iamina_d1_key_custody_v1';
const OWNER=/^amina_vault_v1_(?:native_[1-9]\d*|device_[a-f0-9]{32})$/;
const text=new TextEncoder();
const validOwner=owner=>{
  if(typeof owner!=='string'||!OWNER.test(owner))throw Error('D1_CUSTODY_OWNER_DENIED');
};
const encode=bytes=>{
  let s='';for(const c of bytes)s+=String.fromCharCode(c);return btoa(s);
};
const decode=(s,length)=>{
  if(typeof s!=='string'||!/^([A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
    throw Error('D1_CUSTODY_BAD_ENCODING');
  const bytes=Uint8Array.from(atob(s),c=>c.charCodeAt(0));
  if(length!==undefined&&bytes.length!==length)throw Error('D1_CUSTODY_BAD_LENGTH');
  return bytes;
};
const aad=(owner,id,purpose)=>text.encode(
  JSON.stringify([FORMAT,VERSION,owner,id,purpose,'AES-256-GCM']));
function openStore(){
 return new Promise((resolve,reject)=>{
  const req=indexedDB.open(DBNAME,1);
  req.onupgradeneeded=()=>{
   if(!req.result.objectStoreNames.contains('vaults'))
     req.result.createObjectStore('vaults',{keyPath:'owner'});
  };
  req.onsuccess=()=>resolve(req.result);
  req.onerror=()=>reject(Error('D1_CUSTODY_STORAGE_UNAVAILABLE'));
  req.onblocked=()=>reject(Error('D1_CUSTODY_STORAGE_BLOCKED'));
 });
}
function get(db,owner){
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('vaults','readonly');
  const req=tx.objectStore('vaults').get(owner);
  req.onsuccess=()=>resolve(req.result||null);
  req.onerror=()=>reject(Error('D1_CUSTODY_READ_FAIL'));
 });
}
function add(db,record){
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('vaults','readwrite');
  tx.objectStore('vaults').add(record);
  tx.oncomplete=()=>resolve();
  tx.onerror=()=>reject(Error('D1_CUSTODY_EXISTS_OR_WRITE_FAILED'));
  tx.onabort=()=>reject(Error('D1_CUSTODY_EXISTS_OR_ABORTED'));
 });
}
function replace(db,expected,newRecord){
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('vaults','readwrite');
  const store=tx.objectStore('vaults');
  const getReq=store.get(expected.owner);
  let changed=false;
  getReq.onsuccess=()=>{
   const current=getReq.result;
   if(!current||current.id!==expected.id||current.version!==VERSION||
      current.status!==expected.status||
      current.revision!==expected.revision)return;
   // Optimistic version condition; two tabs cannot overwrite an account
   // with a different record id or change the state unexpectedly.
   store.put({...newRecord,revision:expected.revision+1});changed=true;
  };
  tx.oncomplete=()=>changed?resolve():reject(Error('D1_CUSTODY_CONCURRENT_CHANGE'));
  tx.onerror=()=>reject(Error('D1_CUSTODY_WRITE_FAIL'));
  tx.onabort=()=>reject(Error('D1_CUSTODY_WRITE_ABORT'));
 });
}
const requireRecord=(r,owner)=>{
 if(!r||r.format!==FORMAT||r.version!==VERSION||r.owner!==owner||
   typeof r.id!=='string'||typeof r.status!=='string')
    throw Error('D1_CUSTODY_NOT_ENROLLED_OR_TAMPERED');
 return r;
};
async function deriveRecovery(secret,salt,owner){
 const raw=await crypto.subtle.importKey('raw',secret,'HKDF',false,['deriveKey']);
 return crypto.subtle.deriveKey({
  name:'HKDF',hash:'SHA-256',salt,
  info:text.encode('IAMINA|D1|DEVICE_DEK_RECOVERY|v1|'+owner),
 },raw,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
const freshDeviceKek=()=>crypto.subtle.generateKey({name:'AES-GCM',length:256},
 false,['encrypt','decrypt']);
const random=n=>crypto.getRandomValues(new Uint8Array(n));
async function seal(key,nonce,owner,id,purpose,bytes){
 const out=await crypto.subtle.encrypt({
  name:'AES-GCM',iv:nonce,additionalData:aad(owner,id,purpose),tagLength:128,
 },key,bytes);
 return encode(new Uint8Array(out));
}
async function open(key,nonce,owner,id,purpose,cipher){
 try{
  const out=await crypto.subtle.decrypt({
   name:'AES-GCM',iv:decode(nonce,12),
   additionalData:aad(owner,id,purpose),tagLength:128,
  },key,decode(cipher,48));
  const d=new Uint8Array(out);
  if(d.length!==32||d.every(x=>x===0))throw Error('D1_CUSTODY_EMPTY_DEK');
  return d;
 }catch{throw Error('D1_CUSTODY_AUTH_DENIED')}
}
function equal32(a,b){
 if(a.length!==32||b.length!==32)return false;
 let acc=0;for(let i=0;i<32;i++)acc|=(a[i]^b[i]);return acc===0;
}
const withStore=async cb=>{
 const db=await openStore();
 try{return await cb(db)}finally{db.close()}
};
async function create(owner){
 validOwner(owner);
 if(!crypto?.subtle||!crypto?.getRandomValues)throw Error('D1_CUSTODY_CRYPTO_REQUIRED');
 return withStore(async db=>{
  if(await get(db,owner))throw Error('D1_CUSTODY_ALREADY_ENROLLED');
  const dek=random(32),recovery=random(32);
  try{
   const id=encode(random(16)),key=await freshDeviceKek();
   const deviceNonce=random(12),recoverySalt=random(16),recoveryNonce=random(12);
   const recoveryKek=await deriveRecovery(recovery,recoverySalt,owner);
   const rec={
    owner,format:FORMAT,version:VERSION,id,
    status:'pending_confirmation',revision:1,
    // JS CryptoKey is structured-cloned by IndexedDB, extractable:false.
    deviceKek:key,
    device:{nonce:encode(deviceNonce),
      ciphertext:await seal(key,deviceNonce,owner,id,'device',dek)},
    recovery:{salt:encode(recoverySalt),nonce:encode(recoveryNonce),
      ciphertext:await seal(recoveryKek,recoveryNonce,owner,id,'recovery',dek)},
   };
   await add(db,rec);
   // Return recovery once. Do not persist it in browser storage.
   return Object.freeze({owner,id,recoveryKey:encode(recovery),
     status:'pending_confirmation'});
  }finally{dek.fill(0);recovery.fill(0)}
 });
}
async function openRecovery(rec,owner,recoveryB64){
 const secret=decode(recoveryB64,32);
 try{
  if(secret.every(x=>x===0))throw Error('D1_CUSTODY_RECOVERY_INVALID');
  const salt=decode(rec.recovery.salt,16);
  const key=await deriveRecovery(secret,salt,owner);
  return await open(key,rec.recovery.nonce,owner,rec.id,'recovery',rec.recovery.ciphertext);
 }finally{secret.fill(0)}
}
async function openDevice(rec,owner){
 if(!rec.deviceKek||rec.deviceKek.extractable!==false||
    rec.deviceKek.type!=='secret')throw Error('D1_CUSTODY_DEVICE_KEY_UNAVAILABLE');
 return open(rec.deviceKek,rec.device.nonce,owner,rec.id,'device',rec.device.ciphertext);
}
async function confirm(owner,recoveryB64){
 validOwner(owner);
 return withStore(async db=>{
  const r=requireRecord(await get(db,owner),owner);
  if(r.status!=='pending_confirmation')throw Error('D1_CUSTODY_CONFIRM_STATE');
  const recovered=await openRecovery(r,owner,recoveryB64);
  const local=await openDevice(r,owner);
  try{
   if(!equal32(recovered,local))throw Error('D1_CUSTODY_KEY_MISMATCH');
   await replace(db,r,{...r,status:'ready'});
   return Object.freeze({owner,status:'ready'});
  }finally{recovered.fill(0);local.fill(0)}
 });
}
async function unlockDevice(owner){
 validOwner(owner);
 return withStore(async db=>{
  const rec=requireRecord(await get(db,owner),owner);
  if(rec.status!=='ready')throw Error('D1_CUSTODY_RECOVERY_NOT_CONFIRMED');
  return openDevice(rec,owner);
 });
}
async function unlockRecovery(owner,recoveryB64){
 validOwner(owner);
 return withStore(async db=>{
  const rec=requireRecord(await get(db,owner),owner);
  if(rec.status!=='ready')throw Error('D1_CUSTODY_RECOVERY_NOT_CONFIRMED');
  return openRecovery(rec,owner,recoveryB64);
 });
}
async function rebindDevice(owner,recoveryB64){
 validOwner(owner);
 return withStore(async db=>{
  const rec=requireRecord(await get(db,owner),owner);
  if(rec.status!=='ready')throw Error('D1_CUSTODY_NOT_CONFIRMED');
  const recovered=await openRecovery(rec,owner,recoveryB64);
  try{
   const key=await freshDeviceKek(),nonce=random(12);
   const newRec={...rec,deviceKek:key,device:{
    nonce:encode(nonce),ciphertext:await seal(key,nonce,owner,rec.id,'device',recovered)}};
   await replace(db,rec,newRec);
   return Object.freeze({owner,status:'ready',deviceRebound:true});
  }finally{recovered.fill(0)}
 });
}
async function inspect(owner){
 validOwner(owner);
 return withStore(async db=>{
  const rec=await get(db,owner);
  if(!rec)return Object.freeze({enrolled:false});
  requireRecord(rec,owner);
  return Object.freeze({enrolled:true,status:rec.status,
   owner,version:rec.version,id:rec.id,
   deviceKeyExtractable:rec.deviceKek?.extractable??null,
   hasRecoveryEnvelope:!!rec.recovery?.ciphertext,
   // These fields are intentionally unavailable through inspect().
  });
 });
}
global.iaminaD1DeviceKeyCustody=Object.freeze({
 create,confirm,unlockDevice,unlockRecovery,rebindDevice,inspect,
});
})(window);
