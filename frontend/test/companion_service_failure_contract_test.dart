import 'dart:convert';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _TokenAuthService extends AuthService {
  @override
  Future<String?> getIdToken() async => 'synthetic-token';
}

void main() {
  test('chat propagates canonical retryable provider timeout', () async {
    final service = CompanionService(
      authService: _TokenAuthService(),
      httpClient: MockClient(
        (_) async => http.Response(
          jsonEncode({
            'error': {
              'code': 'provider_timeout',
              'message': 'The AI service did not respond in time.',
              'retryable': true,
            },
          }),
          503,
        ),
      ),
      baseUrl: 'http://127.0.0.1:8000',
    );

    await expectLater(
      service.sendChatMessage('Bonjour'),
      throwsA(
        isA<ProviderApiException>()
            .having((error) => error.code, 'code', 'provider_timeout')
            .having((error) => error.retryable, 'retryable', isTrue)
            .having((error) => error.statusCode, 'statusCode', 503),
      ),
    );
    service.dispose();
  });

  test('malformed provider error body fails closed without leaking it', () async {
    final service = CompanionService(
      authService: _TokenAuthService(),
      httpClient: MockClient(
        (_) async => http.Response('vendor-secret-detail', 503),
      ),
      baseUrl: 'http://127.0.0.1:8000',
    );

    ProviderApiException? caught;
    try {
      await service.sendChatMessage('Bonjour');
    } on ProviderApiException catch (error) {
      caught = error;
    }

    expect(caught, isNotNull);
    expect(caught!.code, 'provider_unknown_failure');
    expect(caught.toString(), isNot(contains('vendor-secret-detail')));
    service.dispose();
  });
}
