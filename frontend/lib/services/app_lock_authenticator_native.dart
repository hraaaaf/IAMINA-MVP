import 'dart:io';
import 'dart:convert';

import 'package:flutter/services.dart';

import 'app_lock_authenticator.dart';

/// Platform channel for *native cryptographic* biometric signatures.
///
/// Only Android Keystore (API 30+) or iOS Secure Enclave may grant unlock.
/// Neither platform reports success from a boolean-only biometric prompt.
/// The native side creates a one-use random challenge, signs it with an
/// authentication-per-use private key and verifies that signature before reply.
final class NativeAppLockAuthenticator implements AppLockAuthenticator {
  static const channelName = 'ma.iamina.app/native_app_lock_v1';
  static const nativeOrigin = 'https://native.iamina.invalid';
  static const nativeRpId = 'ma.iamina.app';
  static const _channel = MethodChannel(channelName);

  const NativeAppLockAuthenticator();

  bool get _supportedPlatform => Platform.isAndroid || Platform.isIOS;

  @override
  Future<AppLockCapability> capability() async {
    if (!_supportedPlatform) return AppLockCapability.unavailable;
    try {
      final reply = await _channel.invokeMapMethod<String, dynamic>('capability');
      return reply?['capability'] == 'supported'
          ? AppLockCapability.supported : AppLockCapability.unavailable;
    } on PlatformException {
      return AppLockCapability.unavailable;
    } on MissingPluginException {
      return AppLockCapability.unavailable;
    }
  }

  @override
  Future<AppLockCredential> enroll() async {
    if (await capability() != AppLockCapability.supported) {
      throw const AppLockException('strong_auth_unavailable');
    }
    final reply = await _invoke('enroll');
    if (reply['verified'] != true) {
      throw const AppLockException('signature_not_verified');
    }
    final credential = AppLockCredential.decode(
      // The existing app-lock persistence protocol contains WebAuthn-shaped
      // fields. On native we pin a DISTINCT origin and RP and store a native
      // non-exportable-key handle in credentialId (never a WebAuthn token).
      _encodeCredential(reply),
    );
    if (credential.origin != nativeOrigin ||
        credential.rpId != nativeRpId ||
        !credential.credentialId.startsWith('native-bio-v1-') ||
        credential.signCount != 0) {
      throw const AppLockException('invalid_native_enrollment');
    }
    try {
      final spki = base64Decode(credential.publicKeySpki);
      if (spki.length != 91 || spki[0] != 0x30 || spki[1] != 0x59) {
        throw const AppLockException('invalid_native_public_key');
      }
    } on FormatException {
      throw const AppLockException('invalid_native_public_key');
    }
    return credential;
  }

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) async {
    if (!_supportedPlatform ||
        credential.origin != nativeOrigin ||
        credential.rpId != nativeRpId ||
        !credential.credentialId.startsWith('native-bio-v1-')) {
      throw const AppLockException('invalid_native_credential');
    }
    final reply = await _invoke('unlock', credential.toJson());
    if (reply['verified'] != true) {
      throw const AppLockException('signature_not_verified');
    }
    // Local monotonically increasing metadata only, not a server-side
    // authenticator counter or cryptographic attestation.
    return AppLockAssertion(signCount: credential.signCount + 1);
  }

  static String _encodeCredential(Map<String, dynamic> reply) {
    final credential = <String, Object>{
      'version': AppLockCredential.currentVersion,
      'credentialId': reply['credentialId'] is String
          ? reply['credentialId'] as String : '',
      'publicKeySpki': reply['publicKeySpki'] is String
          ? reply['publicKeySpki'] as String : '',
      'origin': nativeOrigin,
      'rpId': nativeRpId,
      'signCount': 0,
    };
    return jsonEncode(credential);
  }

}

AppLockAuthenticator createPlatformAppLockAuthenticator() =>
    const NativeAppLockAuthenticator();
