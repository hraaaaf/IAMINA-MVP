import 'dart:convert';

import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('SSE builder sends synthetic patient text in POST JSON, never URL', () {
    const canary = 'synthetic-private-medical-text';
    final url = Uri.parse('https://example.invalid/api/v1/ai/chat/stream');
    final request = buildChatStreamPostRequest(url, canary);
    expect(request.method, 'POST');
    expect(request.url.query, isEmpty);
    expect(request.url.toString(), isNot(contains(canary)));
    expect(request.headers['Content-Type'], 'application/json');
    expect(request.headers['Accept'], 'text/event-stream');
    expect(jsonDecode(request.body), {
      'message': canary,
      'context_days': 14,
    });
  });

  test('SSE URL with query/fragment is rejected before dispatch', () {
    expect(
      () => buildChatStreamPostRequest(
        Uri.parse('https://example.invalid/api/v1/ai/chat/stream?message=secret'),
        'synthetic',
      ),
      throwsArgumentError,
    );
  });
}
