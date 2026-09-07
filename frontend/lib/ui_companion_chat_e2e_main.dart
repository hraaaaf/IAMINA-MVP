import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'features/companion/companion_conversation_screen.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';

class _E2EProxyAuthService extends AuthService {
  @override
  Future<String?> getIdToken() async => 'e2e-proxy';
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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
      home: CompanionConversationScreen(service: service),
    ),
  );
}
