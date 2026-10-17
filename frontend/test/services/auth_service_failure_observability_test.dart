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
    when(() => storage.delete(key: any(named: 'key'))).thenAnswer((_) async {});
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
    expect(failures, <String>['logout:StateError']);
    expect(failures.single, isNot(contains(token)));
    expect(failures.single, isNot(contains('synthetic-secret-token')));

    service.dispose();
  });

  test('non-2xx remote logout is observable but local bearer stays erased',
      () async {
    const token = 'iamina.e30:1abcde:synthetic_secret_token';
    when(() => storage.read(key: any(named: 'key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String?;
      if (key == 'iamina_native_access_token') return token;
      return null;
    });
    when(() => storage.delete(key: any(named: 'key'))).thenAnswer((_) async {});
    when(() => httpClient.post(any(), headers: any(named: 'headers')))
        .thenAnswer((invocation) async {
      final uri = invocation.positionalArguments.first as Uri;
      final headers = invocation.namedArguments[#headers] as Map<String, String>;
      expect(uri.path, '/api/v1/auth/logout');
      expect(headers['Authorization'], 'Bearer $token');
      // Synthetic API denial: the token must not be assumed revoked remotely.
      return http.Response('synthetic-private-upstream-response', 503);
    });

    final service = buildService();
    await service.initialize();
    expect(service.hasRemoteApiCredential, isTrue);

    await service.signOut();

    expect(service.isAuthenticated, isFalse);
    expect(service.hasRemoteApiCredential, isFalse);
    expect(await service.getIdToken(), isNull);
    expect(failures, <String>['logout:StateError']);
    expect(failures.single, isNot(contains(token)));
    expect(failures.single, isNot(contains('synthetic-private')));
    verify(() => storage.delete(key: 'iamina_native_access_token')).called(1);
    service.dispose();
  });
}
