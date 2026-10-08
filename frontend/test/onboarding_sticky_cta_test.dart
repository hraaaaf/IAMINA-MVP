import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/onboarding_chat_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

class _LocalPreferences extends LocalePreferenceService {
  _LocalPreferences() : super(ApiClient(baseUrl: 'http://localhost:8000'));

  @override
  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {}
}

void main() {
  testWidgets('completed first use keeps Commencer fully visible at 390x844',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    final prefs = _LocalPreferences();
    final auth = AuthService();
    addTearDown(db.close);
    addTearDown(prefs.dispose);
    addTearDown(auth.dispose);
    final router = GoRouter(
      initialLocation: '/onboarding',
      routes: [
        GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingChatScreen()),
        GoRoute(path: '/dashboard', builder: (_, __) => const Scaffold(body: Text('Dashboard'))),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<AuthService>.value(value: auth),
        ChangeNotifierProvider<LocalePreferenceService>.value(value: prefs),
      ],
      child: MaterialApp.router(
        routerConfig: router,
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
      ),
    ));
    await tester.pumpAndSettle();

    Future<void> select(String label) async {
      final choice = find.text(label);
      await tester.ensureVisible(choice);
      await tester.pumpAndSettle();
      await tester.tap(choice);
      await tester.pumpAndSettle();
    }

    await select('Français');
    await select('Maroc');
    await select('Simple et chaleureux');
    await select('Diabète Type 2');
    await select('Comprimés');

    final start = find.byKey(const Key('onboarding-sticky-start'));
    expect(start, findsOneWidget);
    expect(find.text('Commencer'), findsOneWidget);
    final rect = tester.getRect(start);
    expect(rect.top, greaterThanOrEqualTo(0));
    expect(rect.bottom, lessThanOrEqualTo(844));
    expect(tester.takeException(), isNull);

    await tester.tap(start);
    await tester.pumpAndSettle();
    expect(find.text('Dashboard'), findsOneWidget);
  });
}
