import 'package:amina/data/models/companion_models.dart';
import 'package:amina/features/companion/companion_premium_screen.dart';
import 'package:amina/services/companion_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _UnavailableOverview extends CompanionService {
  int attempts = 0;

  @override
  Future<CompanionOverview?> fetchOverview() async {
    attempts++;
    return null;
  }

  @override
  void dispose() {}
}

Widget _harness(_UnavailableOverview service, Locale locale) {
  final router = GoRouter(
    initialLocation: '/companion',
    routes: [
      GoRoute(
        path: '/companion',
        builder: (_, __) => CompanionPremiumScreen(service: service),
      ),
      GoRoute(
        path: '/companion/chat',
        builder: (_, __) => const Scaffold(
          body: Center(child: Text('Companion chat route reached')),
        ),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (_, __) => const Scaffold(body: Text('Dashboard route')),
      ),
    ],
  );
  return MaterialApp.router(
    locale: locale,
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    routerConfig: router,
  );
}

void main() {
  testWidgets('390x844 unavailable overview keeps honesty and opens chat', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final service = _UnavailableOverview();

    await tester.pumpWidget(_harness(service, const Locale('fr')));
    await tester.pumpAndSettle();

    expect(service.attempts, 1);
    expect(find.text('Données indisponibles'), findsOneWidget);
    expect(find.textContaining('Aucune interprétation n’est inventée'), findsOneWidget);
    expect(find.textContaining('les réponses peuvent rester limitées'), findsOneWidget);
    expect(find.byKey(const Key('companion-overview-chat-action')), findsOneWidget);
    expect(find.byKey(const Key('companion-overview-retry-action')), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.ensureVisible(find.byKey(const Key('companion-overview-chat-action')));
    await tester.tap(find.byKey(const Key('companion-overview-chat-action')));
    await tester.pumpAndSettle();
    expect(find.text('Companion chat route reached'), findsOneWidget);
    expect(service.attempts, 1);
  });

  testWidgets('retry remains available when overview is unavailable', (
    tester,
  ) async {
    final service = _UnavailableOverview();
    await tester.pumpWidget(_harness(service, const Locale('fr')));
    await tester.pumpAndSettle();
    expect(service.attempts, 1);

    await tester.tap(find.byKey(const Key('companion-overview-retry-action')));
    await tester.pumpAndSettle();

    expect(service.attempts, 2);
    expect(find.text('Données indisponibles'), findsOneWidget);
    expect(find.byKey(const Key('companion-overview-chat-action')), findsOneWidget);
  });

  for (final locale in const [Locale('en'), Locale('ar')]) {
    testWidgets('localized error exit and retry in ${locale.languageCode}', (tester) async {
      await tester.pumpWidget(_harness(_UnavailableOverview(), locale));
      await tester.pumpAndSettle();
      final isArabic = locale.languageCode == 'ar';
      expect(
        find.text(isArabic ? 'تحدث مع IAmina' : 'Chat with IAmina'),
        findsOneWidget,
      );
      expect(
        find.text(isArabic ? 'إعادة المحاولة' : 'Retry'),
        findsOneWidget,
      );
      expect(
        Directionality.of(tester.element(find.byType(CompanionPremiumScreen))),
        isArabic ? TextDirection.rtl : TextDirection.ltr,
      );
      expect(tester.takeException(), isNull);
    });
  }
}
