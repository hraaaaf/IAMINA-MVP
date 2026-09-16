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

  test('token validation transport failure is observable and remains invalid', () async {
    const token = 'iamina.synthetic-secret-token';
    when(() => storage.read(key: any(named: 'key'))).thenAnswer(
      (_) async => token,
    );
    when(() => storage.delete(key: any(named: 'key'))).thenAnswer(
      (_) async {},
    );
    when(
      () => httpClient.get(
        any(),
        headers: any(named: 'headers'),
      ),
    ).thenThrow(StateError('transport carried synthetic-secret-token'));

    final service = buildService();
    await service.initialize();

    expect(service.isInitialized, isTrue);
    expect(service.isAuthenticated, isFalse);
    expect(failures, <String>['validate_native_token:StateError']);
    expect(failures.single, isNot(contains(token)));
    verify(() => storage.delete(key: any(named: 'key'))).called(1);

    service.dispose();
  });

  test('logout transport failure is observable but local logout completes', () async {
    const token = 'iamina.synthetic-secret-token';
    when(() => storage.read(key: any(named: 'key'))).thenAnswer(
      (_) async => token,
    );
    when(() => storage.delete(key: any(named: 'key'))).thenAnswer(
      (_) async {},
    );
    when(
      () => httpClient.get(
        any(),
        headers: any(named: 'headers'),
      ),
    ).thenAnswer((_) async => http.Response('{}', 200));
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
    verify(() => storage.delete(key: any(named: 'key'))).called(1);

    service.dispose();
  });
}
