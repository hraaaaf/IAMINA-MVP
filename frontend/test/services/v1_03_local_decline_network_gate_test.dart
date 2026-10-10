import 'dart:typed_data';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

class _NoBearerAuth extends AuthService {
  int bearerCalls = 0;

  @override
  Future<String?> getIdToken() async {
    bearerCalls += 1;
    throw StateError('Local AI gate must block before auth or network');
  }
}

void main() {
  test('Companion text and voice never reach HTTP after local decline', () async {
    final consent = ConsentService()
      ..markVerifiedConsent()
      ..declineLocally();
    var networkCalls = 0;
    final auth = _NoBearerAuth();
    final service = CompanionService(
      authService: auth,
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
    expect(auth.bearerCalls, 0);
    service.dispose();
    consent.dispose();
  });

  test('ApiClient AI stream and media helpers deny before bearer or HTTP', () async {
    final consent = ConsentService()
      ..markVerifiedConsent()
      ..declineLocally();
    final auth = _NoBearerAuth();
    final api = ApiClient(
      authService: auth,
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
    expect(await api.chatWithAmina('Synthetic greeting'), isNull);
    expect(auth.bearerCalls, 0);
    consent.dispose();
  });
  test('without verified notice, Companion patient chat and voice deny pre-network', () async {
    final consent = ConsentService()..seedInitialProfile(null);
    final auth = _NoBearerAuth();
    var networkCalls = 0;
    final service = CompanionService(
      authService: auth,
      consentService: consent,
      httpClient: MockClient((_) async {
        networkCalls += 1;
        throw StateError('No patient AI network request permitted');
      }),
    );
    for (final action in <Future<Object?> Function()>[
      () => service.sendChatMessage('Synthetic patient question'),
      () => service.sendVoiceMessage(
            Uint8List.fromList(<int>[1, 2, 3]),
            'audio/webm',
          ),
    ]) {
      await expectLater(
        action(),
        throwsA(
          isA<ProviderApiException>().having(
            (failure) => failure.code,
            'code',
            'ai_consent_unverified_locally',
          ),
        ),
      );
    }
    expect(networkCalls, 0);
    expect(auth.bearerCalls, 0);
    service.dispose();
    consent.dispose();
  });

  test('without verified notice, ApiClient patient AI denies before bearer', () async {
    final consent = ConsentService()..seedInitialProfile(null);
    final auth = _NoBearerAuth();
    final api = ApiClient(
      authService: auth,
      consentService: consent,
      baseUrl: 'http://127.0.0.1:8000',
    );
    await expectLater(
      api.chatStream('Synthetic question').toList(),
      throwsA(
        isA<ProviderApiException>().having(
          (failure) => failure.code,
          'code',
          'ai_consent_unverified_locally',
        ),
      ),
    );
    expect(await api.chatWithAmina('Synthetic question'), isNull);
    expect(await api.sendVoiceMessage(Uint8List.fromList(<int>[1]), 'audio/mp4'), isNull);
    expect(await api.transcribeAudio(Uint8List.fromList(<int>[1]), 'audio/mp4'), isNull);
    expect(await api.analyzeMealImage(Uint8List.fromList(<int>[1])), isNull);
    expect(await api.analyzeGlucometerImage('c3ludGhldGlj', 'image/jpeg'), isNull);
    expect(auth.bearerCalls, 0);
    consent.dispose();
  });

}
