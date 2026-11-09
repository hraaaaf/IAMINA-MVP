// CI-only real controller+physical IndexedDB A-B-A; FAKE principal, NO real login.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/foundation.dart';

const a = 734, b = 812;
void requireOk(bool test) { if (!test) throw StateError('D7 scoped vault check failed'); }

class FakePrincipal extends ChangeNotifier {
  int? id;
  FakePrincipal(this.id);
  void select(int? next) { AuthEpoch.advance(); id = next; notifyListeners(); }
}
Future<void> verify(AppDatabase db, int id, String type, List<String> codes) async {
  final rows = await db.select(db.patientProfiles).get();
  requireOk(rows.length == 1);
  requireOk(rows.single.userId == id && rows.single.diabetesType == type);
  final d = await PatientTreatmentDeclarationStore(db).read();
  requireOk(d != null);
  requireOk(d!.ownerId == id && d.state == 'declared');
  requireOk(listEquals(d.codes, codes));
  requireOk(d.syncStatus == 'pending' && d.localGeneration == 1);
}
Future<void> seed(AppDatabase db, int id, String type, List<String> codes) async {
  requireOk((await db.select(db.patientProfiles).get()).isEmpty);
  requireOk(await PatientTreatmentDeclarationStore(db).read() == null);
  await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
    userId: drift.Value(id),
    updatedAt: DateTime.utc(2026, 10, 29),
    diabetesType: drift.Value(type),
  ));
  await PatientTreatmentDeclarationStore(db).write(state: 'declared', codes: codes);
  await verify(db, id, type, codes);
}
Future<void> main() async {
  final phase = Uri.base.queryParameters['phase'] ?? '';
  html.document.title = 'IAMINA_D7_CTRL_PENDING';
  const phases = {'seed_a', 'seed_b', 'verify_a', 'verify_b', 'edit_a',
                  'verify_a_edited', 'switch_a_b_a'};
  if (!phases.contains(phase)) {
    html.document.title = 'IAMINA_D7_CTRL_FAIL:invalid_phase';
    return;
  }
  final fake = FakePrincipal(
      phase == 'seed_b' || phase == 'verify_b' ? b : a);
  final controller = PatientVaultSessionController(
    authChanges: fake,
    resolveScope: () async => fake.id == null
        ? null : PatientVaultScope.nativeDjango(fake.id!),
  );
  try {
    await controller.reconcile();
    AppDatabase active() {
      final db = controller.activeDatabase;
      requireOk(db != null && db.activeProfileRowId == fake.id);
      return db!;
    }
    if (phase == 'seed_a') {
      await seed(active(), a, 'type2', ['oral_meds', 'lifestyle']);
    } else if (phase == 'seed_b') {
      await seed(active(), b, 'type1', ['insulin']);
    } else if (phase == 'verify_a') {
      await verify(active(), a, 'type2', ['oral_meds', 'lifestyle']);
    } else if (phase == 'verify_b') {
      await verify(active(), b, 'type1', ['insulin']);
    } else if (phase == 'edit_a') {
      await verify(active(), a, 'type2', ['oral_meds', 'lifestyle']);
      final db = active();
      await (db.update(db.patientProfiles)
          ..where((p) => p.userId.equals(a))).write(
          const PatientProfilesCompanion(diabetesType: drift.Value('type1')));
      await verify(active(), a, 'type1', ['oral_meds', 'lifestyle']);
    } else if (phase == 'verify_a_edited') {
      await verify(active(), a, 'type1', ['oral_meds', 'lifestyle']);
    } else if (phase == 'switch_a_b_a') {
      await verify(active(), a, 'type1', ['oral_meds', 'lifestyle']);
      final before = active();
      fake.select(b);
      requireOk(controller.activeDatabase == null);
      await controller.reconcile();
      requireOk(!identical(active(), before));
      await verify(active(), b, 'type1', ['insulin']);
      fake.select(null);
      requireOk(controller.activeDatabase == null);
      await controller.reconcile();
      requireOk(controller.activeScope == null && !controller.hasVault);
      fake.select(a);
      requireOk(controller.activeDatabase == null);
      await controller.reconcile();
      await verify(active(), a, 'type1', ['oral_meds', 'lifestyle']);
    }
    html.document.title = 'IAMINA_D7_CTRL_' + phase.toUpperCase() + '_PASS';
  } catch (e) {
    html.document.title = 'IAMINA_D7_CTRL_FAIL:' + e.runtimeType.toString();
  } finally {
    controller.dispose();
    fake.dispose();
  }
}
