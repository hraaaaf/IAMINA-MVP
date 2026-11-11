// D1 P0-C CRYPTO SPIKE. Synthetic payloads only. NOT connected to Drift,
// IndexedDB/OPFS or patient backup. Never treat this as encryption-at-rest proof.
// No key/passphrase is persisted, logged, or sent over the network.
const FORMAT = 'iamina-d1-synthetic-envelope-v1';
const te = new TextEncoder();
const td = new TextDecoder('utf-8', {fatal:true});
const MIN_ITERATIONS = 310000;
const encoding = (bytes) => btoa(String.fromCharCode(...bytes));
const decoding = (value) => {
  if (typeof value !== 'string' || !/^[A-Za-z0-9+/]*={0,2}$/.test(value))
    throw new Error('invalid envelope encoding');
  return Uint8Array.from(atob(value), (char) => char.charCodeAt(0));
};
const secureRandom = (length) => {
  const b = new Uint8Array(length);
  globalThis.crypto.getRandomValues(b);
  return b;
};
const validOwner = (value) => typeof value === 'string' &&
  value.startsWith('amina_vault_v1_') && value.length <= 150;
const aad = (ownerScope, schemaVersion) =>
  te.encode(JSON.stringify([FORMAT, ownerScope, schemaVersion]));
const derive = async (passphrase, salt, iterations) => {
  if (typeof passphrase !== 'string' || passphrase.length < 12) {
    throw new Error('strong recovery secret required');
  }
  const material = await crypto.subtle.importKey('raw', te.encode(passphrase),
    'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey(
    {name:'PBKDF2',hash:'SHA-256',salt,iterations},material,
    {name:'AES-GCM',length:256},false,['encrypt','decrypt']);
};
export async function encryptSyntheticPayload({
  ownerScope, plaintext, passphrase, schemaVersion=12,
}) {
  if (!validOwner(ownerScope) || !Number.isSafeInteger(schemaVersion) ||
      schemaVersion < 1 || typeof plaintext !== 'string') {
    throw new Error('invalid synthetic vault envelope request');
  }
  const salt = secureRandom(16), iv = secureRandom(12);
  const key = await derive(passphrase, salt, MIN_ITERATIONS);
  const ciphertext = await crypto.subtle.encrypt(
    {name:'AES-GCM',iv,additionalData:aad(ownerScope,schemaVersion),
      tagLength:128},key,te.encode(plaintext));
  return Object.freeze({
    format:FORMAT,ownerScope,schemaVersion,iterations:MIN_ITERATIONS,
    salt:encoding(salt),iv:encoding(iv),
    ciphertext:encoding(new Uint8Array(ciphertext)),
  });
}
export async function decryptSyntheticPayload({
  envelope, expectedOwner, passphrase,
}) {
  if (!envelope || typeof envelope !== 'object' || !validOwner(expectedOwner) ||
      envelope.format !== FORMAT || envelope.ownerScope !== expectedOwner ||
      !Number.isSafeInteger(envelope.schemaVersion) ||
      envelope.schemaVersion < 1 ||
      envelope.iterations !== MIN_ITERATIONS ||
      Object.keys(envelope).sort().join('|') !==
        'ciphertext|format|iterations|iv|ownerScope|salt|schemaVersion') {
    throw new Error('untrusted or foreign vault envelope');
  }
  const salt = decoding(envelope.salt),iv = decoding(envelope.iv);
  const ciphertext = decoding(envelope.ciphertext);
  if (salt.length !== 16 || iv.length !== 12 || ciphertext.length < 16)
    throw new Error('invalid synthetic envelope lengths');
  const key = await derive(passphrase,salt,MIN_ITERATIONS);
  const plaintext = await crypto.subtle.decrypt(
    {name:'AES-GCM',iv,additionalData:aad(expectedOwner,envelope.schemaVersion),
      tagLength:128},key,ciphertext);
  return td.decode(plaintext);
}
