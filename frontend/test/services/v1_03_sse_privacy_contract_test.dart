import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('patient SSE uses POST JSON body without PHI-bearing query', () {
    final content = File('lib/services/api_client.dart').readAsStringSync();
    final stream = content.substring(
      content.indexOf('Stream<String> chatStream(String message)'),
    );
    final request = stream.substring(0, stream.indexOf('final client = http.Client();'));
    expect(request, contains("http.Request('POST', uri)"));
    expect(request, contains("'Content-Type'] = 'application/json'"));
    expect(request, contains("'message': message"));
    expect(request, isNot(contains("queryParameters: {'message'")));
    expect(request, isNot(contains("http.Request('GET'")));
  });
}
