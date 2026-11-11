// D1 B: experimental encrypted export codec, SYNTHETIC ONLY.
// Not wired to LocalBackup or patient UI. Never serialize recovery keys.
const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder('utf-8', {fatal: true});
const FORMAT='IAMINA_D1_BACKUP';
const VERSION=1;
const CONTEXT='IAMINA|D1|backup|v1|';
function requireOwner(owner) {
  if (typeof owner!=='string' ||
    !/^amina_vault_v1_(native_[1-9][0-9]*|device_[a-f0-9]{32})$/.test(owner))
    throw new Error('INVALID_OWNER');
}
function requireKey(key) {
  if (!(key instanceof Uint8Array) || key.byteLength!==32 ||
      key.every(v=>v===0)) throw new Error('INVALID_RECOVERY_KEY');
}
function requireCrypto(cryptoProvider) {
  if (!cryptoProvider?.subtle || typeof cryptoProvider.getRandomValues!=='function')
    throw new Error('WEBCRYPTO_REQUIRED');
}
function encodeB64(bytes) {
  let raw='';
  for(let offset=0;offset<bytes.length;offset+=8192)
    raw+=String.fromCharCode(...bytes.subarray(offset,offset+8192));
  return btoa(raw);
}
function decodeB64(s,expectedLength=null) {
  if(typeof s!=='string'||s.length===0||!/^([A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))
    throw new Error('MALFORMED_BASE64');
  const str=atob(s);
  if(expectedLength!==null&&str.length!==expectedLength)
    throw new Error('MALFORMED_BYTE_LENGTH');
  return Uint8Array.from(str,c=>c.charCodeAt(0));
}
function metadata(owner,schema) {
  return textEncoder.encode(JSON.stringify([FORMAT,VERSION,owner,schema,'AES-256-GCM','HKDF-SHA256']));
}
async function aesKey(cryptoProvider,key,owner,salt) {
  const material=await cryptoProvider.subtle.importKey('raw',key,'HKDF',false,['deriveKey']);
  return cryptoProvider.subtle.deriveKey(
    {name:'HKDF',hash:'SHA-256',salt,info:textEncoder.encode(CONTEXT+owner)},
    material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
function requireSchema(schema) {
  if(!Number.isSafeInteger(schema)||schema<1||schema>10000)
    throw new Error('INVALID_SCHEMA');
}
// Recovery material is 32 random bytes protected out-of-band, NOT an ordinary
// password. Password-derived recovery requires a separate audited KDF design.
export async function encryptBackup(cryptoProvider,{owner,schema,plaintext,recoveryKey}) {
  requireCrypto(cryptoProvider);requireOwner(owner);requireSchema(schema);requireKey(recoveryKey);
  if(typeof plaintext!=='string')throw new Error('INVALID_PLAINTEXT');
  const salt=cryptoProvider.getRandomValues(new Uint8Array(16));
  const nonce=cryptoProvider.getRandomValues(new Uint8Array(12));
  const key=await aesKey(cryptoProvider,recoveryKey,owner,salt);
  const cipher=await cryptoProvider.subtle.encrypt({
    name:'AES-GCM',iv:nonce,additionalData:metadata(owner,schema),tagLength:128,
  },key,textEncoder.encode(plaintext));
  return JSON.stringify({
    format:FORMAT,version:VERSION,owner,schema,
    cipher:'AES-256-GCM',kdf:'HKDF-SHA256',
    salt:encodeB64(salt),nonce:encodeB64(nonce),
    ciphertext:encodeB64(new Uint8Array(cipher)),
  });
}
export async function decryptBackup(cryptoProvider,{expectedOwner,expectedSchema,envelope,recoveryKey}) {
  requireCrypto(cryptoProvider);requireOwner(expectedOwner);
  requireSchema(expectedSchema);requireKey(recoveryKey);
  let parsed;
  try{parsed=JSON.parse(envelope);}catch{throw new Error('INVALID_ENVELOPE');}
  if(!parsed||typeof parsed!=='object'||Array.isArray(parsed)||
     parsed.format!==FORMAT||parsed.version!==VERSION||
     parsed.cipher!=='AES-256-GCM'||parsed.kdf!=='HKDF-SHA256'||
     parsed.schema!==expectedSchema||parsed.owner!==expectedOwner)
    throw new Error('BACKUP_IDENTITY_OR_VERSION_MISMATCH');
  const salt=decodeB64(parsed.salt,16);
  const nonce=decodeB64(parsed.nonce,12);
  const ciphertext=decodeB64(parsed.ciphertext);
  if(ciphertext.length<16)throw new Error('INVALID_CIPHERTEXT');
  const key=await aesKey(cryptoProvider,recoveryKey,expectedOwner,salt);
  try{
    const clear=await cryptoProvider.subtle.decrypt({
      name:'AES-GCM',iv:nonce,
      additionalData:metadata(expectedOwner,expectedSchema),tagLength:128,
    },key,ciphertext);
    return textDecoder.decode(clear);
  }catch {throw new Error('BACKUP_AUTHENTICATION_FAILED');}
}
