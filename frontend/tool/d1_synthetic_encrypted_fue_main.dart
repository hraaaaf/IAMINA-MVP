// IAMINA D1 CI-only Flutter Web entrypoint for D7/D22 positive FUE.
// It renders the real PatientVaultAppHost, AminaApp, AppLock and production
// screens, but injects a synthetic-only encrypted SQLite3MC vault factory.
// Absolutely NOT an alternative production main.dart or a clinical GO.
// No real patients, remote accounts, legacy migration or provider egress.
import 'dart:async';
import 'dart:html' as html;

import 'package:flutter/material.dart';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/web_patient_vault_cipher_candidate.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/locale_preference_service.dart';
import 'package:amina/services/patient_vault_app_host.dart';
import 'package:amina/services/patient_vault_session_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Restrict test to loopback AND to an explicit CI-only URL fixture marker.
  // This is necessary but not sufficient for genuine patient admission;
  // the real application entrypoint never references this source.
  final uri = Uri.base;
  const fixtureEnabled = bool.fromEnvironment(
    'IAMINA_D1_SYNTHETIC_FUE', defaultValue: false,
  );
  if (!fixtureEnabled ||
      !({'localhost', '127.0.0.1', '::1'}.contains(uri.host))) {
    runApp(const MaterialApp(home: Scaffold(
      body: Center(child: Text('D1 synthetic FUE fixture disabled')),
    )));
    return;
  }

  final auth = AuthService();
  await auth.initialize();
  final lock = AppLockService(
    authService: auth,
    // Every CI browser context is disposable and starts clean. Never model
    // this initial-state oracle as a patient recovery policy.
    protectedLocalStateProbe: () async => false,
  );
  await lock.initialize();
  auth.addListener(lock.lock);

  final api = ApiClient(
    authService: auth,
    canUsePatientSyncTransport: () => false,
  );
  final locale = LocalePreferenceService(api)..refresh();
  final cipher = WebPatientVaultCipherCandidate();
  Future<AppDatabase> onlySyntheticCipher(PatientVaultScope scope) async {
    if (!auth.isAuthenticated ||
        scope.nativeDjangoUserId != null ||
        !scope.databaseName.startsWith('amina_vault_v1_device_')) {
      throw StateError('d1_ci_synthetic_local_owner_required');
    }
    final slot = 'iamina_d1_ci_fixture_recovery_${scope.databaseName}';
    var recovery = html.window.sessionStorage[slot];
    if (recovery == null) {
      final enrollment = await cipher.enrollEmptyScope(scope);
      recovery = enrollment.recoveryCode;
      // Disposable CI synthetic-only recovery material, never valid as a
      // patient secret storage mechanism. It is NOT output to logs/artifacts.
      html.window.sessionStorage[slot] = recovery;
    }
    final key = await cipher.unlock(scope, recovery);
    return cipher.openCandidateDatabase(scope, key);
  }

  final vault = PatientVaultSessionController(
    authChanges: auth,
    resolveScope: auth.resolvePatientVaultScope,
    openDatabase: onlySyntheticCipher,
  );
  await vault.reconcile();
  runApp(PatientVaultAppHost(
    auth: auth,
    api: api,
    appLock: lock,
    locale: locale,
    controller: vault,
    auditAllowed: false,
  ));
}
