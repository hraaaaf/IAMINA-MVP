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
  test('demo audit chat posts to public demo endpoint without bearer', () async {
    late http.Request captured;
    final client = MockClient((request) async {
      captured = request;
      return http.Response(
        jsonEncode({
          'reply': 'Bonjour 👋 Je suis là. Que puis-je faire pour toi ?',
          'conversation_id': 'demo-governed',
          'timestamp': '2026-09-19T00:00:00Z',
          'is_emergency': false,
          'reply_language': 'fr',
        }),
        200,
        headers: {'content-type': 'application/json'},
      );
    });
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: client,
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage('bonjour');

    expect(captured.method, 'POST');
    expect(captured.url.path, '/api/v1/demo/chat');
    expect(captured.headers['authorization'], isNull);
    expect(captured.headers['content-type'], 'application/json');
    expect(jsonDecode(captured.body), {
      'message': 'bonjour',
      'language': 'fr',
      'history': <dynamic>[],
    });
    expect(reply?.conversationId, 'demo-governed');
    expect(reply?.replyLanguage, 'fr');
    expect(reply?.reply, contains('Que puis-je faire'));

    service.dispose();
  });

  test('demo audit chat sends prior governed exchange on the next turn', () async {
    final captured = <http.Request>[];
    var call = 0;
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: MockClient((request) async {
        captured.add(request);
        call += 1;
        return http.Response(
          jsonEncode({
            'reply': call == 1
                ? 'Tu veux mieux dormir.'
                : 'Ton objectif précédent était de mieux dormir.',
            'conversation_id': 'demo-governed',
            'timestamp': '2026-09-21T00:00:00Z',
            'is_emergency': false,
            'reply_language': 'fr',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
      baseUrl: 'http://127.0.0.1:8000',
    );

    await service.sendChatMessage('Je veux mieux dormir.');
    await service.sendChatMessage('Quel était mon objectif ?');

    expect(captured, hasLength(2));
    expect(captured[1].headers['authorization'], isNull);
    expect(jsonDecode(captured[1].body), {
      'message': 'Quel était mon objectif ?',
      'language': 'fr',
      'history': [
        {'role': 'user', 'content': 'Je veux mieux dormir.'},
        {'role': 'assistant', 'content': 'Tu veux mieux dormir.'},
      ],
    });

    service.dispose();
  });

  test('demo audit chat decodes governed Arabic reply', () async {
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: MockClient(
        (_) async => http.Response(
          jsonEncode({
            'reply': 'مرحباً 👋 أنا هنا. كيف يمكنني مساعدتك؟',
            'conversation_id': 'demo-governed',
            'timestamp': '2026-09-19T00:00:00Z',
            'is_emergency': false,
            'reply_language': 'ar',
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ),
      ),
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage('مرحبا');

    expect(reply?.conversationId, 'demo-governed');
    expect(reply?.replyLanguage, 'ar');
    expect(reply?.reply, contains('مرحباً'));

    service.dispose();
  });

  test('demo audit chat falls back locally when backend is unavailable', () async {
    final service = CompanionService(
      authService: _AuditAuthService(),
      httpClient: MockClient((_) async => throw http.ClientException('offline')),
      baseUrl: 'http://127.0.0.1:8000',
    );

    final reply = await service.sendChatMessage('bonjour');

    expect(reply?.conversationId, 'demo-local');
    expect(reply?.replyLanguage, 'fr');
    expect(reply?.reply, contains('mode démo'));

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
