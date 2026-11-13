import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D1 P0 Web refuses native and device patient vaults before SQLite', () {
    final native = PatientVaultScope.nativeDjango(734);
    final device = PatientVaultScope.deviceLocal(
      'b32afafd-8d9d-4ad4-8513-7dcfb54299a6',
    );
    if (kIsWeb) {
      for (final scope in [native, device]) {
        expect(
          () => AppDatabase.forPatientVault(scope),
          throwsA(
            isA<StateError>().having(
              (error) => error.message,
              'message',
              'web_patient_vault_encryption_not_verified',
            ),
          ),
        );
      }
    } else {
      // Only the Web patient storage path is denied by this change.
      expect(kIsWeb, isFalse);
    }
  });

  test('D1 P0 synthetic guest audit namespace is distinct from patients', () {
    // Policy-only assertion: constructing/closing Drift would try to load
    // sqlite3.wasm from the Flutter test runner, which does not serve it.
    // The independent TD-014 browser FUE covers the real guest/login route.
    final audit = PatientVaultScope.auditOnly().databaseName;
    expect(audit, 'amina_vault_v1_audit');
    expect(audit, isNot(PatientVaultScope.nativeDjango(734).databaseName));
    expect(
      audit,
      isNot(
        PatientVaultScope.deviceLocal(
          'b32afafd-8d9d-4ad4-8513-7dcfb54299a6',
        ).databaseName,
      ),
    );
  });

  test('D1 P0 Web denies both app-lock opt-out methods immediately', () async {
    final lock = AppLockService();
    addTearDown(lock.dispose);
    expect(lock.canOptOutOfAppLock, !kIsWeb);
    if (!kIsWeb) return;
    final refusal = isA<AppLockException>().having(
      (error) => error.code,
      'code',
      'web_encrypted_vault_required',
    );
    await expectLater(lock.continueWithoutAppLock(), throwsA(refusal));
    await expectLater(lock.disableForCurrentVault(), throwsA(refusal));
    expect(lock.isExplicitlySkipped, isFalse);
    expect(lock.isUnlocked, isFalse);
  });
}
