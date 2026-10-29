import 'package:amina/features/auth/login_screen_fr_certified.dart' as fr;
import 'package:amina/features/auth/login_screen_mena.dart' as mena;
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

/// D11: real FR/AR first-entry widgets, no clinical network or patient writes.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  for (final locale in const ['fr', 'ar']) {
    for (final viewport in const <(double, double)>[
      (390, 844), (768, 1024), (1280, 900),
    ]) {
      testWidgets('D11 real signup and recovery $locale $viewport',
          (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        addTearDown(() {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
        });
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
              ? const fr.LoginScreen()
              : const mena.LoginScreen(),
        ));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        expect(find.byType(TextField), findsNWidgets(2));

        final l10n =
            AppLocalizations.of(tester.element(find.byType(Scaffold).first))!;
        final signup = find.text(l10n.createAccount);
        await tester.ensureVisible(signup.last);
        await tester.tap(signup.last);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsOneWidget);
        final fields = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextField),
        );
        expect(fields, findsNWidgets(3));
        await tester.enterText(fields.at(0), 'fue@example.invalid');
        await tester.enterText(fields.at(1), 'Example-Strong-2026!');
        await tester.enterText(fields.at(2), 'Different-2026!');
        final create = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(FilledButton),
        );
        await tester.ensureVisible(create);
        await tester.tap(create);
        await tester.pumpAndSettle();
        // The UI must not submit mismatched passwords.
        expect(find.byType(AlertDialog), findsOneWidget);
        expect(tester.takeException(), isNull);

        final cancel = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextButton),
        );
        await tester.tap(cancel.first);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsNothing);

        final forgot = find.text(l10n.forgotPassword);
        await tester.ensureVisible(forgot);
        await tester.tap(forgot);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsOneWidget);
        expect(find.text(l10n.resetPassword), findsOneWidget);
        final recoveryCancel = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextButton),
        );
        await tester.tap(recoveryCancel.first);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
