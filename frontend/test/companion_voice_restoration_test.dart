import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/companion_service.dart';

class _IdleCompanionService extends CompanionService {
  @override
  void dispose() {}
}

class _EmergencyCompanionService extends CompanionService {
  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    return const CompanionChatReply(
      reply: 'Appelle immédiatement les services d’urgence.',
      conversationId: 'emergency-test',
      replyLanguage: 'fr',
      isEmergency: true,
    );
  }

  @override
  void dispose() {}
}


Widget _harness() => MaterialApp(
  locale: const Locale('fr'),
  supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
  localizationsDelegates: const [
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  home: CompanionConversationScreen(service: _IdleCompanionService()),
);

void main() {
  final cases = <(double, double)>[
    (390, 844),
    (768, 1024),
    (1280, 900),
  ];

  for (final (width, height) in cases) {
    testWidgets(
      'canonical companion exposes voice control at ' +
          width.toInt().toString() +
          'x' +
          height.toInt().toString(),
      (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = Size(width, height);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);

        final semantics = tester.ensureSemantics();

        await tester.pumpWidget(_harness());
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('companion-chat-voice')), findsOneWidget);
        expect(find.byIcon(Icons.mic_rounded), findsOneWidget);
        expect(
          find.bySemanticsLabel('Envoyer un message vocal'),
          findsOneWidget,
        );
        expect(find.byKey(const Key('companion-chat-input')), findsOneWidget);
        expect(find.byKey(const Key('companion-chat-send')), findsOneWidget);
        expect(tester.takeException(), isNull);
        semantics.dispose();
      },
    );
  }

  testWidgets('emergency reply keeps prominent live-region rendering', (tester) async {
    final semantics = tester.ensureSemantics();

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: CompanionConversationScreen(
          service: _EmergencyCompanionService(),
        ),
      ),
    );

    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Je me sens très mal.',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('companion-emergency-bubble')),
      findsOneWidget,
    );
    expect(
      find.bySemanticsLabel(
        'Alerte urgente IAmina. Appelle immédiatement les services d’urgence.',
      ),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('companion-assistant-bubble')),
      findsNothing,
    );
    semantics.dispose();
  });

}
