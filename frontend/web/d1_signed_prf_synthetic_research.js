/* IAMINA D1-6: test-only SAME assertion Django WebAuthn + browser PRF bridge.
 * No patient routes, no deployment, no device claim, no persistent vault.
 * PRF/KEK/DEK MUST NEVER be transported over HTTP. The Django verifier
 * validates the signature, challenge, RP and account; browser PRF derives
 * a NON-EXTRACTABLE synthetic KEK locally only after that server ACK.
 * A mocked credentials.get() is NOT evidence of physical Face ID.
 * Callbacks are trusted research code: XSS/malicious callbacks are out of scope.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.iaminaD1SignedPrfResearch = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const PREFIX = '/api/v1/d1-research/passkey/';
  const FORMAT = 'IAMINA_D1_SIGNED_PRF_SYNTHETIC_V1';
  const NOTE = 'IAMINA_D1_SYNTHETIC_VAULT_ONLY';
  const textEncoder = new TextEncoder();
  const textDecoder = new TextDecoder();

  function denied() { throw new Error('D1_SIGNED_PRF_RESEARCH_DENIED'); }
  function bytes(input, length) {
    if (!(input instanceof Uint8Array) ||
        (length !== undefined && input.byteLength !== length)) denied();
    return input;
  }
  function b64(input) {
    let chars = '';
    for (const value of bytes(input)) chars += String.fromCharCode(value);
    return btoa(chars).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function raw(str) {
    if (typeof str !== 'string' || !/^[A-Za-z0-9_-]+$/.test(str)) denied();
    const padded = str.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = Uint8Array.from(atob(padded + '='.repeat((4 - padded.length % 4) % 4)),
      c => c.charCodeAt(0));
    if (!decoded.length || b64(decoded) !== str) denied();
    return decoded;
  }
  function same(a, b) {
    if (a.length !== b.length) return false;
    let mismatch = 0;
    for (let i = 0; i < a.length; i++) mismatch |= a[i] ^ b[i];
    return mismatch === 0;
  }
  function scopeKey(s) {
    if (!s || s.authenticated !== true || s.patientReady !== false ||
        !/^[1-9]\d{0,18}$/.test(s.accountId) ||
        s.vaultOwner !== 'amina_vault_v1_native_' + s.accountId ||
        !/^[a-f0-9]{64}$/.test(s.sessionStamp) ||
        !Number.isSafeInteger(s.epoch) || s.epoch < 0 ||
        typeof s.credentialId !== 'string' || raw(s.credentialId).length > 1024 ||
        typeof s.origin !== 'string') denied();
    return JSON.stringify([s.accountId,s.vaultOwner,s.credentialId,s.origin,
      s.sessionStamp,s.epoch]);
  }
  function ownerKey(s) {
    return JSON.stringify([FORMAT,s.accountId,s.vaultOwner,s.credentialId,s.origin]);
  }
  function envelopeKey(e) {
    return JSON.stringify([FORMAT,e.accountId,e.vaultOwner,e.credentialId,e.origin]);
  }
  function assertLive(signal) {
    if (signal && signal.aborted) denied();
  }
  async function rpc(fetchImpl, csrfToken, method, body, signal) {
    assertLive(signal);
    const csrf = csrfToken();
    if (typeof csrf !== 'string' || !/^[a-zA-Z0-9]{16,128}$/.test(csrf)) denied();
    const response = await fetchImpl(PREFIX + method, {
      method: 'POST',mode:'same-origin',credentials:'same-origin',
      redirect:'error',cache:'no-store',signal,
      headers:{'Content-Type':'application/json','X-CSRFToken':csrf},
      body:JSON.stringify(body)
    });
    assertLive(signal);
    if (!response || response.status !== 200 || response.redirected === true) denied();
    const payload = await response.json();
    assertLive(signal);
    if (!payload || typeof payload !== 'object') denied();
    return payload;
  }
  function responsePayload(credential, challenge, credentialId, origin) {
    if (!credential || credential.type !== 'public-key' ||
        !(credential.rawId instanceof ArrayBuffer) ||
        !credential.response) denied();
    if (b64(new Uint8Array(credential.rawId)) !== credentialId) denied();
    const cd = bytes(new Uint8Array(credential.response.clientDataJSON));
    let parsed;
    try { parsed = JSON.parse(textDecoder.decode(cd)); } catch (_) { denied(); }
    if (parsed.type !== 'webauthn.get' || parsed.origin !== origin ||
        parsed.crossOrigin === true || parsed.challenge !== b64(challenge)) denied();
    const ad = bytes(new Uint8Array(credential.response.authenticatorData));
    if (ad.length < 37 || (ad[32] & 0x05) !== 0x05) denied();
    const sig = bytes(new Uint8Array(credential.response.signature));
    if (!sig.length) denied();
    const handle = credential.response.userHandle;
    return {id:credentialId,rawId:credentialId,type:'public-key',response:{
      clientDataJSON:b64(cd),authenticatorData:b64(ad),signature:b64(sig),
      userHandle:handle === null || handle === undefined ? null :
        b64(new Uint8Array(handle))
    }};
  }

  function createSignedPrfBridge({fetchImpl, credentialsGet, cryptoImpl,
    csrfToken, origin} = {}) {
    if (typeof fetchImpl !== 'function' || typeof credentialsGet !== 'function' ||
        typeof csrfToken !== 'function' || !cryptoImpl?.subtle ||
        typeof cryptoImpl.getRandomValues !== 'function' ||
        typeof origin !== 'string' || !/^https:\/\/[A-Za-z0-9.-]+$/.test(origin)) denied();
    const host = new URL(origin).hostname;
    if (origin !== 'https://' + host) denied();

    async function context(credentialId, signal) {
      raw(credentialId);
      const scope = await rpc(fetchImpl,csrfToken,'session-context',
        {credential_id:credentialId},signal);
      if (scope.credentialId !== credentialId || scope.origin !== origin) denied();
      scopeKey(scope);
      return scope;
    }

    // Prepare off the user-gesture critical path. A fresh server challenge
    // and session fingerprint are fetched BEFORE the physical button tap.
    // Prepared state is strictly single-use and held only in this JS realm.
    const consumed = new WeakSet();
    async function prepareVerification({credentialId,signal} = {}) {
      raw(credentialId);
      const startScope = await context(credentialId,signal);
      const before = scopeKey(startScope);
      const start = await rpc(fetchImpl,csrfToken,'verify/start',
        {credential_id:credentialId},signal);
      const options = start?.options;
      if (typeof start.ceremony_id !== 'string' ||
          !options || options.rpId !== host ||
          !Array.isArray(options.allowCredentials) ||
          options.allowCredentials.length !== 1 ||
          options.allowCredentials[0].id !== credentialId ||
          options.userVerification !== 'required') denied();
      const challenge = raw(options.challenge);
      if (challenge.length !== 32) denied();
      // Copy validated public options; never store PRF secret in prepared object.
      return Object.freeze({credentialId,
        ceremonyId:start.ceremony_id,
        before,
        options:Object.freeze({...options,
          challenge:Uint8Array.from(challenge),
          allowCredentials:Object.freeze([Object.freeze({
            ...options.allowCredentials[0],id:raw(credentialId)
          })])
        })
      });
    }

    async function finishPrepared({prepared,prfInput,salt,callback,signal} = {}) {
      if (!prepared || typeof prepared !== 'object' ||
          consumed.has(prepared) || typeof callback !== 'function') denied();
      bytes(prfInput,32);bytes(salt,16);
      if (typeof prepared.credentialId !== 'string' ||
          typeof prepared.before !== 'string' ||
          typeof prepared.ceremonyId !== 'string' ||
          !prepared.options || prepared.options.rpId !== host ||
          prepared.options.userVerification !== 'required' ||
          !Array.isArray(prepared.options.allowCredentials) ||
          prepared.options.allowCredentials.length !== 1) denied();
      // No awaits before credentialsGet; preserves transient Safari activation.
      // The caller MUST call finishPrepared directly in a trusted click event.
      consumed.add(prepared);
      assertLive(signal);
      const publicKey = {
        ...prepared.options,
        challenge:Uint8Array.from(prepared.options.challenge),
        allowCredentials:[{...prepared.options.allowCredentials[0],
          id:Uint8Array.from(prepared.options.allowCredentials[0].id)}],
        userVerification:'required',
        extensions:{prf:{eval:{first:Uint8Array.from(prfInput)}}}
      };
      const assertionPromise = credentialsGet({publicKey,signal});
      const assertion = await assertionPromise;
      assertLive(signal);
      const payload = responsePayload(assertion,publicKey.challenge,
        prepared.credentialId,origin);
      const results = assertion.getClientExtensionResults?.();
      const output = results?.prf?.results?.first;
      if (!(output instanceof ArrayBuffer) || output.byteLength !== 32) denied();
      const prf = new Uint8Array(output);
      try {
        const verified = await rpc(fetchImpl,csrfToken,'verify/finish',{
          ceremony_id:prepared.ceremonyId,credential:payload
        },signal);
        if (verified.status !== 'ASSERTION_VERIFIED_RESEARCH_ONLY' ||
            verified.patient_ready !== false) denied();
        const after = await context(prepared.credentialId,signal);
        if (scopeKey(after) !== prepared.before) denied();
        const seed = await cryptoImpl.subtle.importKey(
          'raw',prf,'HKDF',false,['deriveKey']);
        const kek = await cryptoImpl.subtle.deriveKey({
          name:'HKDF',hash:'SHA-256',salt,
          info:textEncoder.encode('IAMINA|D1|SIGNED_PRF|SYNTHETIC|v1|' + ownerKey(after))
        },seed,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
        if (kek.extractable) denied();
        assertLive(signal);
        await callback(Object.freeze({kek,scope:after}));
        const finalScope = await context(prepared.credentialId,signal);
        if (scopeKey(finalScope) !== prepared.before) denied();
        assertLive(signal);
        return Object.freeze({status:'D1_SIGNED_PRF_SYNTHETIC_COMPLETE',
          patientReady:false});
      } finally {
        prf.fill(0);
      }
    }

    async function withVerifiedPrf({credentialId,prfInput,salt,callback,signal} = {}) {
      // Backward-compatible CI fixture. NOT suitable for a physical Safari
      // button event: prepareVerification awaits Django and may lose activation.
      const prepared = await prepareVerification({credentialId,signal});
      return finishPrepared({prepared,prfInput,salt,callback,signal});
    }
    return Object.freeze({context,prepareVerification,finishPrepared,withVerifiedPrf});
  }

  async function sealSyntheticFixture({cryptoImpl,kek,scope,prfInput,salt} = {}) {
    bytes(prfInput,32);bytes(salt,16);scopeKey(scope);
    if (!cryptoImpl?.subtle || !cryptoImpl.getRandomValues ||
        !kek || kek.extractable !== false) denied();
    const dek = cryptoImpl.getRandomValues(new Uint8Array(32));
    const wrapIV = cryptoImpl.getRandomValues(new Uint8Array(12));
    const vaultIV = cryptoImpl.getRandomValues(new Uint8Array(12));
    try {
      const vaultKey = await cryptoImpl.subtle.importKey(
        'raw',dek,'AES-GCM',false,['encrypt']);
      const wrapped = await cryptoImpl.subtle.encrypt({
        name:'AES-GCM',iv:wrapIV,additionalData:textEncoder.encode(ownerKey(scope))
      },kek,dek);
      const ciphertext = await cryptoImpl.subtle.encrypt({
        name:'AES-GCM',iv:vaultIV,additionalData:textEncoder.encode(ownerKey(scope))
      },vaultKey,textEncoder.encode(NOTE));
      return Object.freeze({
        format:FORMAT,version:1,accountId:scope.accountId,
        vaultOwner:scope.vaultOwner,credentialId:scope.credentialId,
        origin:scope.origin,prfInput:b64(prfInput),salt:b64(salt),
        wrapIV:b64(wrapIV),vaultIV:b64(vaultIV),
        wrappedDEK:b64(new Uint8Array(wrapped)),
        ciphertext:b64(new Uint8Array(ciphertext))
      });
    } finally { dek.fill(0); }
  }

  async function openSyntheticFixture({cryptoImpl,kek,scope,envelope} = {}) {
    if (!cryptoImpl?.subtle || !kek || kek.extractable !== false ||
        !envelope || envelope.format !== FORMAT ||
        envelope.version !== 1 || envelopeKey(envelope) !== ownerKey(scope)) denied();
    const wrapped = raw(envelope.wrappedDEK);
    const dek = new Uint8Array(await cryptoImpl.subtle.decrypt({
      name:'AES-GCM',iv:bytes(raw(envelope.wrapIV),12),
      additionalData:textEncoder.encode(ownerKey(scope))
    },kek,wrapped));
    try {
      if (dek.length !== 32) denied();
      const vaultKey = await cryptoImpl.subtle.importKey(
        'raw',dek,'AES-GCM',false,['decrypt']);
      const opened = new Uint8Array(await cryptoImpl.subtle.decrypt({
        name:'AES-GCM',iv:bytes(raw(envelope.vaultIV),12),
        additionalData:textEncoder.encode(ownerKey(scope))
      },vaultKey,raw(envelope.ciphertext)));
      try { if (textDecoder.decode(opened) !== NOTE) denied(); }
      finally { opened.fill(0); }
      return Object.freeze({status:'SYNTHETIC_VAULT_OPENED',patientReady:false});
    } finally { dek.fill(0); }
  }
  return Object.freeze({
    createSignedPrfBridge,sealSyntheticFixture,openSyntheticFixture
  });
});
