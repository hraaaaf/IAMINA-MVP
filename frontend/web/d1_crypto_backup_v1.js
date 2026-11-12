/* IAMINA D1 experimental WebCrypto. Bundled locally; no network or logging.
 * NOT available in deployed IAMINA until review and explicit authorization.
 * 32-byte recovery secret must be random; do not substitute a human password.
 * Anti-rollback/escrow/custody and external security audit remain mandatory.
 */
(function attachD1Backup(global) {
  'use strict';
  const enc = new TextEncoder();
  const dec = new TextDecoder('utf-8',{fatal:true});
  const fmt = 'IAMINA_D1_BACKUP';
  const ownerPattern = /^amina_vault_v1_(?:native_[1-9]\d*|device_[a-f0-9]{32})$/;
  const b64 = bytes => {
    let s=''; for(const b of bytes)s+=String.fromCharCode(b);return btoa(s);
  };
  const un64 = (s,len) => {
    if(typeof s!=='string'||!/^([A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
      throw Error('D1_BACKUP_FORMAT');
    const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));
    if(len!==undefined&&b.length!==len)throw Error('D1_BACKUP_SIZE');
    return b;
  };
  const checked = (owner,recovery) => {
    if(typeof owner!=='string'||!ownerPattern.test(owner))
      throw Error('D1_BACKUP_OWNER');
    if(!(recovery instanceof Uint8Array)||recovery.length!==32||
       recovery.every(v=>v===0))throw Error('D1_BACKUP_KEY');
    if(!global.crypto||!global.crypto.subtle||!global.crypto.getRandomValues)
      throw Error('D1_BACKUP_WEBCRYPTO_UNAVAILABLE');
  };
  const aad = (owner,schema,keyId,createdAt) =>
    enc.encode(JSON.stringify([fmt,1,owner,schema,keyId,createdAt,'HKDF-SHA256','AES-256-GCM']));
  async function derive(owner,recovery,salt) {
    const seed=await crypto.subtle.importKey('raw',recovery,'HKDF',false,['deriveKey']);
    return crypto.subtle.deriveKey({
      name:'HKDF',hash:'SHA-256',salt,
      info:enc.encode('IAMINA|D1|CLINICAL_BACKUP|v1|'+owner),
    },seed,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
  }
  async function seal(owner,plaintext,recovery) {
    checked(owner,recovery);
    if(typeof plaintext!=='string')throw Error('D1_BACKUP_PAYLOAD');
    let root;
    try{root=JSON.parse(plaintext)}catch{throw Error('D1_BACKUP_JSON')}
    if(!root||root.formatVersion!==2||root.vaultName!==owner||
       !Number.isSafeInteger(root.schemaVersion)||root.schemaVersion<1||
       typeof root.createdAtUtc!=='string')throw Error('D1_BACKUP_SCOPE');
    const salt=crypto.getRandomValues(new Uint8Array(16));
    const nonce=crypto.getRandomValues(new Uint8Array(12));
    const keyId=b64(crypto.getRandomValues(new Uint8Array(16)));
    const key=await derive(owner,recovery,salt);
    const sealed=await crypto.subtle.encrypt({
      name:'AES-GCM',iv:nonce,
      additionalData:aad(owner,root.schemaVersion,keyId,root.createdAtUtc),
      tagLength:128,
    },key,enc.encode(plaintext));
    return JSON.stringify({
      format:fmt,version:1,owner,schemaVersion:root.schemaVersion,
      createdAtUtc:root.createdAtUtc,keyId,salt:b64(salt),
      nonce:b64(nonce),ciphertext:b64(new Uint8Array(sealed)),
    });
  }
  async function open(expectedOwner,envelope,recovery) {
    checked(expectedOwner,recovery);
    let obj;
    try{obj=JSON.parse(envelope)}catch{throw Error('D1_BACKUP_FORMAT')}
    if(!obj||Array.isArray(obj)||obj.format!==fmt||obj.version!==1||
       obj.owner!==expectedOwner||
       !Number.isSafeInteger(obj.schemaVersion)||obj.schemaVersion<1||
       typeof obj.createdAtUtc!=='string')throw Error('D1_BACKUP_OWNER_OR_FORMAT');
    const salt=un64(obj.salt,16),nonce=un64(obj.nonce,12);
    const keyId=un64(obj.keyId,16);
    const ciphertext=un64(obj.ciphertext);
    if(ciphertext.length<17)throw Error('D1_BACKUP_CIPHERTEXT');
    const key=await derive(expectedOwner,recovery,salt);
    let clear;
    try{
      clear=await crypto.subtle.decrypt({
        name:'AES-GCM',iv:nonce,tagLength:128,
        additionalData:aad(expectedOwner,obj.schemaVersion,b64(keyId),obj.createdAtUtc),
      },key,ciphertext);
    }catch{throw Error('D1_BACKUP_AUTH_FAILED')}
    let result;
    try{result=dec.decode(clear)}catch{throw Error('D1_BACKUP_DECODE')}
    let root;
    try{root=JSON.parse(result)}catch{throw Error('D1_BACKUP_BAD_JSON')}
    if(root.formatVersion!==2||root.vaultName!==expectedOwner||
       root.schemaVersion!==obj.schemaVersion||
       root.createdAtUtc!==obj.createdAtUtc)throw Error('D1_BACKUP_INNER_MISMATCH');
    return result;
  }
  // Freeze to prevent accidental runtime replacement. This is NOT a defense
  // against arbitrary same-origin script injection (XSS).
  global.iaminaD1CryptoBackup=Object.freeze({seal,open});
})(window);
