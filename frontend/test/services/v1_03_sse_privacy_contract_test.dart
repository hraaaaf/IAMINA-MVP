import 'dart:convert';
import 'dart:io';

import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('actual SSE request puts synthetic patient data only into JSON', () {
    const secret = 'SYNTHETIC_PRIVATE_DIABETES_175_MGDL';
    final request = buildPatientSseRequest('https://example.invalid', secret);
    expect(request.method, 'POST');
    expect(request.url.path, '/api/v1/ai/chat/stream');
    expect(request.url.query, isEmpty);
    expect(request.url.toString(), isNot(contains(secret)));
    expect(request.headers['Content-Type'], 'application/json');
    expect(request.headers['Accept'], 'text/event-stream');
    final parsed = jsonDecode(request.body) as Map<String, dynamic>;
    expect(parsed['message'], secret);
    expect(parsed['context_days'], 14);
  });

  test('chatStream uses tested request builder rather than GET query', () {
    final content = File('lib/services/api_client.dart').readAsStringSync();
    final part = content.substring(
      content.indexOf('Stream<String> chatStream(String message)'),
    );
    final request = part.substring(0, part.indexOf('final client = http.Client();'));
    expect(request, contains('buildPatientSseRequest(baseUrl, message)'));
    expect(request, isNot(contains('queryParameters:')));
    expect(request, isNot(contains("http.Request('GET'")));
  });
}
