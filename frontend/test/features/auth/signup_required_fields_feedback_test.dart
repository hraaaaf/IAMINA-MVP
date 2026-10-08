import 'package:amina/features/auth/login_screen_fr_certified.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final size in const [Size(390, 844), Size(360, 560)]) {
    testWidgets('signup explains missing and mismatched fields at ${size.width.toInt()}x${size.height.toInt()}',
        (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(const MaterialApp(
        locale: Locale('fr'),
        supportedLocales: [Locale('fr')],
        localizationsDelegates: [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: LoginScreen(),
      ));
      await tester.pumpAndSettle();
      final openSignup = find.widgetWithText(TextButton, 'Créer un compte');
      await tester.ensureVisible(openSignup);
      await tester.tap(openSignup);
      await tester.pumpAndSettle();
      expect(find.byType(AlertDialog), findsOneWidget);

      final create = find.widgetWithText(FilledButton, 'Créer');
      await tester.tap(create);
      await tester.pump();
      expect(find.text('Renseignez les trois champs pour créer votre compte.'),
          findsOneWidget);
      expect(find.byKey(const Key('signup-validation-feedback')), findsOneWidget);
      expect(find.byType(AlertDialog), findsOneWidget);

      final fields = find.descendant(
        of: find.byType(AlertDialog),
        matching: find.byType(TextField),
      );
      expect(fields, findsNWidgets(3));
      await tester.enterText(fields.at(0), 'test@example.invalid');
      await tester.enterText(fields.at(1), 'ValidSyntheticPassword-99');
      await tester.enterText(fields.at(2), 'DifferentSyntheticPassword-88');
      await tester.tap(create);
      await tester.pump();
      expect(find.text('Les mots de passe ne correspondent pas.'),
          findsOneWidget);
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(tester.takeException(), isNull);

      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    });
  }
}
