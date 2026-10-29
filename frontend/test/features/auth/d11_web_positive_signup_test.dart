import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/login_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

const _syntheticToken =
    'iamina.eyJ1aWQiOjEsInYiOjB9:1abcdf:signature_456';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  for (final locale in const ['fr', 'ar']) {
    for (final viewport in const <(double, double)>[
      (390, 844), (768, 1024), (1280, 900),
    ]) {
      testWidgets('D11 optional hosted signup real UI $locale $viewport',
          (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        FlutterSecureStorage.setMockInitialValues({});
        var registered = 0;
        var forbiddenDemoCalls = 0;
        final auth = AuthService(httpClient: MockClient((request) async {
          if (request.url.path == '/api/v1/auth/register') {
            registered++;
            return http.Response(
              '{"access_token":"$_syntheticToken","user":{"id":1}}',
              200,
            );
          }
          if (request.url.path.contains('demo')) forbiddenDemoCalls++;
          fail('Unexpected endpoint for account registration UI');
        }));
        await auth.initialize();
        final db = AppDatabase.defaults();
        final api = ApiClient(authService: auth);
        final router = GoRouter(routes: [
          GoRoute(path: '/', builder: (_, __) => const LoginScreen()),
          GoRoute(
            path: '/onboarding',
            builder: (_, __) => const Scaffold(
              body: Center(child: Text('D11_POSITIVE_ONBOARDING')),
            ),
          ),
        ]);
        addTearDown(() async {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
          router.dispose();
          await db.close();
          auth.dispose();
        });

        await tester.pumpWidget(MultiProvider(
          providers: [
            ChangeNotifierProvider<AuthService>.value(value: auth),
            Provider<AppDatabase>.value(value: db),
            Provider<ApiClient>.value(value: api),
          ],
          child: MaterialApp.router(
            routerConfig: router,
            locale: Locale(locale),
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
        expect(tester.takeException(), isNull);

        // D30 local-first entry must offer optional account creation.
        final accountChoice = find.byKey(const Key('d30-choose-account'));
        expect(accountChoice, findsOneWidget);
        await tester.ensureVisible(accountChoice);
        await tester.tap(accountChoice);
        await tester.pumpAndSettle();

        final l10n =
            AppLocalizations.of(tester.element(find.byType(Scaffold).first))!;
        final signup = find.text(l10n.createAccount);
        await tester.ensureVisible(signup.last);
        await tester.tap(signup.last);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsOneWidget);
        final inputs = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextField),
        );
        expect(inputs, findsNWidgets(3));
        await tester.enterText(inputs.at(0), 'test-patient@example.invalid');
        await tester.enterText(inputs.at(1), 'Strong-Synthetic-2026!');
        await tester.enterText(inputs.at(2), 'Strong-Synthetic-2026!');
        final submit = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(FilledButton),
        );
        await tester.tap(submit);
        await tester.pumpAndSettle();
        expect(registered, 1);
        expect(forbiddenDemoCalls, 0);
        expect(auth.isRemoteCredentialVerified, isTrue);
        expect(auth.boundNativeAccountId, 1);
        expect(find.text('D11_POSITIVE_ONBOARDING'), findsOneWidget);
        expect(tester.takeException(), isNull);
      }, skip: !kRemoteAccountEnrollmentEnabled);
    }
  }
}
