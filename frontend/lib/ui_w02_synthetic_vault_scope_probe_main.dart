// W02 CI-only browser boundary probe. Synthetic IDs and fake glucose values.
// Proves physical Drift IndexedDB vault isolation across navigation/reload,
// NOT real authentication, encryption, key recovery or a patient release gate.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart';

const _scopeA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const _scopeB = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const _fixtureA = 'w02-local-a-physical-vault-synthetic';
const _fixtureB = 'w02-local-b-physical-vault-synthetic';

Future<void> main() async {
  final phase = Uri.base.queryParameters['phase'] ?? 'invalid';
  html.document.title = 'IAMINA_W02_PENDING';
  AppDatabase? db;
  try {
    final isA = phase == 'seed_a' || phase == 'verify_a';
    if (!{'seed_a', 'seed_b', 'verify_a', 'verify_b'}.contains(phase)) {
      throw StateError('invalid synthetic W02 phase');
    }
    final scope = PatientVaultScope.deviceLocal(isA ? _scopeA : _scopeB);
    db = AppDatabase.forPatientVault(scope);
    await db.customSelect('SELECT 1').getSingle();

    Future<void> ensureAbsent(String uuid) async {
      final wrong = await (db!.select(
        db.logEntries,
      )..where((entry) => entry.clientUuid.equals(uuid))).getSingleOrNull();
      if (wrong != null) {
        throw StateError('cross vault fixture unexpectedly visible');
      }
    }

    Future<void> ensurePresent(String uuid, double value) async {
      final owned = await (db!.select(
        db.logEntries,
      )..where((entry) => entry.clientUuid.equals(uuid))).getSingleOrNull();
      if (owned == null || owned.bloodSugar != value) {
        throw StateError('owned vault fixture missing or changed');
      }
    }

    if (phase == 'seed_a' || phase == 'seed_b') {
      final uuid = isA ? _fixtureA : _fixtureB;
      final foreign = isA ? _fixtureB : _fixtureA;
      await ensureAbsent(foreign);
      await (db.delete(
        db.logEntries,
      )..where((entry) => entry.clientUuid.equals(uuid))).go();
      await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.utc(2026, 10, 16, 8),
          bloodSugar: isA ? 111.0 : 222.0,
          clientUuid: uuid,
          syncStatus: const Value('pending'),
        ),
      );
      await ensurePresent(uuid, isA ? 111.0 : 222.0);
    } else {
      await ensureAbsent(isA ? _fixtureB : _fixtureA);
      await ensurePresent(isA ? _fixtureA : _fixtureB, isA ? 111.0 : 222.0);
    }

    await db.close();
    html.document.title = 'IAMINA_W02_${phase.toUpperCase()}_PASS';
  } catch (error) {
    if (db != null) {
      try {
        await db.close();
      } catch (_) {
        // Original probe failure takes precedence.
      }
    }
    html.document.title = 'IAMINA_W02_FAIL:${error.runtimeType}';
  }
}
