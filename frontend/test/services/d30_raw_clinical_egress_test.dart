import 'dart:io';
import 'dart:typed_data';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D30 raw clinical transport requires nonempty bearer', () {
    expect(hasBearerForDirectClinicalTransport(null), isFalse);
    expect(hasBearerForDirectClinicalTransport(''), isFalse);
    expect(hasBearerForDirectClinicalTransport('synthetic-bearer'), isTrue);
  });

  test('D30 local-only cannot create HTTP transport for raw PHI media/stream',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    var authHttpCalls = 0;
    final auth = AuthService(
      httpClient: MockClient((request) async {
        authHttpCalls++;
        fail('Authentication must not contact server for local-only media');
      }),
    );
    await auth.initialize();
    await auth.enrollLocalDevice();
    expect(await auth.getIdToken(), isNull);
    final api = ApiClient(
      baseUrl: 'http://127.0.0.1:1',
      authService: auth,
    );

    var createdHttpClients = 0;
    await HttpOverrides.runZoned(
      () async {
        // A streamed chat previously embedded clinical text in a GET URL,
        // even when no bearer existed.
        expect(
          await api.chatStream('synthetic confidential glucose note').toList(),
          isEmpty,
        );
        expect(
          await api.sendVoiceMessage(
            Uint8List.fromList([1, 2, 3]),
            'audio/wav',
          ),
          isNull,
        );
        expect(
          await api.analyzeGlucometerImage(
            'c3ludGhldGlj',
            'image/jpeg',
          ),
          isNull,
        );
        expect(
          await api.transcribeAudio(
            Uint8List.fromList([4, 5, 6]),
            'audio/wav',
          ),
          isNull,
        );
      },
      createHttpClient: (context) {
        createdHttpClients++;
        throw StateError('D30 attempted clinical network egress');
      },
    );

    expect(createdHttpClients, 0);
    expect(authHttpCalls, 0);
    auth.dispose();
  });
}
