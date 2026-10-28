import 'package:amina/features/auth/w01_read_only_preview_screen.dart';
import 'package:amina/features/navigation/main_shell.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthService auth;
  late AppLockService lock;
  late ConsentService consent;

  setUp(() async {
    FlutterSecureStorage.setMockInitialValues({});
    auth = AuthService();
    lock = AppLockService();
    await lock.initialize();
    consent = ConsentService();
  });

  tearDown(() {
    consent.dispose();
    lock.dispose();
    auth.dispose();
  });

  Widget testApp() {
    final router = GoRouter(
      initialLocation: '/w01-preview',
      routes: [
        GoRoute(
          path: '/w01-preview',
          builder: (_, __) =>
              const W01ReadOnlyPreviewScreen(previewEnabled: true),
        ),
        GoRoute(
          path: '/app-lock/setup',
          builder: (_, __) => const Scaffold(body: Text('Setup')),
        ),
        GoRoute(
          path: '/app-lock/unlock',
          builder: (_, __) => const Scaffold(body: Text('Unlock')),
        ),
        GoRoute(
          path: '/consent',
          builder: (_, __) => const Scaffold(body: Text('Server consent')),
        ),
        GoRoute(
          path: '/dashboard',
          builder: (_, __) => const Scaffold(body: Text('Patient dashboard')),
        ),
      ],
    );
    addTearDown(router.dispose);
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthService>.value(value: auth),
        ChangeNotifierProvider<AppLockService>.value(value: lock),
        ChangeNotifierProvider<ConsentService>.value(value: consent),
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
        supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
      ),
    );
  }

  Widget medicalBannerApp() => MultiProvider(
    providers: [
      ChangeNotifierProvider<AuthService>.value(value: auth),
      ChangeNotifierProvider<AppLockService>.value(value: lock),
      ChangeNotifierProvider<ConsentService>.value(value: consent),
    ],
    child: MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
      home: const Scaffold(
        body: Column(
          children: [
            W01OptionalChoicesBar(),
            Expanded(child: Center(child: Text('Medical home unchanged'))),
          ],
        ),
      ),
    ),
  );

  for (final size in [const Size(390, 640), const Size(390, 844)]) {
    testWidgets('W01 medical banner accept visibly explains local-only block '
        'on ${size.width}x${size.height}', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(medicalBannerApp());
      await tester.pumpAndSettle();

      final accept = find.byKey(const Key('w01-medical-consent-accept'));
      expect(accept, findsOneWidget);
      await tester.tap(accept);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('w01-consent-account-required-dialog')),
          findsOneWidget);
      expect(find.textContaining('Cette session locale ne peut pas'),
          findsOneWidget);
      expect(find.text('Medical home unchanged'), findsOneWidget);
      expect(consent.hasConsent, isFalse);

      await tester.tap(
          find.byKey(const Key('w01-consent-account-required-dismiss')));
      await tester.pumpAndSettle();
      expect(accept, findsOneWidget);
      expect(consent.hasConsent, isFalse);

      await tester.tap(find.byKey(const Key('w01-medical-consent-skip')));
      await tester.pumpAndSettle();
      expect(consent.hasDeclinedLocally, isTrue);
      expect(consent.hasConsent, isFalse);
      expect(accept, findsNothing);
      expect(find.text('Medical home unchanged'), findsOneWidget);
    });
  }

  testWidgets('390x844 top-left accept and skip never unlock patient vault', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();

    final card = find.byKey(const Key('w01-preview-consent-card'));
    expect(card, findsOneWidget);
    expect(find.text('Accepter'), findsOneWidget);
    expect(find.text('Passer'), findsOneWidget);
    expect(tester.getRect(card).left, lessThan(30));

    await tester.tap(find.byKey(const Key('w01-preview-consent-accept')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('w01-preview-consent-required-dialog')),
        findsOneWidget);
    expect(find.textContaining('Aucun consentement n’a été accordé'),
        findsOneWidget);
    expect(find.text('Server consent'), findsNothing);
    expect(consent.hasConsent, isFalse);
    expect(lock.isUnlocked, isFalse);

    await tester.tap(
        find.byKey(const Key('w01-preview-consent-dialog-dismiss')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('w01-preview-consent-required-dialog')),
        findsNothing);
    await tester.tap(find.byKey(const Key('w01-preview-consent-skip')));
    await tester.pumpAndSettle();
    expect(card, findsNothing);
    expect(find.text('Patient dashboard'), findsNothing);
    expect(consent.hasConsent, isFalse);
    expect(lock.isUnlocked, isFalse);
  });

  testWidgets('read-only preview can offer strong lock setup', (tester) async {
    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('w01-preview-open-lock')));
    await tester.tap(find.byKey(const Key('w01-preview-open-lock')));
    await tester.pumpAndSettle();
    expect(find.text('Setup'), findsOneWidget);
    expect(find.text('Patient dashboard'), findsNothing);
  });
}
