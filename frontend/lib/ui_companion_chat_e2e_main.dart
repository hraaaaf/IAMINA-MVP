import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'features/companion/companion_conversation_screen.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';

class _E2EProxyAuthService extends AuthService {
  @override
  Future<String?> getIdToken() async => 'e2e-proxy';
}

/// Synthetic visual proof only. Never connected to real patient services.
class _SyntheticP1FallbackService extends CompanionService {
  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async => const CompanionChatReply(
    reply: 'Réponse locale limitée.',
    conversationId: 'synthetic-p1-proof',
    replyLanguage: 'fr',
    responseMode: 'governance_fallback',
  );
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final isP1Proof = Uri.base.queryParameters['p1-proof'] == '1';
  final service = CompanionService(
    authService: _E2EProxyAuthService(),
    baseUrl: companionApiBaseUrl,
  );

  runApp(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      locale: const Locale('fr'),
      supportedLocales: const [Locale('fr')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(useMaterial3: true, fontFamily: 'Inter'),
      home: CompanionConversationScreen(
        service: isP1Proof ? _SyntheticP1FallbackService() : service,
        latestLocalReading: isP1Proof ? () async => 128.0 : null,
      ),
    ),
  );
}
