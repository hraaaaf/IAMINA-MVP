(() => {
  'use strict';

  const ok = (payload = {}) => JSON.stringify({ ok: true, ...payload });
  const fail = (code) => JSON.stringify({ ok: false, code });

  const toBase64Url = (buffer) => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/g, '');
  };

  const fromBase64Url = (value) => {
    const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return bytes;
  };

  const randomBytes = (length) => {
    const bytes = new Uint8Array(length);
    crypto.getRandomValues(bytes);
    return bytes;
  };

  const concat = (...arrays) => {
    const length = arrays.reduce((sum, array) => sum + array.length, 0);
    const output = new Uint8Array(length);
    let offset = 0;
    for (const array of arrays) {
      output.set(array, offset);
      offset += array.length;
    }
    return output;
  };

  const bytesEqual = (a, b) => {
    if (a.length !== b.length) return false;
    let mismatch = 0;
    for (let i = 0; i < a.length; i += 1) mismatch |= a[i] ^ b[i];
    return mismatch === 0;
  };

  const sha256 = async (bytes) =>
    new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));

  const readUint32 = (bytes, offset) =>
    ((bytes[offset] << 24) |
      (bytes[offset + 1] << 16) |
      (bytes[offset + 2] << 8) |
      bytes[offset + 3]) >>> 0;

  const assertClientData = (clientDataJson, expectedType, expectedChallenge) => {
    const bytes = new Uint8Array(clientDataJson);
    let parsed;
    try {
      parsed = JSON.parse(new TextDecoder().decode(bytes));
    } catch (_) {
      throw new Error('client_data_invalid');
    }
    if (parsed.type !== expectedType) throw new Error('client_type_mismatch');
    if (parsed.challenge !== toBase64Url(expectedChallenge)) {
      throw new Error('challenge_mismatch');
    }
    if (parsed.origin !== location.origin) throw new Error('origin_mismatch');
    return bytes;
  };

  const inspectAuthenticatorData = async (authenticatorData, rpId) => {
    const bytes = new Uint8Array(authenticatorData);
    if (bytes.length < 37) throw new Error('authenticator_data_short');

    const expectedRpHash = await sha256(new TextEncoder().encode(rpId));
    if (!bytesEqual(bytes.slice(0, 32), expectedRpHash)) {
      throw new Error('rp_id_hash_mismatch');
    }

    const flags = bytes[32];
    const userPresent = (flags & 0x01) !== 0;
    const userVerified = (flags & 0x04) !== 0;
    if (!userPresent) throw new Error('user_presence_missing');
    if (!userVerified) throw new Error('user_verification_missing');

    return {
      bytes,
      signCount: readUint32(bytes, 33),
    };
  };

  const readDerLength = (bytes, cursor) => {
    if (cursor.index >= bytes.length) throw new Error('signature_der_invalid');
    const first = bytes[cursor.index++];
    if ((first & 0x80) === 0) return first;
    const count = first & 0x7f;
    if (count === 0 || count > 2 || cursor.index + count > bytes.length) {
      throw new Error('signature_der_invalid');
    }
    let value = 0;
    for (let i = 0; i < count; i += 1) value = (value << 8) | bytes[cursor.index++];
    return value;
  };

  const normalizeDerInteger = (bytes) => {
    let value = bytes;
    while (value.length > 32 && value[0] === 0) value = value.slice(1);
    if (value.length > 32) throw new Error('signature_der_invalid');
    const output = new Uint8Array(32);
    output.set(value, 32 - value.length);
    return output;
  };

  const derEcdsaToRaw = (signature) => {
    const bytes = new Uint8Array(signature);
    const cursor = { index: 0 };
    if (bytes[cursor.index++] !== 0x30) throw new Error('signature_der_invalid');
    const sequenceLength = readDerLength(bytes, cursor);
    if (cursor.index + sequenceLength !== bytes.length) {
      throw new Error('signature_der_invalid');
    }

    if (bytes[cursor.index++] !== 0x02) throw new Error('signature_der_invalid');
    const rLength = readDerLength(bytes, cursor);
    const rEnd = cursor.index + rLength;
    if (rEnd > bytes.length) throw new Error('signature_der_invalid');
    const r = normalizeDerInteger(bytes.slice(cursor.index, rEnd));
    cursor.index = rEnd;

    if (bytes[cursor.index++] !== 0x02) throw new Error('signature_der_invalid');
    const sLength = readDerLength(bytes, cursor);
    const sEnd = cursor.index + sLength;
    if (sEnd !== bytes.length) throw new Error('signature_der_invalid');
    const s = normalizeDerInteger(bytes.slice(cursor.index, sEnd));

    return concat(r, s);
  };

  const mapError = (error) => {
    if (error instanceof DOMException) {
      switch (error.name) {
        case 'NotAllowedError':
          return 'user_cancelled';
        case 'InvalidStateError':
          return 'credential_state_invalid';
        case 'SecurityError':
          return 'origin_not_allowed';
        case 'NotSupportedError':
          return 'unsupported_authenticator';
        default:
          return 'webauthn_failure';
      }
    }
    if (error instanceof Error && /^[a-z0-9_]+$/.test(error.message)) {
      return error.message;
    }
    return 'app_lock_failure';
  };

  const capability = async () => {
    try {
      if (!window.isSecureContext) return ok({ capability: 'insecure_context' });
      if (!window.PublicKeyCredential || !navigator.credentials) {
        return ok({ capability: 'unavailable' });
      }
      if (typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable !== 'function') {
        return ok({ capability: 'unavailable' });
      }
      const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
      return ok({ capability: available ? 'supported' : 'unavailable' });
    } catch (_) {
      return ok({ capability: 'unavailable' });
    }
  };

  const enroll = async () => {
    try {
      const capabilityResult = JSON.parse(await capability());
      if (capabilityResult.capability !== 'supported') {
        return fail(capabilityResult.capability === 'insecure_context'
          ? 'insecure_context'
          : 'strong_auth_unavailable');
      }

      const challenge = randomBytes(32);
      const userId = randomBytes(32);
      const rpId = location.hostname;
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge,
          rp: { name: 'IAMINA' },
          user: {
            id: userId,
            name: 'iamina-local',
            displayName: 'IAMINA local',
          },
          pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            residentKey: 'preferred',
            requireResidentKey: false,
            userVerification: 'required',
          },
          timeout: 60000,
          attestation: 'none',
        },
      });

      if (!(credential instanceof PublicKeyCredential)) {
        throw new Error('credential_invalid');
      }
      const response = credential.response;
      if (!response || typeof response.getPublicKey !== 'function' ||
          typeof response.getAuthenticatorData !== 'function') {
        throw new Error('public_key_export_unavailable');
      }

      assertClientData(response.clientDataJSON, 'webauthn.create', challenge);
      const auth = await inspectAuthenticatorData(response.getAuthenticatorData(), rpId);
      const algorithm = typeof response.getPublicKeyAlgorithm === 'function'
        ? response.getPublicKeyAlgorithm()
        : null;
      if (algorithm !== -7) throw new Error('unsupported_algorithm');
      const publicKey = response.getPublicKey();
      if (!publicKey) throw new Error('public_key_export_unavailable');

      return ok({
        credential: {
          version: 1,
          credentialId: toBase64Url(credential.rawId),
          publicKeySpki: toBase64Url(publicKey),
          rpId,
          origin: location.origin,
          signCount: auth.signCount,
        },
      });
    } catch (error) {
      return fail(mapError(error));
    }
  };

  const unlock = async (credentialJson) => {
    try {
      let stored;
      try {
        stored = JSON.parse(credentialJson);
      } catch (_) {
        throw new Error('stored_credential_invalid');
      }
      if (!stored || stored.version !== 1 ||
          typeof stored.credentialId !== 'string' || !stored.credentialId ||
          typeof stored.publicKeySpki !== 'string' || !stored.publicKeySpki ||
          typeof stored.rpId !== 'string' || !stored.rpId ||
          typeof stored.origin !== 'string' || !stored.origin ||
          !Number.isInteger(stored.signCount) || stored.signCount < 0) {
        throw new Error('stored_credential_invalid');
      }
      if (!window.isSecureContext) throw new Error('insecure_context');
      if (stored.origin !== location.origin || stored.rpId !== location.hostname) {
        throw new Error('origin_mismatch');
      }

      const challenge = randomBytes(32);
      const expectedCredentialId = fromBase64Url(stored.credentialId);
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge,
          rpId: stored.rpId,
          allowCredentials: [{
            type: 'public-key',
            id: expectedCredentialId,
            transports: ['internal'],
          }],
          userVerification: 'required',
          timeout: 60000,
        },
      });

      if (!(assertion instanceof PublicKeyCredential)) {
        throw new Error('assertion_invalid');
      }
      if (!bytesEqual(new Uint8Array(assertion.rawId), expectedCredentialId)) {
        throw new Error('credential_id_mismatch');
      }

      const response = assertion.response;
      const clientData = assertClientData(
        response.clientDataJSON,
        'webauthn.get',
        challenge,
      );
      const auth = await inspectAuthenticatorData(response.authenticatorData, stored.rpId);

      const clientHash = await sha256(clientData);
      const signedData = concat(auth.bytes, clientHash);
      const publicKey = await crypto.subtle.importKey(
        'spki',
        fromBase64Url(stored.publicKeySpki),
        { name: 'ECDSA', namedCurve: 'P-256' },
        false,
        ['verify'],
      );
      const rawSignature = derEcdsaToRaw(response.signature);
      const verified = await crypto.subtle.verify(
        { name: 'ECDSA', hash: 'SHA-256' },
        publicKey,
        rawSignature,
        signedData,
      );
      if (!verified) throw new Error('signature_invalid');

      if (stored.signCount > 0 && auth.signCount > 0 && auth.signCount <= stored.signCount) {
        throw new Error('signature_counter_rollback');
      }

      return ok({ signCount: auth.signCount });
    } catch (error) {
      return fail(mapError(error));
    }
  };

  window.iaminaAppLock = Object.freeze({ capability, enroll, unlock });
})();
