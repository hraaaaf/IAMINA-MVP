import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _TokenAuthService extends AuthService {
  _TokenAuthService();

  @override
  Future<String?> getIdToken() async => 'synthetic-token';
}

class _AuditAuthService extends AuthService {
  _AuditAuthService();

  @override
  bool get isAuditSession => true;

  @override
  Future<String?> getIdToken() async =>
      throw StateError('demo responder must not request a bearer');
}

void main() {
  test('demo audit chat replies locally without backend or bearer', () async {
    var networkCalls = 0;
    final client = MockClient((request) async {
      networkCalls += 1;
      return http.Response('unexpected', 500);
    });
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: client,
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage('bonjour');

    expect(networkCalls, 0);
    expect(reply?.conversationId, 'demo-local');
    expect(reply?.replyLanguage, 'fr');
    expect(reply?.reply, contains('mode démo'));

    service.dispose();
  });

  test('demo audit chat keeps Arabic local', () async {
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: MockClient((_) async => http.Response('unexpected', 500)),
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage('مرحبا');

    expect(reply?.conversationId, 'demo-local');
    expect(reply?.replyLanguage, 'ar');
    expect(reply?.reply, contains('وضع العرض'));

    service.dispose();
  });

  test('sendChatMessage posts governed chat request and decodes reply', () async {
    late http.Request captured;
    final client = MockClient((request) async {
      captured = request;
      return http.Response(
        jsonEncode({
          'reply': 'Réponse synthétique gouvernée.',
          'conversation_id': 'conv-1',
          'timestamp': '2026-09-05T00:00:00Z',
          'is_emergency': false,
          'reply_language': 'fr',
        }),
        200,
        headers: {'content-type': 'application/json'},
      );
    });
    final service = CompanionService(
      authService: _TokenAuthService(),
      httpClient: client,
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage(
      'Dois-je augmenter ma dose ?',
      contextDays: 14,
    );

    expect(captured.method, 'POST');
    expect(captured.url.path, '/api/v1/ai/chat');
    expect(captured.headers['authorization'], 'Bearer synthetic-token');
    expect(captured.headers['content-type'], 'application/json');
    expect(jsonDecode(captured.body), {
      'message': 'Dois-je augmenter ma dose ?',
      'context_days': 14,
    });
    expect(reply?.reply, 'Réponse synthétique gouvernée.');
    expect(reply?.conversationId, 'conv-1');
    expect(reply?.replyLanguage, 'fr');

    service.dispose();
  });
}
