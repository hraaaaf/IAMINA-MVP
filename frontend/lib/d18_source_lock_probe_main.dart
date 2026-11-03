// D18 CI-only standalone Dart Web probe: uses the actual app Dart source-lock bridge.
// Synthetic namespaces, no patient DB, no migration or clinical UI.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:async';
import 'dart:html' as html;

import 'data/drift/d18_source_lock_gate.dart';
import 'data/drift/d18_source_lock_lease.dart';
import 'data/drift/patient_vault_scope.dart';

Future<void> main() async {
  // CI-only Dart→Web Locks bridge proof: never bootstrap the Flutter renderer.
  // The app's real Web/UI is validated by independent browser workflows.
  final phase = Uri.base.queryParameters['phase'] ?? '';
  try {
    late final D18SourceLockLease lease;
    switch (phase) {
      case 'legacy':
        lease = await D18SourceLockGate.legacy();
        break;
      case 'a':
        lease = await D18SourceLockGate.patient(
          PatientVaultScope.nativeDjango(734));
        break;
      case 'b':
        lease = await D18SourceLockGate.patient(
          PatientVaultScope.nativeDjango(812));
        break;
      case 'audit_guest':
        lease = await D18SourceLockGate.auditGuest();
        break;
      case 'audit_denied':
        lease = await D18SourceLockGate.patient(PatientVaultScope.auditOnly());
        break;
      default:
        throw StateError('D18_PROBE_INVALID_PHASE');
    }
    html.window.onMessage.listen((event) {
      if (event.origin != html.window.location.origin ||
          event.data != 'D18_SOURCE_RELEASE') return;
      unawaited(() async {
        try {
          await lease.close();
          html.document.title = 'D18_SOURCE_DART_RELEASED:' + phase;
        } catch (e) {
          html.document.documentElement?.dataset['d18SourceError'] =
              e.runtimeType.toString();
          html.document.title = 'D18_SOURCE_DART_FAIL:' + phase;
        }
      }());
    });
    html.document.title = 'D18_SOURCE_DART_HELD:' + phase;
  } catch (e) {
    html.document.documentElement?.dataset['d18SourceError'] =
        e.runtimeType.toString();
    html.document.title = 'D18_SOURCE_DART_FAIL:' + phase;
  }
}
