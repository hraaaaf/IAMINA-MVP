import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D30 device-only session refuses journal upload without remote token',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected authentication network request');
      }),
    );
    await auth.initialize();
    await auth.enrollLocalDevice();
    expect(auth.isAuthenticated, isTrue);
    expect(await auth.getIdToken(), isNull);

    final api = ApiClient(
      baseUrl: 'http://127.0.0.1:1',
      authService: auth,
    );
    final entry = <String, dynamic>{
      'client_uuid': 'synthetic-d30',
      'blood_sugar': 120,
    };
    expect(await api.syncLogEntry(entry), isFalse);
    expect(await api.batchSyncLogs([entry]), isEmpty);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();
  });
}
