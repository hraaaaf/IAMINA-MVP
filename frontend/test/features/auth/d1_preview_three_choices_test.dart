import 'package:amina/features/auth/login_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  for (final viewport in const [Size(390, 844), Size(768, 1024), Size(1280, 900)]) {
    testWidgets('D1 Preview: guest, native login and immediate signup at ${viewport.width}x${viewport.height}',
        (tester) async {
      tester.view.physicalSize = viewport;
      tester.view.devicePixelRatio = 1;
      FlutterSecureStorage.setMockInitialValues({});
      final auth = AuthService();
      await tester.runAsync(() async => auth.initialize());
      final router = GoRouter(routes: [
        GoRoute(path: '/', builder: (_, __) => const LoginScreen()),
        GoRoute(path: '/app-lock/setup', builder: (_, __) =>
            const Scaffold(body: Text('D1_SYNTHETIC_SAFE_HOLD_GATE'))),
      ]);
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
        router.dispose();
        auth.dispose();
      });
      await tester.pumpWidget(ChangeNotifierProvider<AuthService>.value(
        value: auth,
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

      expect(find.text('Continuer sans compte'), findsOneWidget);
      expect(find.byKey(const Key('d30-choose-account')), findsOneWidget);
      expect(find.byKey(const Key('d1-preview-create-account')), findsOneWidget);
      // No sign-out is possible on the welcome screen.
      expect(find.text('Se déconnecter'), findsNothing);

      final signup = find.byKey(const Key('d1-preview-create-account'));
      await tester.ensureVisible(signup);
      await tester.tap(signup);
      await tester.pumpAndSettle();
      expect(find.byType(AlertDialog), findsOneWidget);
      final fields = find.descendant(
        of: find.byType(AlertDialog), matching: find.byType(TextField),
      );
      expect(fields, findsNWidgets(3));
      // The dialog does not create an account unless form is submitted.
      final cancel = find.widgetWithText(TextButton, 'Annuler').first;
      await tester.tap(cancel);
      await tester.pumpAndSettle();

      final back = find.byKey(const Key('d30-return-local'));
      await tester.ensureVisible(back);
      await tester.tap(back);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d30-choose-account')), findsOneWidget);
      await tester.tap(find.byKey(const Key('d30-choose-account')));
      await tester.pumpAndSettle();
      expect(find.text('Se connecter'), findsWidgets);
      expect(tester.takeException(), isNull);
    }, skip: !kD1PreviewAuthChoices || !kRemoteAccountSignInEnabled ||
            !kRemoteAccountEnrollmentEnabled);
  }
}
