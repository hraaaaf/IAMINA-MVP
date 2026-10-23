import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/companion_service.dart';

class _DelayedCompanionService extends CompanionService {
  final Completer<CompanionChatReply?> completer = Completer<CompanionChatReply?>();

  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) => completer.future;

  @override
  void dispose() {}
}

class _FailingCompanionService extends CompanionService {
  final ProviderApiException failure;

  _FailingCompanionService(this.failure);

  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    throw failure;
  }

  @override
  void dispose() {}
}

Widget _harness(
  ProviderApiException failure, {
  Locale locale = const Locale('fr'),
}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    home: CompanionConversationScreen(
      service: _FailingCompanionService(failure),
    ),
  );
}

Future<void> _submit(WidgetTester tester) async {
  await tester.enterText(
    find.byKey(const Key('companion-chat-input')),
    'Bonjour',
  );
  await tester.tap(find.byKey(const Key('companion-chat-send')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('composer retains focus while waiting and after reply', (tester) async {
    final service = _DelayedCompanionService();
    await tester.pumpWidget(
      MaterialApp(
        home: CompanionConversationScreen(service: service),
      ),
    );

    final input = find.byKey(const Key('companion-chat-input'));
    await tester.tap(input);
    await tester.enterText(input, 'Salut');
    expect(tester.widget<TextField>(input).focusNode?.hasPrimaryFocus, isTrue);

    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pump();
    expect(tester.widget<TextField>(input).focusNode?.hasPrimaryFocus, isTrue);

    service.completer.complete(
      const CompanionChatReply(
        reply: 'Bonjour 👋',
        conversationId: 'conv-test',
        replyLanguage: 'fr',
      ),
    );
    await tester.pumpAndSettle();

    expect(tester.widget<TextField>(input).focusNode?.hasPrimaryFocus, isTrue);
    expect(find.text('Bonjour 👋'), findsOneWidget);
  });

  for (final width in <double>[390, 768, 1280]) {
    testWidgets('timeout failure stays readable at ${width.toInt()}px', (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 900);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        _harness(
          const ProviderApiException(
            code: 'provider_timeout',
            message: 'The AI service did not respond in time.',
            retryable: true,
            statusCode: 503,
          ),
        ),
      );
      await _submit(tester);

      expect(find.byKey(const Key('companion-chat-failure')), findsOneWidget);
      expect(
        find.text('IAmina met trop de temps à répondre. Réessaie dans un instant.'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }

  final localOnlyCopy = <(Locale, String)>[
    (const Locale('fr'), 'Vos données restent sur cet appareil. Le chat et la voix via serveur sont désactivés dans cette version.'),
    (const Locale('en'), 'Your data stays on this device. Server-based chat and voice are disabled in this version.'),
    (const Locale('ar'), 'تبقى بياناتك على هذا الجهاز. المحادثة والصوت عبر الخادم معطّلان في هذا الإصدار.'),
  ];

  for (final (locale, copy) in localOnlyCopy) {
    for (final width in <double>[390, 768, 1280]) {
      testWidgets('local-only notice is truthful at ${width.toInt()}px / ${locale.languageCode}', (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = Size(width, 900);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);
        await tester.pumpWidget(
          _harness(
            const ProviderApiException(
              code: 'clinical_transport_disabled_local_only',
              message: 'Remote companion service disabled',
              retryable: false,
              statusCode: 403,
            ),
            locale: locale,
          ),
        );
        await _submit(tester);
        expect(find.byKey(const Key('companion-chat-failure')), findsOneWidget);
        expect(find.text(copy), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('quota failure uses distinct English copy', (tester) async {
    await tester.pumpWidget(
      _harness(
        const ProviderApiException(
          code: 'provider_quota_exceeded',
          message: 'The AI service quota is currently exhausted.',
          retryable: false,
          statusCode: 429,
        ),
        locale: const Locale('en'),
      ),
    );
    await _submit(tester);

    expect(
      find.text('IAmina has reached its temporary limit. Try again later.'),
      findsOneWidget,
    );
  });
}
