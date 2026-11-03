import 'dart:async';

// D18 pre-cutover source interlock (disabled for clinical runtime by default).
// This is cooperative: it cannot stop older cached tabs without Web Locks.
import 'patient_vault_scope.dart';
import 'd18_source_lock_lease.dart';
import 'd18_source_lock_stub.dart'
    if (dart.library.js_interop) 'd18_source_lock_web.dart' as browser;

abstract final class D18SourceLockGate {
  static Future<D18SourceLockLease> legacy() => browser.acquireLegacy();

  static Future<D18SourceLockLease> patient(PatientVaultScope scope) =>
      browser.acquirePatient(scope.databaseName);
}
