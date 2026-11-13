import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/web_vault_explicit_admission.dart';
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

class _Signals extends ChangeNotifier {
  void changed() => notifyListeners();
}

class _CloseObservedDatabase extends AppDatabase {
  _CloseObservedDatabase(PatientVaultScope scope)
      : super.testPatientVault(NativeDatabase.memory(), scope);

  bool closeCalled = false;

  @override
  Future<void> close() async {
    closeCalled = true;
    await super.close();
  }
}

WebVaultAdmissionIdentity _validNative({
  bool authenticated = true,
  bool lockReady = true,
  bool unlocked = true,
  bool verified = true,
  int? nativeId = 734,
}) => (
  authenticated: authenticated,
  appLockInitialized: lockReady,
  appLockConfigured: lockReady,
  appLockUnlocked: unlocked,
  appLockRecoveryRequired: false,
  remoteCredentialVerified: verified,
  hasRemoteCredential: verified,
  nativeAccountId: nativeId,
);

void main() {
  final a = PatientVaultScope.nativeDjango(734);
  final b = PatientVaultScope.nativeDjango(812);

  test('D1 never opens with missing recovery, missing lock, or old bearer',
      () async {
    final changes = _Signals();
    addTearDown(changes.dispose);
    var state = _validNative();
    var opens = 0;
    var epoch = 0;
    final gate = WebVaultExplicitAdmission(
      sessionChanges: changes,
      identity: () => state,
      resolveScope: () async => a,
      authEpoch: () => epoch,
      encryptedOpener: (scope, code) async {
        opens++;
        return AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
      },
    );
    addTearDown(gate.dispose);

    Future<void> rejects(String code, String recovery) async {
      await expectLater(
        gate.openWithExplicitRecovery(scope: a, recoveryCode: recovery),
        throwsA(isA<StateError>().having(
          (e) => e.message, 'code', code,
        )),
      );
    }

    await rejects('web_vault_explicit_recovery_required', '');
    state = _validNative(unlocked: false);
    changes.changed();
    await rejects('web_vault_identity_or_app_lock_required', 'fake-recovery');
    state = _validNative(lockReady: false);
    changes.changed();
    await rejects('web_vault_identity_or_app_lock_required', 'fake-recovery');
    state = _validNative(verified: false);
    changes.changed();
    await rejects('web_vault_verified_native_owner_required', 'fake-recovery');
    state = _validNative(nativeId: 812);
    changes.changed();
    await rejects('web_vault_verified_native_owner_required', 'fake-recovery');
    state = _validNative(authenticated: false);
    changes.changed();
    await rejects('web_vault_identity_or_app_lock_required', 'fake-recovery');
    expect(opens, 0);
    expect(epoch, 0);
  });

  test('D1 owner B can never unwrap owner A through resolved scope mismatch',
      () async {
    final changes = _Signals();
    addTearDown(changes.dispose);
    var openerCalled = false;
    final gate = WebVaultExplicitAdmission(
      sessionChanges: changes,
      identity: () => _validNative(),
      resolveScope: () async => b,
      authEpoch: () => 7,
      encryptedOpener: (scope, code) async {
        openerCalled = true;
        return AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
      },
    );
    addTearDown(gate.dispose);

    await expectLater(
      gate.openWithExplicitRecovery(scope: a, recoveryCode: 'fake-recovery'),
      throwsA(isA<StateError>().having(
        (e) => e.message, 'code', 'web_vault_authenticated_scope_mismatch',
      )),
    );
    expect(openerCalled, isFalse);
  });

  test('D1 revokes a pending owner-A WebCrypto open on logout/app lock event',
      () async {
    final changes = _Signals();
    addTearDown(changes.dispose);
    var state = _validNative();
    var epoch = 12;
    final pending = Completer<AppDatabase>();
    final entered = Completer<void>();
    final gate = WebVaultExplicitAdmission(
      sessionChanges: changes,
      identity: () => state,
      resolveScope: () async => a,
      authEpoch: () => epoch,
      encryptedOpener: (scope, code) {
        entered.complete();
        return pending.future;
      },
    );
    addTearDown(gate.dispose);

    final attempt = gate.openWithExplicitRecovery(
      scope: a, recoveryCode: 'fake-recovery',
    );
    await entered.future;

    // Reject a second concurrent attempt instead of racing two tab-local
    // sessions against the same key and mutable IndexedDB state.
    await expectLater(
      gate.openWithExplicitRecovery(scope: a, recoveryCode: 'fake-recovery'),
      throwsA(isA<StateError>().having(
        (e) => e.message, 'code', 'web_vault_admission_already_pending',
      )),
    );

    state = _validNative(nativeId: 812, unlocked: false);
    epoch++;
    changes.changed();
    final stale = _CloseObservedDatabase(a);
    pending.complete(stale);
    await expectLater(
      attempt,
      throwsA(isA<StateError>().having(
        (e) => e.message, 'code', 'web_vault_admission_revoked',
      )),
    );
    // A NativeDatabase may lazily reopen when a test retains its executor.
    // Query-after-close is NOT a valid close oracle for Drift. Observe the
    // actual close() invocation and the rejected Future instead.
    expect(stale.closeCalled, isTrue);
  });

  test('D1 non-clinical grant requires explicit code, same owner, and lock',
      () async {
    final changes = _Signals();
    addTearDown(changes.dispose);
    var state = _validNative();
    var supplied = '';
    var epoch = 4;
    final gate = WebVaultExplicitAdmission(
      sessionChanges: changes,
      identity: () => state,
      resolveScope: () async => a,
      authEpoch: () => epoch,
      encryptedOpener: (scope, code) async {
        supplied = code;
        return AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
      },
    );
    addTearDown(gate.dispose);

    final opened = await gate.openWithExplicitRecovery(
      scope: a, recoveryCode: 'user-entered-once',
    );
    expect(opened.patientVaultScope?.databaseName, a.databaseName);
    expect(supplied, 'user-entered-once');
    await opened.close();

    // The policy never cached a recovery key: reopening requires the caller
    // to explicitly supply it again.
    await expectLater(
      gate.openWithExplicitRecovery(scope: a, recoveryCode: ''),
      throwsA(isA<StateError>()),
    );
    state = _validNative(unlocked: false);
    epoch++;
    changes.changed();
    await expectLater(
      gate.openWithExplicitRecovery(scope: a, recoveryCode: 'user-entered-once'),
      throwsA(isA<StateError>()),
    );
  });
}
