// @TestOn('browser')
import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _bindingKey = 'iamina_native_account_binding_v1';
const _localSessionKey = 'iamina_local_session_v1';
const _localDeviceKey = 'iamina_local_device_id_v1';
const _bearer = 'iamina.e30:1abcde:w02_web_cold_boot_synthetic';

/// Real Chrome runtime; deliberately unerasable persistent bearer.
/// No real patient, account, external backend or network call.
class _UnwritableBrowserStorage implements FlutterSecureStorage {
  final Map<String, String> values;
  _UnwritableBrowserStorage(this.values);

  Future<String?> _read(String key) async => values[key];
  Future<void> _write(String key, String value) async {
    throw StateError('synthetic browser write unavailable');
  }
  Future<void> _delete(String key) async {
    throw StateError('synthetic browser delete unavailable');
  }

  @override
  dynamic noSuchMethod(Invocation invocation) {
    final key = invocation.namedArguments[#key] as String?;
    switch (invocation.memberName) {
      case #read:
        return _read(key!);
      case #write:
        return _write(key!, invocation.namedArguments[#value] as String);
      case #delete:
        return _delete(key!);
      default:
        throw UnsupportedError('Unexpected secure-storage operation');
    }
  }
}

AuthService _webService(_UnwritableBrowserStorage storage) => AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        fail('Cold boot must not call HTTP: ${request.url.path}');
      }),
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 F05B WEB RED: cold boot never publishes an unerasable cached native bearer',
      () async {
    final storage = _UnwritableBrowserStorage({
      _tokenKey: _bearer,
      _bindingKey: jsonEncode({'token': _bearer, 'user_id': 734}),
      _localSessionKey: 'enrolled',
      _localDeviceKey: 'synthetic-device-f05b',
    });
    final reopened = _webService(storage);
    await reopened.initialize();

    // Browser data can be stale after a failed logout even if no durable
    // marker can be written. Without explicit reauthentication it must not
    // grant remote identity, API egress, or ANY clinical vault authority.
    expect(reopened.isInitialized, isTrue);
    expect(reopened.isAuthenticated, isFalse);
    expect(reopened.hasRemoteApiCredential, isFalse);
    expect(reopened.boundNativeAccountId, isNull);
    expect(await reopened.getIdToken(), isNull);
    expect(await reopened.resolvePatientVaultScope(), isNull);
    // The test *requires* leftover bytes to remain: deleting them is impossible
    // in this fault model. Security is denial of their authority, not magic
    // physical erasure.
    expect(storage.values[_tokenKey], _bearer);
    reopened.dispose();
  });

  test('W02 F05B WEB local-only device enrollment remains distinct from bearer boot',
      () async {
    final storage = _UnwritableBrowserStorage({
      _localSessionKey: 'enrolled',
      _localDeviceKey: 'synthetic-device-f05b',
    });
    final reopened = _webService(storage);
    await reopened.initialize();

    // A genuine marker-only local enrollment is a separate device scope.
    // Its existing app-lock must still gate protected clinical content.
    expect(reopened.isAuthenticated, isTrue);
    expect(reopened.hasRemoteApiCredential, isFalse);
    expect(reopened.boundNativeAccountId, isNull);
    expect(await reopened.getIdToken(), isNull);
    expect(await reopened.resolvePatientVaultScope(), isNotNull);
    reopened.dispose();
  });
}
