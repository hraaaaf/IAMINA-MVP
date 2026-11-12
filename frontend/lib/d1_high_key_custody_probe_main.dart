// D1 High CI-only real Drift SQLite3MC admission with device-wrapped DEK.
// No real login, app data, patient tokens or production main.dart.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';

import 'package:flutter/foundation.dart';
import 'data/drift/database.dart';
import 'data/drift/d1_web_vault_key_admission.dart';
import 'data/drift/patient_vault_scope.dart';

@JS('iaminaD1DeviceKeyCustody.create')
external JSPromise<JSObject> createJs(JSString owner);
@JS('iaminaD1DeviceKeyCustody.confirm')
external JSPromise<JSObject> confirmJs(JSString owner, JSString recovery);
@JS('iaminaD1DeviceKeyCustody.rebindDevice')
external JSPromise<JSObject> rebindJs(JSString owner, JSString recovery);

final class _Changes extends ChangeNotifier {
  void change() => notifyListeners();
}

final a = PatientVaultScope.nativeDjango(731);
final b = PatientVaultScope.nativeDjango(812);

Future<void> main() async {
  html.document.title = 'D1_KEY_AUTH_RUNNING';
  var phase = 'START';
  var epoch = 31;
  var owner = a;
  var authenticated = true;
  var unlocked = false;
  final auth = _Changes(), lock = _Changes();
  final coordinator = D1WebVaultKeySessionCoordinator(
    authChanges: auth,
    appLockChanges: lock,
    resolveOwner: () async => owner,
    currentAuthEpoch: () => epoch,
    isAuthenticated: () => authenticated,
    isUnlocked: () => unlocked,
  );
  try {
    phase = 'CREATE';
    final ca = await createJs(a.databaseName.toJS).toDart;
    final cb = await createJs(b.databaseName.toJS).toDart;
    final recoveryA = (ca['recoveryKey'] as JSString).toDart;
    final recoveryB = (cb['recoveryKey'] as JSString).toDart;

    phase = 'LOCKED';
    var denied = false;
    try { await coordinator.admitAfterUnlock(); } catch (_) { denied = true; }
    if (!denied || coordinator.activeDatabase != null) {
      throw StateError('LOCKED_ACCOUNT_COULD_OPEN');
    }

    unlocked = true;
    lock.change();
    phase = 'UNCONFIRMED';
    denied = false;
    try { await coordinator.admitAfterUnlock(); } catch (_) { denied = true; }
    if (!denied || coordinator.activeDatabase != null) {
      throw StateError('UNCONFIRMED_RECOVERY_ALLOWED');
    }

    phase = 'CONFIRM';
    await confirmJs(a.databaseName.toJS, recoveryA.toJS).toDart;
    await confirmJs(b.databaseName.toJS, recoveryB.toJS).toDart;

    phase = 'OPEN_A';
    await coordinator.admitAfterUnlock();
    if (coordinator.activeScope?.databaseName != a.databaseName) {
      throw StateError('WRONG_OWNER_A');
    }
    final dbA = coordinator.activeDatabase!;
    await dbA.into(dbA.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.utc(2026, 11, 12),
      bloodSugar: 117,
      clientUuid: 'D1_A_KEYED_CIPHERTEXT_ROW_731',
    ));

    phase = 'LOCK_REVOKE';
    unlocked = false;
    lock.change();
    if (coordinator.activeDatabase != null || coordinator.hasVault) {
      throw StateError('UNLOCK_REVOKE_NOT_IMMEDIATE');
    }
    await coordinator.revokeAndFlush();

    phase = 'ACCOUNT_B';
    owner = b;
    epoch++;
    auth.change();
    unlocked = true;
    lock.change();
    await coordinator.admitAfterUnlock();
    final dbB = coordinator.activeDatabase!;
    if ((await dbB.getRecentLogs()).isNotEmpty) {
      throw StateError('A_DATA_LEAKED_TO_B');
    }
    await dbB.into(dbB.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.utc(2026, 11, 12),
      bloodSugar: 87,
      clientUuid: 'D1_B_KEYED_CIPHERTEXT_ROW_812',
    ));
    phase = 'ACCOUNT_A_REOPEN';
    owner = a;
    epoch++;
    auth.change();
    await coordinator.revokeAndFlush();
    await coordinator.admitAfterUnlock();
    final dbAgainA = coordinator.activeDatabase!;
    final rowsA = await dbAgainA.getRecentLogs();
    if (rowsA.length != 1 ||
        rowsA.single.clientUuid != 'D1_A_KEYED_CIPHERTEXT_ROW_731') {
      throw StateError('A_B_A_KEYED_REOPEN_FAILED');
    }

    phase = 'LOGOUT';
    authenticated = false;
    epoch++;
    auth.change();
    if (coordinator.activeDatabase != null) {
      throw StateError('AUTH_LOGOUT_DID_NOT_REVOKE');
    }
    await coordinator.revokeAndFlush();
    denied = false;
    try { await coordinator.admitAfterUnlock(); } catch (_) { denied = true; }
    if (!denied) throw StateError('LOGOUT_KEY_ACCESS_ALLOWED');

    // Device-local KEK is rewrapped from the patient-held high-entropy key
    // AFTER all workers have fully closed; the original DEK stays unchanged.
    phase = 'RECOVER_DEVICE';
    await rebindJs(a.databaseName.toJS, recoveryA.toJS).toDart;
    authenticated = true;
    unlocked = true;
    auth.change();
    lock.change();
    await coordinator.admitAfterUnlock();
    final last = await coordinator.activeDatabase!.getRecentLogs();
    if (last.length != 1 ||
        last.single.clientUuid != 'D1_A_KEYED_CIPHERTEXT_ROW_731') {
      throw StateError('RECOVERY_REBIND_CHANGED_DATABASE_KEY');
    }
    phase = 'CLOSE';
    await coordinator.revokeAndFlush();
    html.document.title = 'D1_KEY_AUTH_PASS';
  } catch (_) {
    html.document.title = 'D1_KEY_AUTH_FAIL_$phase';
  } finally {
    coordinator.dispose();
    auth.dispose();
    lock.dispose();
  }
}
