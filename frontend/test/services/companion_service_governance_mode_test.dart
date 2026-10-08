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

  test('old certified FR fallback without response_mode is labelled', () {
    final reply = CompanionChatReply.fromJson({
      'reply': 'Je peux continuer avec les fonctions locales d’IAMINA. Demande-moi une donnée précise enregistrée — '
          'glycémie, repas, sommeil, stress, traitement enregistré, CGM ou documents — '
          'ou demande-moi ce que je sais faire.',
      'reply_language': 'fr',
    });
    expect(reply.responseMode, 'governance_fallback');
  });

  test('legacy EN, AR and Darija fallback replies are labelled', () {
    const legacyReplies = [
      "I can keep helping with IAmina's local functions. Ask me for a specific recorded item — "
          'glucose, meals, sleep, stress, recorded treatment, CGM or documents — '
          'or ask what I can do.',
      'نقدر نكمل معك بوظائف IAmina المحلية. اسألني عن معلومة محددة ومسجلة مثل السكر، الوجبات، '
          'النوم، التوتر، العلاج المسجل، CGM أو الوثائق، أو اسألني ماذا أستطيع أن أفعل.',
      'N9der nkemmel m3ak b fonctions locales dyal IAmina. Sowlni 3la data m7edda msjla — '
          'sucre, makla, n3as, stress, traitement msjjel, CGM wela documents — '
          'wela sowlni chno n9der ndir.',
    ];
    for (final legacy in legacyReplies) {
      expect(CompanionChatReply.fromJson({'reply': legacy}).responseMode,
          'governance_fallback');
    }
  });

  test('unknown copy and explicit server metadata cannot be overridden', () {
    const legacy = 'Je peux continuer avec les fonctions locales d’IAMINA.';
    expect(CompanionChatReply.fromJson({'reply': legacy}).responseMode,
        'standard');
    const exact = 'Je peux continuer avec les fonctions locales d’IAMINA. Demande-moi une donnée précise enregistrée — '
        'glycémie, repas, sommeil, stress, traitement enregistré, CGM ou documents — '
        'ou demande-moi ce que je sais faire.';
    expect(CompanionChatReply.fromJson({
      'reply': exact,
      'response_mode': 'standard',
    }).responseMode, 'standard');
  });
}
