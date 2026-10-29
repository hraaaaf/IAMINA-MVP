import 'package:amina/features/auth/login_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// This test runs in real Chrome with IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED=true
/// and IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false. No accounts or credentials.
void main() {
  testWidgets('D7 QA Preview exposes existing-account login but no signup',
      (tester) async {
    expect(kRemoteAccountLoginEnabled, isTrue);
    expect(kRemoteAccountEnrollmentEnabled, isFalse);
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: const LoginScreen(),
    ));
    await tester.pumpAndSettle();
    final choose = find.byKey(const Key('d30-choose-account'));
    expect(choose, findsOneWidget);
    await tester.ensureVisible(choose);
    await tester.tap(choose);
    await tester.pumpAndSettle();
    expect(find.text('Créer un compte'), findsNothing);
    expect(find.byKey(const Key('d30-return-local')), findsOneWidget);
  });
}
