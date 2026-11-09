import 'dart:io';

import 'package:amina/features/auth/login_screen_fr_certified.dart' as fr;
import 'package:amina/features/auth/login_screen_mena.dart' as mena;
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W01 Preview sign-in and account creation are independent', () {
    final auth = File('lib/services/auth_service.dart').readAsStringSync();
    final entry = File('lib/features/auth/login_screen.dart').readAsStringSync();
    final build = File('vercel_build.sh').readAsStringSync();

    expect(auth, contains("'IAMINA_REMOTE_ACCOUNT_SIGN_IN'"));
    expect(auth, contains('defaultValue: kRemoteAccountEnrollmentEnabled'));
    expect(auth, contains('if (!kRemoteAccountEnrollmentEnabled)'));
    expect(entry, contains('if (!_accountMode || !kRemoteAccountSignInEnabled)'));
    expect(entry, contains('syntheticLoginOnly: !kRemoteAccountEnrollmentEnabled'));
    expect(build, contains('IAMINA_REMOTE_ACCOUNT_SIGN_IN=true'));
    expect(build, contains('IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false'));
    expect(build, isNot(contains('IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED=true')));
  });

  for (final locale in const ['fr', 'ar']) {
    for (final size in const [Size(390, 844), Size(768, 1024)]) {
      testWidgets('W01 synthetic-only sign-in UI $locale $size', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(MaterialApp(
          locale: Locale(locale),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: locale == 'fr'
              ? const fr.LoginScreen(syntheticLoginOnly: true)
              : const mena.LoginScreen(syntheticLoginOnly: true),
        ));
        await tester.pumpAndSettle();

        final l10n =
            AppLocalizations.of(tester.element(find.byType(Scaffold).first))!;
        expect(find.byType(TextField), findsNWidgets(2));
        expect(find.text(l10n.signIn), findsOneWidget);
        expect(find.text(l10n.createAccount), findsNothing);
        expect(find.text(l10n.forgotPassword), findsNothing);
        expect(find.text(l10n.demoAccess), findsNothing);
        if (locale == 'fr') {
          expect(find.text('Accès démo'), findsNothing);
          expect(find.text('Créer un compte'), findsNothing);
        }
        expect(tester.takeException(), isNull);
      });
    }
  }
}
