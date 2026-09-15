import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/companion_service.dart';

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
