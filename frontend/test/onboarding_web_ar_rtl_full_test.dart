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

// Independent post-merge audit: full AR/RTL step sequence on synthetic vault.
class _ArabicTestPreferences extends LocalePreferenceService {
  _ArabicTestPreferences() : super(ApiClient(baseUrl: 'http://localhost:8000'));

  @override
  Future<void> setLanguageOnly(String language) async {}

  @override
  Future<String?> suggestCountryFromIp() async => null;

  @override
  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {}
}

void main() {
  for (final size in <Size>[
    const Size(390, 844),
    const Size(768, 1024),
    const Size(1280, 900),
  ]) {
    testWidgets('Post-merge Web Arabic RTL journey at $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      final prefs = _ArabicTestPreferences();
      final auth = AuthService();
      addTearDown(db.close);
      addTearDown(prefs.dispose);
      addTearDown(auth.dispose);
      final router = GoRouter(initialLocation: '/onboarding', routes: [
        GoRoute(path: '/onboarding',
          builder: (_, __) => const OnboardingChatScreen()),
        GoRoute(path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('Dashboard'))),
      ]);
      addTearDown(router.dispose);

      await tester.pumpWidget(MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          ChangeNotifierProvider<AuthService>.value(value: auth),
          ChangeNotifierProvider<LocalePreferenceService>.value(value: prefs),
        ],
        child: MaterialApp.router(
          routerConfig: router,
          locale: const Locale('ar'),
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

      void rtlTitle(String copy, {bool revealed = false}) {
        final finder = find.text(copy);
        expect(finder, findsOneWidget);
        expect(Directionality.of(tester.element(finder)), TextDirection.rtl);
        if (revealed && size.width < 900) {
          final rect = tester.getRect(finder);
          expect(rect.top, greaterThanOrEqualTo(-1));
          expect(rect.top, lessThan(size.height - 55));
        }
      }

      rtlTitle('اختر لغة التطبيق.');
      await tester.tap(find.text('العربية'));
      await tester.pumpAndSettle();
      rtlTitle('في أي بلد تستخدم IAmina؟', revealed: true);

      final country = find.byKey(const Key('onboarding-country-search'));
      await tester.tap(country);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).last, 'المغر');
      await tester.pumpAndSettle();
      await tester.tap(find.text('المغرب').last);
      await tester.pumpAndSettle();
      rtlTitle('ما نوع داء السكري الذي تتابعه؟', revealed: true);

      final type2 = find.text('السكري النوع 2');
      await tester.ensureVisible(type2);
      await tester.pumpAndSettle();
      await tester.tap(type2);
      await tester.pumpAndSettle();
      rtlTitle('ما العلاجات التي تتبعها حاليًا؟ (اختياري)',
        revealed: true);

      final oral = find.byKey(const Key('d7-treatment-oral_meds'));
      final lifestyle = find.byKey(const Key('d7-treatment-lifestyle'));
      await tester.ensureVisible(oral);
      await tester.pumpAndSettle();
      final header = find.text('ما العلاجات التي تتبعها حاليًا؟ (اختياري)');
      final before = tester.getRect(header).top;
      await tester.tap(oral);
      await tester.pumpAndSettle();
      expect(tester.getRect(header).top, closeTo(before, 1));
      await tester.tap(lifestyle);
      await tester.pumpAndSettle();
      expect(tester.getRect(header).top, closeTo(before, 1));

      final next = find.byKey(const Key('onboarding-treatment-next'));
      if (size.width < 900) {
        await tester.ensureVisible(next);
        await tester.pumpAndSettle();
        expect(find.text('المتابعة إلى الوحدات'), findsOneWidget);
        await tester.tap(next);
        await tester.pumpAndSettle();
      } else {
        expect(next, findsNothing);
      }
      rtlTitle('ما وحدة القياس التي تفضلها؟',
        revealed: size.width < 900);
      expect(find.text('ابدأ'), findsOneWidget);
      expect(find.text('Dashboard'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }
}