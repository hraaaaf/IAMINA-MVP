import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

class _SyntheticReply extends CompanionService {
  final bool urgent;
  _SyntheticReply({this.urgent = false});

  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async => CompanionChatReply(
    reply: 'Réponse synthétique — نص عربي',
    conversationId: 'synthetic-copy-selection',
    replyLanguage: 'fr',
    isEmergency: urgent,
  );

  @override
  void dispose() {}
}

void main() {
  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    for (final width in const [390.0, 768.0, 1280.0]) {
      testWidgets('decision #16 selectable replies ${locale.languageCode} ${width.toInt()}',
          (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = Size(width, 900);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);

        await tester.pumpWidget(MaterialApp(
          locale: locale,
          supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: CompanionConversationScreen(service: _SyntheticReply()),
        ));
        await tester.pumpAndSettle();
        await tester.enterText(
          find.byKey(const Key('companion-chat-input')),
          'Question de test / سؤال',
        );
        await tester.tap(find.byKey(const Key('companion-chat-send')));
        await tester.pumpAndSettle();
        final selectables = tester.widgetList<SelectableText>(
          find.descendant(
            of: find.byKey(const Key('companion-chat-message-list')),
            matching: find.byType(SelectableText),
          ),
        ).toList();
        expect(selectables.map((w) => w.data), contains('Question de test / سؤال'));
        expect(selectables.map((w) => w.data), contains('Réponse synthétique — نص عربي'));
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('urgent alert keeps readable live-region label alongside selectable text', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: CompanionConversationScreen(service: _SyntheticReply(urgent: true)),
    ));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('companion-chat-input')), 'Alerte test');
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('companion-emergency-bubble')), findsOneWidget);
    expect(find.descendant(
      of: find.byKey(const Key('companion-emergency-bubble')),
      matching: find.byType(SelectableText),
    ), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
