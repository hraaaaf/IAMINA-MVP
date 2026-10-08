import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _Authenticated extends AuthService {
  @override
  Future<String?> getIdToken() async => 'synthetic-token';
}

void main() {
  Future<CompanionChatReply?> callWithMode(String? mode) async {
    final service = CompanionService(
      authService: _Authenticated(),
      httpClient: MockClient((request) async {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body.keys.toSet(), {'message', 'context_days'});
        expect(request.headers['authorization'], 'Bearer synthetic-token');
        return http.Response(
          jsonEncode({
            'reply': 'Réponse sûre.',
            'conversation_id': 'conv-synthetic',
            'reply_language': 'fr',
            if (mode != null) 'response_mode': mode,
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
      baseUrl: 'http://127.0.0.1:8000',
    );
    final reply = await service.sendChatMessage('Ma première mesure ?');
    service.dispose();
    return reply;
  }

  test('governance fallback is explicit and does not alter payload', () async {
    expect((await callWithMode('governance_fallback'))?.responseMode,
        'governance_fallback');
  });

  test('absent or unknown response mode is safely standard', () async {
    expect((await callWithMode(null))?.responseMode, 'standard');
    expect((await callWithMode('unexpected'))?.responseMode, 'standard');
  });
}
