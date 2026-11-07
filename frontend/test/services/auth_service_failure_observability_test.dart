import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mocktail/mocktail.dart';
import 'package:amina/services/auth_service.dart';

class _MockSecureStorage extends Mock implements FlutterSecureStorage {}
class _MockHttpClient extends Mock implements http.Client {}

void main() {
  late _MockSecureStorage storage;
  late _MockHttpClient httpClient;
  late List<String> failures;

  setUpAll(() {
    registerFallbackValue(Uri());
    registerFallbackValue(<String, String>{});
  });

  setUp(() {
    storage = _MockSecureStorage();
    httpClient = _MockHttpClient();
    failures = <String>[];
  });

  AuthService buildService() {
    return AuthService(
      storage: storage,
      httpClient: httpClient,
      failureLogger: (operation, errorType, stackTrace) {
        failures.add('$operation:$errorType');
      },
    );
  }

  test('initialize logs secure-storage failure and stays fail-closed', () async {
    when(() => storage.read(key: any(named: 'key'))).thenThrow(
      StateError('synthetic-sensitive-token'),
    );

    final service = buildService();
    await service.initialize();

    expect(service.isInitialized, isTrue);
    expect(service.isAuthenticated, isFalse);
    expect(failures, <String>['initialize:StateError']);
    expect(failures.single, isNot(contains('synthetic-sensitive-token')));

    service.dispose();
  });

  test('legacy native token boot stays local and performs no remote validation', () async {
    const token = 'iamina.e30:1abcde:synthetic_secret_token';
    when(() => storage.read(key: any(named: 'key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String?;
      if (key == 'iamina_native_access_token') return token;
      return null;
    });
    when(
      () => storage.write(
        key: any(named: 'key'),
        value: any(named: 'value'),
      ),
    ).thenAnswer((_) async {});

    final service = buildService();
    await service.initialize();

    expect(service.isInitialized, isTrue);
    expect(service.isAuthenticated, isTrue);
    expect(failures, isEmpty);
    verifyNever(() => httpClient.get(any(), headers: any(named: 'headers')));

    service.dispose();
  });

  test('logout transport failure is observable but local logout completes', () async {
    const token = 'iamina.e30:1abcde:synthetic_secret_token';
    // Exercise the independent network-failure contract against a faithful
    // stateful storage double: a successful delete must make a later read
    // return null. A mock that always returns the old token would falsely
    // simulate the separate F05B-SILENT security fault.
    final stored = <String, String>{
      'iamina_native_access_token': token,
    };
    when(() => storage.read(key: any(named: 'key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      return stored[key];
    });
    when(
      () => storage.write(
        key: any(named: 'key'),
        value: any(named: 'value'),
      ),
    ).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      final value = invocation.namedArguments[#value] as String;
      stored[key] = value;
    });
    when(() => storage.delete(key: any(named: 'key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      stored.remove(key);
    });
    when(
      () => httpClient.post(
        any(),
        headers: any(named: 'headers'),
      ),
    ).thenThrow(StateError('logout carried synthetic-secret-token'));

    final service = buildService();
    await service.initialize();
    expect(service.isAuthenticated, isTrue);

    await service.signOut();

    expect(service.isAuthenticated, isFalse);
    expect(stored.containsKey('iamina_native_access_token'), isFalse);
    expect(stored.containsKey('iamina_auth_logout_pending_v1'), isFalse);
    expect(failures, <String>['logout:StateError']);
    expect(failures.single, isNot(contains(token)));
    expect(failures.single, isNot(contains('synthetic-secret-token')));

    service.dispose();
  });
}
