import 'package:amina/features/auth/local_device_enrollment_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';

class _MockAuthService extends Mock implements AuthService {}

void main() {
  testWidgets('D30 local CTA calls device enrollment and goes to app-lock setup',
      (tester) async {
    final auth = _MockAuthService();
    when(() => auth.enrollLocalDevice()).thenAnswer((_) async {});
    final router = GoRouter(initialLocation: '/login', routes: [
      GoRoute(
        path: '/login',
        builder: (_, __) => const LocalDeviceEnrollmentScreen(),
      ),
      GoRoute(
        path: '/app-lock/setup',
        builder: (_, __) => const Scaffold(
          body: Center(child: Text('D30_LOCK_ROUTE_REACHED')),
        ),
      ),
    ]);
    addTearDown(router.dispose);

    await tester.pumpWidget(ChangeNotifierProvider<AuthService>.value(
      value: auth,
      child: MaterialApp.router(
        routerConfig: router,
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
    // FilledButton.icon is implemented by a private subclass in Flutter;
    // find.byType(FilledButton) checks the exact runtimeType and misses it.
    final button = find.byWidgetPredicate((widget) => widget is FilledButton);
    expect(button, findsOneWidget);
    await tester.ensureVisible(button);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pumpAndSettle();
    verify(() => auth.enrollLocalDevice()).called(1);
    expect(find.text('D30_LOCK_ROUTE_REACHED'), findsOneWidget);
    expect(router.routeInformationProvider.value.uri.path, '/app-lock/setup');
  });
  testWidgets('D30 offers remote account as a separate choice when available',
      (tester) async {
    final auth = _MockAuthService();
    var accountSelected = false;
    await tester.pumpWidget(ChangeNotifierProvider<AuthService>.value(
      value: auth,
      child: MaterialApp(
        locale: const Locale('fr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: LocalDeviceEnrollmentScreen(
          onChooseAccount: () => accountSelected = true,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final remote = find.byKey(const Key('d30-choose-account'));
    expect(remote, findsOneWidget);
    expect(find.text('Se connecter ou créer un compte'), findsOneWidget);
    await tester.ensureVisible(remote);
    await tester.pumpAndSettle();
    await tester.tap(remote);
    expect(accountSelected, isTrue);
    verifyNever(() => auth.enrollLocalDevice());
  });
}
