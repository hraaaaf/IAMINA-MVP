import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/api_client.dart';

void main() {
  test('retryable timeout maps to deterministic temporary-unavailable UX', () {
    final error = ProviderApiException.fromJson(
      {
        'error': {
          'code': 'provider_timeout',
          'message': 'The AI service did not respond in time.',
          'retryable': true,
        },
      },
      statusCode: 503,
    );

    expect(error.retryable, isTrue);
    expect(error.statusCode, 503);
    expect(error.userMessage, contains('Réessaie dans quelques instants'));
    expect(error.toString(), isNot(contains('The AI service')));
  });

  test('non-retryable internal failure maps to safe terminal UX', () {
    final error = ProviderApiException.fromJson(
      {
        'error': {
          'code': 'provider_internal_failure',
          'message': 'The AI request could not be completed safely.',
          'retryable': false,
        },
      },
      statusCode: 500,
    );

    expect(error.retryable, isFalse);
    expect(error.userMessage, contains('en toute sécurité'));
  });

  test('malformed error payload fails closed', () {
    final error = ProviderApiException.fromJson(
      {'unexpected': 'vendor detail'},
      statusCode: 502,
    );

    expect(error.code, 'provider_unknown_failure');
    expect(error.retryable, isFalse);
    expect(error.userMessage, isNot(contains('vendor detail')));
  });
}
