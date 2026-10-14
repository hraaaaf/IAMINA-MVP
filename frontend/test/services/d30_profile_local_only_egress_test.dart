import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

const _syntheticProfilePatch = <String, dynamic>{
  'ramadan_start_date': '2026-02-18',
  'ramadan_end_date': '2026-03-19',
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  for (final seededBearer in [false, true]) {
    test(
      'D30 profile local-only hold prevents PATCH with remote bearer: '
      '$seededBearer',
      () async {
        FlutterSecureStorage.setMockInitialValues({
          if (seededBearer)
            'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
        });
        var authenticationRequests = 0;
        final auth = AuthService(
          httpClient: MockClient((request) async {
            authenticationRequests++;
            fail('Profile hold must not trigger remote authentication');
          }),
        );
        await auth.initialize();
        if (!seededBearer) await auth.enrollLocalDevice();
        expect(auth.hasRemoteApiCredential, seededBearer);

        var profileRequests = 0;
        final api = ApiClient(
          baseUrl: 'https://synthetic.example',
          authService: auth,
          httpClient: MockClient((request) async {
            profileRequests++;
            fail('Clinical profile payload must remain on device');
          }),
        );

        expect(api.canUploadClinicalProfile, isFalse);
        expect(await api.patchProfile(_syntheticProfilePatch), isFalse);
        await expectLater(
          api.client.patch<Object, Object>(
            Uri.parse('/api/v1/profile'),
            body: _syntheticProfilePatch,
          ),
          throwsA(isA<StateError>()),
        );

        expect(profileRequests, 0);
        expect(authenticationRequests, 0);
        auth.dispose();
      },
    );
  }

  test('D30 profile hold never alters local data passed by caller', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected authentication request');
      }),
    );
    await auth.initialize();

    final api = ApiClient(
      authService: auth,
      httpClient: MockClient((request) async {
        fail('Unexpected profile HTTP dispatch');
      }),
    );
    final patch = Map<String, dynamic>.from(_syntheticProfilePatch);
    expect(await api.patchProfile(patch), isFalse);
    expect(patch, _syntheticProfilePatch);
    auth.dispose();
  });
}
