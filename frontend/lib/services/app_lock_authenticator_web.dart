import 'dart:convert';
import 'dart:js_interop';

import 'app_lock_authenticator.dart';

@JS('iaminaAppLock.capability')
external JSPromise<JSString> _capability();

@JS('iaminaAppLock.enroll')
external JSPromise<JSString> _enroll();

@JS('iaminaAppLock.unlock')
external JSPromise<JSString> _unlock(JSString credentialJson);

AppLockAuthenticator createPlatformAppLockAuthenticator() =>
    const _WebAppLockAuthenticator();

class _WebAppLockAuthenticator implements AppLockAuthenticator {
  const _WebAppLockAuthenticator();

  @override
  Future<AppLockCapability> capability() async {
    final result = await _call(() => _capability());
    return switch (result['capability']) {
      'supported' => AppLockCapability.supported,
      'insecure_context' => AppLockCapability.insecureContext,
      _ => AppLockCapability.unavailable,
    };
  }

  @override
  Future<AppLockCredential> enroll() async {
    final result = await _call(() => _enroll());
    final credential = result['credential'];
    if (credential is! Map<String, dynamic>) {
      throw const AppLockException('malformed_enrollment');
    }
    return AppLockCredential.decode(jsonEncode(credential));
  }

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) async {
    final result = await _call(
      () => _unlock(jsonEncode(credential.toJson()).toJS),
    );
    final signCount = result['signCount'];
    if (signCount is! int || signCount < 0) {
      throw const AppLockException('malformed_assertion');
    }
    return AppLockAssertion(signCount: signCount);
  }

  Future<Map<String, dynamic>> _call(
    JSPromise<JSString> Function() operation,
  ) async {
    try {
      final raw = (await operation().toDart).toDart;
      final decoded = jsonDecode(raw);
      if (decoded is! Map<String, dynamic>) {
        throw const AppLockException('malformed_bridge_response');
      }
      if (decoded['ok'] != true) {
        final code = decoded['code'];
        throw AppLockException(code is String ? code : 'bridge_failure');
      }
      return decoded;
    } on AppLockException {
      rethrow;
    } catch (_) {
      throw const AppLockException('bridge_unavailable');
    }
  }
}
