import 'package:amina/features/auth/login_screen_fr_certified.dart' as fr;
import 'package:amina/features/auth/login_screen_mena.dart' as mena;
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:drift/native.dart';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:amina/services/auth_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/data/drift/database.dart';

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

        // D11 FUE: text-entry may leave the keyboard/selection overlay
        // above the recovery action. Dismiss it through the user-facing
        // focus path, then verify the actual button is hit-testable.
        FocusManager.instance.primaryFocus?.unfocus();
        await tester.testTextInput.hide();
        await tester.pumpAndSettle();
        final forgot = find.widgetWithText(TextButton, l10n.forgotPassword);
        await tester.ensureVisible(forgot);
        await tester.pumpAndSettle();
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
  // Actual login controls, keyboard focus and negative/recovery behavior are
  // verified with transport-only synthetic HTTP responses. Separate PG16
  // Chrome runs test real login and patient-vault isolation end-to-end.
  for (final locale in const ['fr', 'ar']) {
    for (final viewport in const <(double, double)>[
      (390, 844), (768, 1024), (1280, 900),
    ]) {
      testWidgets('D11 login keyboard negative and recovery $locale $viewport',
          (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        FlutterSecureStorage.setMockInitialValues({});
        // Diagnostic markers are fixture-only; never include credentials.
        // ignore: avoid_print
        print('D11_FUE_NEG_STAGE=fixture_started:$locale:${viewport.$1}');
        var rejectedLogins = 0;
        var recoveryRequests = 0;
        final auth = AuthService(
          httpClient: MockClient((request) async {
            if (request.url.path == '/api/v1/auth/login') {
              rejectedLogins++;
              return http.Response('{"error":"invalid_credentials"}', 401);
            }
            if (request.url.path ==
                '/api/v1/auth/password/reset/request') {
              recoveryRequests++;
              return http.Response('{}', 200);
            }
            fail('Unexpected auth request: ${request.url.path}');
          }),
        );
        // Secure-storage plugin futures must run outside FakeAsync in widget tests.
        await tester.runAsync(() async {
          await auth.initialize();
        });
        // No shared real/legacy patient database in FUE widget tests.
        // ignore: avoid_print
        print('D11_FUE_NEG_STAGE=auth_initialized:$locale:${viewport.$1}');
        final db = AppDatabase(NativeDatabase.memory());
        final api = ApiClient(authService: auth);
        addTearDown(() async {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
          await db.close();
          auth.dispose();
        });
        await tester.pumpWidget(MultiProvider(
          providers: [
            ChangeNotifierProvider<AuthService>.value(value: auth),
            Provider<AppDatabase>.value(value: db),
            Provider<ApiClient>.value(value: api),
          ],
          child: MaterialApp(
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
          ),
        ));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        // ignore: avoid_print
        print('D11_FUE_NEG_STAGE=widget_rendered:$locale:${viewport.$1}');
        final fields = find.byType(TextField);
        final editableFields = find.byType(EditableText);
        final emailFocus =
            tester.widget<EditableText>(editableFields.at(0)).focusNode;
        final passwordFocus =
            tester.widget<EditableText>(editableFields.at(1)).focusNode;
        await tester.tap(fields.first);
        await tester.pump();
        expect(emailFocus.hasFocus, isTrue);
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pump();
        // Keyboard Tab must traverse from email to password with no egress.
        expect(emailFocus.hasFocus, isFalse);
        expect(passwordFocus.hasFocus, isTrue);
        expect(rejectedLogins, 0);

        await tester.enterText(fields.at(0), 'patient@example.invalid');
        await tester.enterText(fields.at(1), 'bad-password');
        final l10n =
            AppLocalizations.of(tester.element(find.byType(Scaffold).first))!;
        final submit = find.text(l10n.signIn);
        await tester.ensureVisible(submit);
        await tester.tap(submit);
        await tester.pumpAndSettle();
        expect(rejectedLogins, 1);
        // ignore: avoid_print
        print('D11_FUE_NEG_STAGE=login_denied:$locale:${viewport.$1}');
        expect(find.text(l10n.loginError), findsOneWidget);
        expect(auth.isRemoteCredentialVerified, isFalse);
        expect(auth.boundNativeAccountId, isNull);
        expect(tester.takeException(), isNull);

        final forgot = find.text(l10n.forgotPassword);
        await tester.ensureVisible(forgot);
        await tester.tap(forgot);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsOneWidget);
        final dialogField = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextField),
        );
        await tester.enterText(dialogField, 'patient@example.invalid');
        final send = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(FilledButton),
        );
        await tester.tap(send);
        await tester.pumpAndSettle();
        expect(recoveryRequests, 1);
        // ignore: avoid_print
        print('D11_FUE_NEG_STAGE=recovery_requested:$locale:${viewport.$1}');
        expect(find.byType(AlertDialog), findsNothing);
        expect(auth.isRemoteCredentialVerified, isFalse);
        expect(tester.takeException(), isNull);
      });
    }
  }

}
