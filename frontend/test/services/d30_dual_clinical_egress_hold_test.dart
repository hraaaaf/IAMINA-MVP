import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D30 both protected egress routes deny before bearer lookup or HTTP',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
    });
    var authRequests = 0;
    final auth = AuthService(
      httpClient: MockClient((request) async {
        authRequests++;
        fail('Auth network must not be required for a denied clinical request');
      }),
    );
    await auth.initialize();
    expect(auth.hasRemoteApiCredential, isTrue);

    var medicalRequests = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        medicalRequests++;
        fail('Clinical data must not leave the device');
      }),
    );
    const log = <String, dynamic>{
      'client_uuid': 'synthetic',
      'blood_sugar': 120,
    };
    const profile = <String, dynamic>{'diabetes_type': 'type2'};

    expect(api.canSyncClinicalJournal, isFalse);
    expect(api.canUploadClinicalProfile, isFalse);
    expect(await api.syncLogEntry(log), isFalse);
    expect(await api.batchSyncLogs([log]), isEmpty);
    expect(await api.patchProfile(profile), isFalse);

    await expectLater(
      api.client.post<Object, Object>(
        Uri.parse('/api/v1/logs/batch'),
        body: [log],
      ),
      throwsA(isA<StateError>()),
    );
    await expectLater(
      api.client.patch<Object, Object>(
        Uri.parse('/api/v1/profile'),
        body: profile,
      ),
      throwsA(isA<StateError>()),
    );
    expect(authRequests, 0);
    expect(medicalRequests, 0);
    auth.dispose();
  });
}
