import 'dart:io';

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
    expect(source.contains('kD2GuestNoDatabasePreview &&'), isTrue);
    expect(source.contains('kD1PreviewOnlySyntheticAccounts &&'), isTrue);
    expect(source.contains('!kFirebaseMigrationEnabled &&'), isTrue);
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
}
