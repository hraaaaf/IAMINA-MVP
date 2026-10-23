import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final (locale, notice) in <(Locale, String)>[
    (const Locale('fr'), 'Le chat et la voix IAmina sont indisponibles dans cette version locale. Aucun message médical n’est envoyé.'),
    (const Locale('en'), 'IAmina chat and voice are unavailable in this local-only version. No medical message is sent.'),
    (const Locale('ar'), 'المحادثة والصوت في IAmina غير متاحين في هذه النسخة المحلية. لا تُرسل رسائل طبية.'),
  ]) {
    for (final width in <double>[390, 768, 1280]) {
      testWidgets('L0 release-like chat disabled ${locale.languageCode} $width', (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = Size(width, 900);
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        await tester.pumpWidget(MaterialApp(
          locale: locale,
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
          home: const CompanionConversationScreen(forceLocalOnlyDisabledForTests: true),
        ));
        await tester.pump();
        expect(find.text(notice), findsOneWidget);
        expect(find.byKey(const Key('companion-local-only-emergency-notice')), findsOneWidget);
        expect(find.byKey(const Key('companion-chat-send')), findsNothing);
        expect(find.byKey(const Key('companion-chat-input')), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
