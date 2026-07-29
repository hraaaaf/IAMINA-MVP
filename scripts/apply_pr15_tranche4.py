from pathlib import Path

api_path = Path("frontend/lib/services/api_client.dart")
api = api_path.read_text()

anchor = "class AuthInterceptor implements Interceptor {"
provider_error = r'''class ProviderApiException implements Exception {
  final String code;
  final String message;
  final bool retryable;
  final int statusCode;

  const ProviderApiException({
    required this.code,
    required this.message,
    required this.retryable,
    required this.statusCode,
  });

  factory ProviderApiException.fromJson(
    Map<String, dynamic> payload, {
    required int statusCode,
  }) {
    final error = payload['error'];
    if (error is! Map<String, dynamic>) {
      return ProviderApiException.unknown(statusCode: statusCode);
    }
    return ProviderApiException(
      code: error['code'] as String? ?? 'provider_unknown_failure',
      message: error['message'] as String? ?? 'The AI request could not be completed safely.',
      retryable: error['retryable'] as bool? ?? false,
      statusCode: statusCode,
    );
  }

  factory ProviderApiException.unknown({required int statusCode}) {
    return ProviderApiException(
      code: 'provider_unknown_failure',
      message: 'The AI request could not be completed safely.',
      retryable: false,
      statusCode: statusCode,
    );
  }

  String get userMessage {
    switch (code) {
      case 'provider_timeout':
      case 'provider_unavailable':
        return 'Le service IA est temporairement indisponible. Réessaie dans quelques instants.';
      case 'provider_quota_exceeded':
        return 'Le service IA est temporairement saturé. Réessaie plus tard.';
      case 'provider_malformed_response':
      case 'provider_internal_failure':
        return 'La réponse IA n’a pas pu être traitée en toute sécurité.';
      default:
        return retryable
            ? 'Le service IA est momentanément indisponible. Réessaie dans quelques instants.'
            : 'La demande IA n’a pas pu être traitée en toute sécurité.';
    }
  }

  @override
  String toString() => 'ProviderApiException(code: $code, retryable: $retryable)';
}

'''
if "class ProviderApiException" not in api:
    api = api.replace(anchor, provider_error + anchor)

old_stream = r'''  /// Streaming SSE chat — yields token strings as they arrive.
  Stream<String> chatStream(String message) async* {
    final token = await _authService.getIdToken();
    final uri = Uri.parse('$baseUrl/api/v1/ai/chat/stream')
        .replace(queryParameters: {'message': message});

    final request = http.Request('GET', uri);
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    try {
      final client = http.Client();
      final streamed = await client.send(request);

      String buffer = '';
      await for (final chunk in streamed.stream.transform(utf8.decoder)) {
        buffer += chunk;
        final lines = buffer.split('\n');
        buffer = lines.removeLast(); // last may be incomplete
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final payload = line.substring(6).trim();
            if (payload == '[DONE]') {
              client.close();
              return;
            }
            try {
              final json = jsonDecode(payload) as Map<String, dynamic>;
              final tok = json['token'] as String?;
              if (tok != null) yield tok;
            } catch (_) {}
          }
        }
      }
      client.close();
    } catch (_) {
      yield 'Une erreur est survenue.';
    }
  }
'''
new_stream = r'''  /// Streaming SSE chat — yields token strings as they arrive.
  Stream<String> chatStream(String message) async* {
    final token = await _authService.getIdToken();
    final uri = Uri.parse('$baseUrl/api/v1/ai/chat/stream')
        .replace(queryParameters: {'message': message});

    final request = http.Request('GET', uri);
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    final client = http.Client();
    try {
      final streamed = await client
          .send(request)
          .timeout(TimeoutInterceptor._kTimeout);

      if (streamed.statusCode < 200 || streamed.statusCode >= 300) {
        final body = await streamed.stream.bytesToString();
        try {
          final payload = jsonDecode(body) as Map<String, dynamic>;
          throw ProviderApiException.fromJson(
            payload,
            statusCode: streamed.statusCode,
          );
        } on ProviderApiException {
          rethrow;
        } catch (_) {
          throw ProviderApiException.unknown(statusCode: streamed.statusCode);
        }
      }

      String buffer = '';
      await for (final chunk in streamed.stream.transform(utf8.decoder)) {
        buffer += chunk;
        final lines = buffer.split('\n');
        buffer = lines.removeLast(); // last may be incomplete
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final payload = line.substring(6).trim();
            if (payload == '[DONE]') return;
            try {
              final json = jsonDecode(payload) as Map<String, dynamic>;
              final tok = json['token'] as String?;
              if (tok != null) yield tok;
            } catch (_) {}
          }
        }
      }
    } on TimeoutException {
      throw const ProviderApiException(
        code: 'provider_timeout',
        message: 'The AI service did not respond in time.',
        retryable: true,
        statusCode: 503,
      );
    } on ProviderApiException {
      rethrow;
    } catch (_) {
      throw const ProviderApiException(
        code: 'provider_unavailable',
        message: 'The AI service is temporarily unavailable.',
        retryable: true,
        statusCode: 503,
      );
    } finally {
      client.close();
    }
  }
'''
if old_stream not in api:
    raise SystemExit("chatStream anchor not found")
api = api.replace(old_stream, new_stream)
api_path.write_text(api)

chat_path = Path("frontend/lib/features/journal/widgets/amina_chat_view.dart")
chat = chat_path.read_text()
old_error = r'''      onError: (_) {
        if (!mounted) return;
        setState(() {
          _messages[aiMsgIndex] = {'isAi': true, 'text': 'Une erreur est survenue. Veuillez réessayer.', 'isEmergency': false};
          _isTyping = false;
        });
      },
'''
new_error = r'''      onError: (error) {
        if (!mounted) return;
        final message = error is ProviderApiException
            ? error.userMessage
            : 'La demande n’a pas pu être traitée en toute sécurité.';
        setState(() {
          _messages[aiMsgIndex] = {
            'isAi': true,
            'text': message,
            'isEmergency': false,
            'retryable': error is ProviderApiException && error.retryable,
          };
          _isTyping = false;
        });
      },
'''
if old_error not in chat:
    raise SystemExit("chat onError anchor not found")
chat = chat.replace(old_error, new_error)
chat_path.write_text(chat)

test_path = Path("frontend/test/services/provider_api_error_test.dart")
test_path.write_text(r'''import 'package:flutter_test/flutter_test.dart';
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
''')
