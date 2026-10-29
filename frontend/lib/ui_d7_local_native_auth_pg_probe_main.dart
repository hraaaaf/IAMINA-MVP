// CI-only integration: actual AuthService/Django native login + scoped Web SQLite.
// Accounts, passwords, PostgreSQL and browser profile are ephemeral; NOT hosted FUE.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

const _a = String.fromEnvironment('D7_CI_A');
const _b = String.fromEnvironment('D7_CI_B');
const _password = String.fromEnvironment('D7_CI_PASS');

void must(bool ok) {
  if (!ok) throw StateError('Synthetic real-auth D7 contract failed');
}

Future<void> verify(AppDatabase db, int id, String type,
    List<String> codes) async {
  final rows = await db.select(db.patientProfiles).get();
  must(rows.length == 1 && rows.single.userId == id);
  must(rows.single.diabetesType == type);
  final d = await PatientTreatmentDeclarationStore(db).read();
  must(d != null && d.ownerId == id && d.state == 'declared');
  must(listEquals(d!.codes, codes));
  must(d.syncStatus == 'pending' && d.localGeneration == 1);
}

Future<void> seed(AppDatabase db, int id, String type,
    List<String> codes) async {
  must((await db.select(db.patientProfiles).get()).isEmpty);
  must(await PatientTreatmentDeclarationStore(db).read() == null);
  await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
    userId: drift.Value(id),
    updatedAt: DateTime.utc(2026, 10, 29),
    diabetesType: drift.Value(type),
  ));
  await PatientTreatmentDeclarationStore(db).write(
    state: 'declared', codes: codes,
  );
  await verify(db, id, type, codes);
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final phase = Uri.base.queryParameters['phase'] ?? '';
  html.document.title = 'IAMINA_D7_NATIVE_PENDING';
  const phases = {
    'seed_a', 'seed_b', 'verify_a', 'verify_b',
    'edit_a', 'verify_a_edited', 'switch_a_b_a',
  };
  if (!phases.contains(phase) ||
      _a.isEmpty || _b.isEmpty || _password.isEmpty ||
      _a == _b || !kIsWeb) {
    html.document.title = 'IAMINA_D7_NATIVE_FAIL:invalid_fixture';
    return;
  }

  final auth = AuthService();
  PatientVaultSessionController? controller;
  var completed = false;
  try {
    await auth.initialize();
    must(!auth.hasRemoteApiCredential);
    controller = PatientVaultSessionController.forAuth(auth);
    await controller.reconcile();
    must(controller.activeDatabase == null);

    Future<int> signIn(String email) async {
      await auth.signInWithEmail(email, _password);
      must(auth.hasRemoteApiCredential && auth.isRemoteCredentialVerified);
      final id = auth.boundNativeAccountId;
      must(id != null && id > 0);
      await controller!.reconcile();
      must(controller.activeScope?.nativeDjangoUserId == id);
      must(controller.activeDatabase?.activeProfileRowId == id);
      return id!;
    }

    AppDatabase current(int id) {
      final db = controller!.activeDatabase;
      must(db != null && db.activeProfileRowId == id);
      return db!;
    }

    final who = phase == 'seed_b' || phase == 'verify_b' ? _b : _a;
    final id = await signIn(who);

    if (phase == 'seed_a') {
      await seed(current(id), id, 'type2', ['oral_meds', 'lifestyle']);
    } else if (phase == 'seed_b') {
      await seed(current(id), id, 'type1', ['insulin']);
    } else if (phase == 'verify_a') {
      await verify(current(id), id, 'type2', ['oral_meds', 'lifestyle']);
    } else if (phase == 'verify_b') {
      await verify(current(id), id, 'type1', ['insulin']);
    } else if (phase == 'edit_a') {
      await verify(current(id), id, 'type2', ['oral_meds', 'lifestyle']);
      final db = current(id);
      await (db.update(db.patientProfiles)
          ..where((p) => p.userId.equals(id))).write(
          const PatientProfilesCompanion(diabetesType: drift.Value('type1')));
      await verify(current(id), id, 'type1', ['oral_meds', 'lifestyle']);
    } else if (phase == 'verify_a_edited') {
      await verify(current(id), id, 'type1', ['oral_meds', 'lifestyle']);
    } else if (phase == 'switch_a_b_a') {
      await verify(current(id), id, 'type1', ['oral_meds', 'lifestyle']);
      final old = current(id);
      final idB = await signIn(_b);
      must(id != idB && !identical(controller.activeDatabase, old));
      await verify(current(idB), idB, 'type1', ['insulin']);
      await auth.signOut();
      await controller.reconcile();
      must(!auth.hasRemoteApiCredential &&
          controller.activeDatabase == null &&
          controller.activeScope == null);
      final idAgain = await signIn(_a);
      must(idAgain == id);
      await verify(current(idAgain), idAgain, 'type1',
          ['oral_meds', 'lifestyle']);
    }

    completed = true;
  } catch (e) {
    html.document.title = 'IAMINA_D7_NATIVE_FAIL:' + e.runtimeType.toString();
  } finally {
    try {
      if (auth.hasRemoteApiCredential) await auth.signOut();
    } catch (_) {}
    controller?.dispose();
    auth.dispose();
  }
  if (completed) {
    html.document.title = 'IAMINA_D7_NATIVE_' + phase.toUpperCase() + '_PASS';
  }
}
