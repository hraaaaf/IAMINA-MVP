import 'dart:ui' show SemanticsFlag;

import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

class _FailingCompanionService extends CompanionService {
  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    throw const ProviderApiException(
      code: 'provider_timeout',
      message: 'The AI service did not respond in time.',
      retryable: true,
      statusCode: 503,
    );
  }

  @override
  void dispose() {}
}

Widget _harness(Locale locale) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    home: CompanionConversationScreen(service: _FailingCompanionService()),
  );
}

void main() {
  final labels = <Locale, ({String close, String send})>{
    const Locale('fr'): (
      close: 'Fermer la conversation',
      send: 'Envoyer le message',
    ),
    const Locale('en'): (
      close: 'Close conversation',
      send: 'Send message',
    ),
    const Locale('ar'): (
      close: 'إغلاق المحادثة',
      send: 'إرسال الرسالة',
    ),
  };

  for (final entry in labels.entries) {
    testWidgets('companion controls expose ${entry.key.languageCode} semantics', (
      tester,
    ) async {
      final semantics = tester.ensureSemantics();
      addTearDown(semantics.dispose);

      await tester.pumpWidget(_harness(entry.key));
      await tester.pumpAndSettle();

      expect(find.bySemanticsLabel(entry.value.close), findsOneWidget);
      expect(find.bySemanticsLabel(entry.value.send), findsOneWidget);
    });
  }

  testWidgets('provider failure is exposed as a live semantic region', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    addTearDown(semantics.dispose);

    await tester.pumpWidget(_harness(const Locale('fr')));
    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Bonjour',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pumpAndSettle();

    const failure =
        'IAmina met trop de temps à répondre. Réessaie dans un instant.';
    final failureFinder = find.bySemanticsLabel(failure);
    expect(failureFinder, findsOneWidget);

    final node = tester.getSemantics(failureFinder);
    expect(node.flagsCollection.contains(SemanticsFlag.isLiveRegion), isTrue);
  });
}
