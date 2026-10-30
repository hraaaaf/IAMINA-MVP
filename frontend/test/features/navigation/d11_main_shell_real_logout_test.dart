import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/navigation/main_shell.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/modules_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

/// D11: exercise the real web MainShell logout pointer, not a direct AuthService
/// call. All account and bearer values are synthetic and local to the test.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const token = 'iamina.e30:1abcde:signature_123';

  for (final locale in const ['fr', 'ar']) {
    for (final viewport in const <(double, double)>[
      (768, 1024),
      (1280, 900),
    ]) {
      testWidgets('D11 MainShell real logout pointer $locale $viewport',
          (tester) async {
        tester.view.physicalSize = Size(viewport.$1, viewport.$2);
        tester.view.devicePixelRatio = 1;
        FlutterSecureStorage.setMockInitialValues({
          'iamina_native_access_token': token,
          'iamina_native_account_binding_v1': jsonEncode({
            'token': token,
            'user_id': 42,
          }),
          'iamina_local_session_v1': 'enrolled',
        });

        var logoutRequests = 0;
        final auth = AuthService(
          httpClient: MockClient((request) async {
            expect(request.method, 'POST');
            expect(request.url.path, '/api/v1/auth/logout');
            expect(request.headers['Authorization'], 'Bearer $token');
            logoutRequests++;
            return http.Response('{}', 200);
          }),
        );
        await tester.runAsync(() => auth.initialize());
        expect(auth.hasRemoteApiCredential, isTrue);
        expect(auth.boundNativeAccountId, 42);

        final api = ApiClient(authService: auth);
        final modules = ModulesProvider(api);
        final router = GoRouter(
          initialLocation: '/dashboard',
          routes: [
            ShellRoute(
              builder: (_, __, child) => MainShell(child: child),
              routes: [
                GoRoute(
                  path: '/dashboard',
                  builder: (_, __) => const Center(
                    child: Text('D11_SYNTHETIC_DASHBOARD'),
                  ),
                ),
              ],
            ),
            GoRoute(
              path: '/login',
              builder: (_, __) => const Scaffold(
                body: Center(child: Text('D11_SIGNED_OUT_LOGIN')),
              ),
            ),
          ],
        );
        addTearDown(() async {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
          router.dispose();
          modules.dispose();
          auth.dispose();
        });

        await tester.pumpWidget(MultiProvider(
          providers: [
            ChangeNotifierProvider<AuthService>.value(value: auth),
            ChangeNotifierProvider<ModulesProvider>.value(value: modules),
            Provider<PatientProfileData?>.value(value: null),
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
        expect(find.text('D11_SYNTHETIC_DASHBOARD'), findsOneWidget);

        // Separate a true product accessibility failure from Flutter Web's
        // test-browser semantics transport. The actual sidebar InkWell MUST
        // expose a native Semantics button and localized accessible name.
        final handle = tester.ensureSemantics();
        try {
        // Rebuild accessibility after enabling semantics on an already-painted
        // ShellRoute; otherwise the tree may contain only its central child.
        await tester.pumpAndSettle();
        final expectedLabel = locale == 'fr' ? 'Déconnexion' : 'تسجيل الخروج';
        final semanticMatch = find.bySemanticsLabel(expectedLabel);
        if (semanticMatch.evaluate().isEmpty && locale == 'fr' && viewport.$1 == 768) {
          final configured = tester.widgetList<Semantics>(find.byType(Semantics))
              .where((widget) => (widget.properties.label ?? '').contains(expectedLabel))
              .map((widget) => 'label=${widget.properties.label} button=${widget.properties.button}')
              .toList();
          debugPrint('D11_LOGOUT_SEMANTICS_CONFIG=$configured');
          final tree = tester.binding.pipelineOwner.semanticsOwner
              ?.rootSemanticsNode?.toStringDeep();
          debugPrint('D11_SEMANTICS_TREE=${tree ?? 'NO_SEMANTICS_ROOT'}');
        }
        expect(
          find.bySemanticsLabel(
            locale == 'fr' ? 'Déconnexion' : 'تسجيل الخروج',
          ),
          findsOneWidget,
        );

        // The app's actual sidebar InkWell, by its real logout icon. Do not
        // invoke AuthService.signOut() from the test itself.
        final logout = find.byIcon(Icons.logout_rounded);
        expect(logout, findsOneWidget);
        await tester.ensureVisible(logout);
        await tester.tap(logout);
        await tester.pumpAndSettle();

        expect(logoutRequests, 1);
        expect(auth.isAuthenticated, isFalse);
        expect(auth.hasRemoteApiCredential, isFalse);
        expect(auth.boundNativeAccountId, isNull);
        expect(await auth.resolvePatientVaultScope(), isNull);
        expect(find.text('D11_SIGNED_OUT_LOGIN'), findsOneWidget);
        expect(find.text('D11_SYNTHETIC_DASHBOARD'), findsNothing);
        expect(tester.takeException(), isNull);
        } finally {
          // dispose BEFORE widget test's own end-of-test assertions;
          // addTearDown executes too late for SemanticsHandle checks.
          handle.dispose();
        }
      });
    }
  }
}
