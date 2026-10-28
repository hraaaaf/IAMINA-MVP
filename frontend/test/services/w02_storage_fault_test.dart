import 'dart:convert';
import 'package:amina/services/auth_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _a = 'iamina.eyJhIjoxfQ:1abcde:sig_a';
const _token = 'iamina_native_access_token';
const _binding = 'iamina_native_account_binding_v1';
const _marker = 'iamina_web_session_revoked_v1';

class FailStorage extends FlutterSecureStorage {
  FailStorage(this.data);
  final Map<String, String> data;
  bool failMarkerWrite = false;
  bool failTokenDelete = false;

  @override
  Future<String?> read({
    required String key,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async => data[key];

  @override
  Future<void> write({
    required String key,
    required String? value,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (key == _marker && failMarkerWrite) {
      throw StateError('Synthetic marker WRITE failure');
    }
    if (value == null) {
      data.remove(key);
    } else {
      data[key] = value;
    }
  }

  @override
  Future<void> delete({
    required String key,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (key == _token && failTokenDelete) {
      throw StateError('Synthetic bearer DELETE failure');
    }
    data.remove(key);
  }
}

Map<String, String> _oldA() => {
  _token: _a,
  _binding: jsonEncode({'token': _a, 'user_id': 734}),
  'iamina_local_session_v1': 'enrolled',
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'W02 marker write fails AND token delete would fail: Web reload refuses A',
    () async {
      final storage = FailStorage(_oldA());
      final active = AuthService(storage: storage);
      addTearDown(active.dispose);
      await active.initialize();
      storage.failMarkerWrite = true;
      storage.failTokenDelete = true;
      await expectLater(active.signOut(), throwsStateError);
      expect(storage.data[_token], _a);
      expect(storage.data.containsKey(_marker), false);
      final reloaded = AuthService(storage: storage);
      addTearDown(reloaded.dispose);
      await reloaded.initialize();
      if (kIsWeb) {
        expect(reloaded.isAuthenticated, isFalse);
        expect(reloaded.boundNativeAccountId, isNull);
        expect(await reloaded.resolvePatientVaultScope(), isNull);
        expect(await reloaded.getIdToken(), isNull);
      }
    },
  );

  test(
    'W02 marker persisted and token deletion fails: restart rejects A',
    () async {
      final storage = FailStorage(_oldA());
      final active = AuthService(storage: storage);
      addTearDown(active.dispose);
      await active.initialize();
      storage.failTokenDelete = true;
      await expectLater(active.signOut(), throwsStateError);
      expect(storage.data[_marker], 'revoked');
      expect(storage.data[_token], _a);
      final reloaded = AuthService(storage: storage);
      addTearDown(reloaded.dispose);
      await reloaded.initialize();
      expect(reloaded.isAuthenticated, false);
      expect(reloaded.hasRemoteApiCredential, false);
      expect(await reloaded.resolvePatientVaultScope(), null);
    },
  );

  test('W02 two open Web tabs: A egress must stop after B switches', () async {
    final shared = FailStorage({});
    final first = AuthService(
      storage: shared,
      httpClient: MockClient(
        (request) async => http.Response(
          '{"access_token":"iamina.eyJhIjoxfQ:1abcde:sig_a","user":{"id":734}}',
          200,
        ),
      ),
    );
    final second = AuthService(
      storage: shared,
      httpClient: MockClient(
        (request) async => http.Response(
          '{"access_token":"iamina.eyJiIjoyfQ:1abcdf:sig_b","user":{"id":812}}',
          200,
        ),
      ),
    );
    addTearDown(first.dispose);
    addTearDown(second.dispose);
    await first.initialize();
    await second.initialize();
    await first.signInWithEmail('a@example.invalid', 'synthetic');
    expect(await first.getIdToken(), _a);
    await second.signInWithEmail('b@example.invalid', 'synthetic');
    if (kIsWeb) {
      expect(
        await first.getIdToken(),
        isNull,
        reason: 'Tab A must not keep egress after tab B replaces stored owner',
      );
      expect(await first.resolvePatientVaultScope(), isNull);
    }
  });

  test(
    'W02 tombstone WRITE fails: independent credential DELETE still attempted',
    () async {
      final storage = FailStorage(_oldA());
      final active = AuthService(storage: storage);
      addTearDown(active.dispose);
      await active.initialize();
      storage.failMarkerWrite = true;
      await expectLater(active.signOut(), throwsStateError);
      expect(storage.data.containsKey(_token), isFalse);
      expect(storage.data.containsKey(_binding), isFalse);
      expect(storage.data.containsKey('iamina_local_session_v1'), isFalse);
      final reloaded = AuthService(storage: storage);
      addTearDown(reloaded.dispose);
      await reloaded.initialize();
      expect(reloaded.hasRemoteApiCredential, isFalse);
      expect(reloaded.isAuthenticated, isFalse);
    },
  );
}
