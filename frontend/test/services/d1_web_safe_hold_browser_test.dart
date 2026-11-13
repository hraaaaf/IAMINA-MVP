import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:amina/services/web_patient_vault_safe_hold.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _SyntheticAuthChanges extends ChangeNotifier {
  void switchOwner() => notifyListeners();
}

void main() {
  test('D1 rejected patient vault is never published or replaced by guest',
      () async {
    final auth = _SyntheticAuthChanges();
    var selected = true;
    var attempts = 0;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async =>
          selected ? PatientVaultScope.nativeDjango(734) : null,
      openDatabase: (scope) {
        attempts++;
        // Same refusal as the real Web factory. No SQLite executor created.
        throw StateError('web_patient_vault_encryption_not_verified');
      },
    );
    addTearDown(controller.dispose);
    addTearDown(auth.dispose);
    await controller.reconcile();
    expect(attempts, greaterThan(0));
    expect(controller.requiresEncryptedWebVault, isTrue);
    expect(controller.hasVault, isFalse);
    expect(controller.activeDatabase, isNull);
    expect(controller.activeScope, isNull);

    // A revoked or absent scope must not inherit A's hold/identity state.
    selected = false;
    auth.switchOwner();
    await controller.reconcile();
    expect(controller.requiresEncryptedWebVault, isFalse);
    expect(controller.activeScope, isNull);
    expect(controller.activeDatabase, isNull);
  });

  for (final locale in const [Locale('fr'), Locale('en'), Locale('ar')]) {
    testWidgets('D1 safe hold is data-free, localized and can sign out: '
        '${locale.languageCode}', (tester) async {
      var signOutCalls = 0;
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(MaterialApp(
        home: WebPatientVaultSafeHold(
          locale: locale,
          onSignOut: () => signOutCalls++,
        ),
      ));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('d1-web-patient-vault-safe-hold')),
          findsOneWidget);
      expect(find.byKey(const Key('d1-web-safe-hold-heading')),
          findsOneWidget);
      expect(find.byKey(const Key('d1-web-safe-hold-explanation')),
          findsOneWidget);
      expect(find.textContaining('734'), findsNothing);
      expect(find.byKey(const Key('d1-web-safe-hold-signout')),
          findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.tap(find.byKey(const Key('d1-web-safe-hold-signout')));
      expect(signOutCalls, 1);
    });
  }

  testWidgets('D1 desktop safe-hold heading and text expose accessibility',
      (tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    final semantics = tester.ensureSemantics();
    addTearDown(semantics.dispose);
    await tester.pumpWidget(MaterialApp(
      home: WebPatientVaultSafeHold(
        locale: const Locale('en'),
        onSignOut: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.bySemanticsLabel('Patient vault unavailable'),
        findsOneWidget);
    expect(
      find.bySemanticsLabel(
        RegExp('Encrypted Web patient storage has not yet been verified'),
      ),
      findsWidgets,
    );
    expect(tester.takeException(), isNull);
  });

}
