import 'dart:typed_data';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _NoBearerAuth extends AuthService {
  @override
  Future<String?> getIdToken() async =>
      throw StateError('Local decline must block before auth or network');
}

void main() {
  test('Companion text and voice never reach HTTP after local decline', () async {
    final consent = ConsentService()
      ..markVerifiedConsent()
      ..declineLocally();
    var networkCalls = 0;
    final service = CompanionService(
      authService: _NoBearerAuth(),
      consentService: consent,
      httpClient: MockClient((_) async {
        networkCalls += 1;
        throw StateError('Unexpected companion network request');
      }),
    );

    for (final action in <Future<Object?> Function()>[
      () => service.sendChatMessage('Synthetic greeting'),
      () => service.sendVoiceMessage(
            Uint8List.fromList(<int>[1, 2, 3]),
            'audio/webm',
          ),
    ]) {
      await expectLater(
        action(),
        throwsA(
          isA<ProviderApiException>().having(
            (e) => e.code,
            'code',
            'ai_declined_locally',
          ),
        ),
      );
    }

    expect(networkCalls, 0);
    service.dispose();
    consent.dispose();
  });

  test('ApiClient AI stream and media helpers deny before bearer or HTTP', () async {
    final consent = ConsentService()
      ..markVerifiedConsent()
      ..declineLocally();
    final api = ApiClient(
      authService: _NoBearerAuth(),
      consentService: consent,
      baseUrl: 'http://127.0.0.1:8000',
    );

    await expectLater(
      api.chatStream('Synthetic greeting').toList(),
      throwsA(
        isA<ProviderApiException>().having(
          (e) => e.code,
          'code',
          'ai_declined_locally',
        ),
      ),
    );
    expect(await api.sendVoiceMessage(Uint8List.fromList(<int>[1]), 'audio/mp4'), isNull);
    expect(await api.transcribeAudio(Uint8List.fromList(<int>[1]), 'audio/mp4'), isNull);
    expect(await api.analyzeMealImage(Uint8List.fromList(<int>[1])), isNull);
    expect(await api.analyzeGlucometerImage('c3ludGhldGlj', 'image/jpeg'), isNull);
    consent.dispose();
  });
}
