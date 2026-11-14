import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:amina/services/auth_service.dart';
import 'package:amina/services/d2_guest_runtime.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D2 guest bootstrap precedes any clinical database or API bootstrap', () {
    final source = File('lib/main.dart').readAsStringSync();
    final guest = source.indexOf('runApp(D2GuestRuntime(auth: authService))');
    final legacy = source.indexOf('AppDatabase.defaults()');
    final controller =
        source.indexOf('PatientVaultSessionController.forAuth(authService)');
    final locale = source.indexOf('final localePreferenceService =');
    expect(guest, greaterThan(0));
    expect(guest, lessThan(legacy));
    expect(guest, lessThan(controller));
    expect(guest, lessThan(locale));
    expect(source.contains('if (kIsWeb && kD2GuestNoDatabasePreview)'), isTrue);
    expect(source.contains('!kD1PreviewOnlySyntheticAccounts ||'), isTrue);
    expect(source.contains('kFirebaseMigrationEnabled ||'), isTrue);
    final denied = source.indexOf('D2 Preview unavailable: synthetic-only');
    expect(denied, greaterThan(0));
    expect(denied, lessThan(legacy));
  });

  test('D2 guest runtime and shell have no clinical database imports', () {
    final runtime =
        File('lib/services/d2_guest_runtime.dart').readAsStringSync();
    final shell =
        File('lib/features/navigation/d2_guest_shell.dart').readAsStringSync();
    for (final source in [runtime, shell]) {
      expect(source.contains("import '../data/drift/database.dart'"), isFalse);
      expect(source.contains('AppDatabase.forPatientVault('), isFalse);
      expect(source.contains('AppDatabase.defaults('), isFalse);
      expect(source.contains('ApiClient('), isFalse);
      expect(source.contains('SyncService('), isFalse);
      expect(source.contains('seedDemoData('), isFalse);
      expect(source.contains('http.post('), isFalse);
    }
    expect(runtime.contains('IAMINA_D2_GUEST_NO_DB'), isTrue);
    expect(runtime.contains('kD1PreviewOnlySyntheticAccounts'), isTrue);
    expect(runtime.contains('isRemoteCredentialVerified'), isTrue);
  });

  for (final locale in const [Locale('fr'), Locale('ar')]) {
    testWidgets('D2 guest runtime: browse then auth gate without any DB $locale',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      FlutterSecureStorage.setMockInitialValues({});
      final auth = AuthService();
      await tester.runAsync(() => auth.initialize());
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
        auth.dispose();
      });

      await tester.pumpWidget(D2GuestRuntime(auth: auth, locale: locale));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
      expect(find.byKey(const Key('d2-guest-auth-gate')), findsNothing);

      // Merely browsing doesn't construct an auth form or patient vault.
      await tester.tap(find.byKey(const Key('d2-guest-nav-journal')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
      expect(find.byKey(const Key('d2-guest-auth-gate')), findsNothing);

      await tester.tap(find.byKey(const Key('d2-guest-nav-dashboard')));
      await tester.pumpAndSettle();
      final add = find.byKey(const Key('d2-guest-action-add'));
      await tester.ensureVisible(add);
      await tester.tap(add);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d2-guest-auth-gate')), findsOneWidget);
      expect(find.text('/ajouter'), findsOneWidget);

      // Without explicit synthetic Preview build flags, auth is default-deny.
      await tester.tap(find.byKey(const Key('d2-guest-auth-submit')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d2-guest-auth-error')), findsOneWidget);
      expect(find.byKey(const Key('d2-guest-authenticated-safe-hold')),
          findsNothing);

      await tester.tap(find.byKey(const Key('d2-guest-auth-back')));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
      expect(find.byKey(const Key('d2-guest-auth-gate')), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('D2 synthetic A registration, logout, login: no patient request',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    FlutterSecureStorage.setMockInitialValues({});
    final paths = <String>[];
    final client = MockClient((request) async {
      paths.add(request.method + ' ' + request.url.path);
      if (request.url.path.endsWith('/auth/register') ||
          request.url.path.endsWith('/auth/login')) {
        return http.Response(
          jsonEncode({
            'access_token': 'iamina.synthetic:1:signature',
            'user': {'id': 920001},
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path.endsWith('/auth/logout')) {
        return http.Response('{"detail":"Signed out"}', 200);
      }
      return http.Response('{"detail":"Forbidden test path"}', 500);
    });
    final auth = AuthService(httpClient: client);
    await tester.runAsync(() => auth.initialize());
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      auth.dispose();
    });

    await tester.pumpWidget(
        D2GuestRuntime(auth: auth, locale: const Locale('fr')));
    await tester.pumpAndSettle();
    final add = find.byKey(const Key('d2-guest-action-add'));
    await tester.ensureVisible(add);
    await tester.tap(add);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-guest-auth-gate')), findsOneWidget);

    await tester.tap(find.byKey(const Key('d2-guest-auth-switch')));
    await tester.pumpAndSettle();
    await tester.enterText(
        find.byKey(const Key('d2-guest-email')), 'real@gmail.com');
    await tester.enterText(
        find.byKey(const Key('d2-guest-password')), 'OnlyForSynthetic!');
    await tester.tap(find.byKey(const Key('d2-guest-auth-submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-guest-auth-error')), findsOneWidget);
    expect(paths, isEmpty); // Real addresses are refused client-side.

    await tester.enterText(
        find.byKey(const Key('d2-guest-email')), 'd2a@d1-preview.test');
    await tester.tap(find.byKey(const Key('d2-guest-auth-submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-guest-authenticated-safe-hold')),
        findsOneWidget);
    expect(find.text('/ajouter'), findsOneWidget);
    expect(auth.isRemoteCredentialVerified, isTrue);

    await tester.tap(find.byKey(const Key('d2-guest-signout')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-guest-empty-state')), findsOneWidget);
    expect(auth.hasRemoteApiCredential, isFalse);

    final imported = find.byKey(const Key('d2-guest-action-import'));
    await tester.ensureVisible(imported);
    await tester.tap(imported);
    await tester.pumpAndSettle();
    await tester.enterText(
        find.byKey(const Key('d2-guest-email')), 'd2a@d1-preview.test');
    await tester.enterText(
        find.byKey(const Key('d2-guest-password')), 'OnlyForSynthetic!');
    await tester.tap(find.byKey(const Key('d2-guest-auth-submit')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('d2-guest-authenticated-safe-hold')),
        findsOneWidget);
    expect(find.text('/importer'), findsOneWidget);
    expect(paths, [
      'POST /api/v1/auth/register',
      'POST /api/v1/auth/logout',
      'POST /api/v1/auth/login',
    ]);
    expect(tester.takeException(), isNull);
  }, skip: !kD1PreviewOnlySyntheticAccounts ||
      !kRemoteAccountSignInEnabled || !kRemoteAccountEnrollmentEnabled);
}
