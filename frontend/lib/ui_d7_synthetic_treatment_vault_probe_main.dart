// D7 CI-only browser proof: synthetic patient-declared treatments in two
// physical IndexedDB vaults. NOT an IAMINA patient UI, auth, or clinical release.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;

const _a = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc';
const _b = 'dddddddd-dddd-4ddd-8ddd-dddddddddddd';
const _aCodes = ['oral_meds', 'insulin'];
const _bCodes = ['lifestyle'];

Future<void> main() async {
  final phase = Uri.base.queryParameters['phase'] ?? 'invalid';
  html.document.title = 'IAMINA_D7_PENDING';
  AppDatabase? db;
  try {
    const phases = {
      'seed_a', 'seed_b', 'verify_a', 'verify_b', 'edit_a',
      'verify_a_edited', 'none_b', 'verify_b_none',
    };
    if (!phases.contains(phase)) {
      throw StateError('Unsupported D7 browser proof phase');
    }
    final isA = {'seed_a', 'verify_a', 'edit_a', 'verify_a_edited'}
        .contains(phase);
    final scope = PatientVaultScope.deviceLocal(isA ? _a : _b);
    final vault = AppDatabase.forPatientVault(scope);
    db = vault;
    await vault.customSelect('SELECT 1').getSingle();

    final store = PatientTreatmentDeclarationStore(vault);
    final profile = await vault.getProfileForLocalUserId(vault.activeProfileRowId);
    final declaration = await store.read();

    Future<void> expectDeclaration({
      required String expectedType,
      required String expectedState,
      required List<String> expectedCodes,
      required int expectedGeneration,
    }) async {
      final ownedProfile = await vault.getProfileForLocalUserId(
        vault.activeProfileRowId,
      );
      final ownedDeclaration = await store.read();
      if (ownedProfile?.diabetesType != expectedType ||
          ownedDeclaration?.ownerId != vault.activeProfileRowId ||
          ownedDeclaration?.state != expectedState ||
          ownedDeclaration?.codes.join(',') != expectedCodes.join(',') ||
          ownedDeclaration?.localGeneration != expectedGeneration ||
          ownedDeclaration?.syncStatus != 'pending' ||
          ownedDeclaration?.provenance != 'patient_declared') {
        throw StateError('D7 owned declaration missing or mutated');
      }
    }

    if (phase == 'seed_a' || phase == 'seed_b') {
      // A new physical vault must not inherit another patient's declaration.
      if (profile != null || declaration != null) {
        throw StateError('D7 fresh vault has unexpected records');
      }
      await vault.into(vault.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: drift.Value(vault.activeProfileRowId),
          updatedAt: DateTime.utc(2026, 10, 29),
          diabetesType: drift.Value(isA ? 'type2' : 'type1'),
        ),
      );
      await store.write(
        state: 'declared',
        codes: isA ? _aCodes : _bCodes,
      );
      await expectDeclaration(
        expectedType: isA ? 'type2' : 'type1',
        expectedState: 'declared',
        expectedCodes: isA ? _aCodes : _bCodes,
        expectedGeneration: 1,
      );
    } else if (phase == 'verify_a') {
      await expectDeclaration(
        expectedType: 'type2', expectedState: 'declared',
        expectedCodes: _aCodes, expectedGeneration: 1,
      );
    } else if (phase == 'verify_b') {
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'declared',
        expectedCodes: _bCodes, expectedGeneration: 1,
      );
    } else if (phase == 'edit_a') {
      // Changing the diagnosed TYPE must not rewrite treatments, even across
      // real page navigation and physical browser-backed vault reopening.
      await expectDeclaration(
        expectedType: 'type2', expectedState: 'declared',
        expectedCodes: _aCodes, expectedGeneration: 1,
      );
      await (vault.update(vault.patientProfiles)
            ..where((row) => row.userId.equals(vault.activeProfileRowId)))
          .write(const PatientProfilesCompanion(
            diabetesType: drift.Value('type1'),
          ));
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'declared',
        expectedCodes: _aCodes, expectedGeneration: 1,
      );
    } else if (phase == 'verify_a_edited') {
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'declared',
        expectedCodes: _aCodes, expectedGeneration: 1,
      );
    } else if (phase == 'none_b') {
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'declared',
        expectedCodes: _bCodes, expectedGeneration: 1,
      );
      // This simulates an explicitly patient-initiated choice; no
      // diagnosis-based prescribing/inference occurs.
      await store.write(state: 'none_declared', codes: const []);
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'none_declared',
        expectedCodes: const [], expectedGeneration: 2,
      );
    } else if (phase == 'verify_b_none') {
      await expectDeclaration(
        expectedType: 'type1', expectedState: 'none_declared',
        expectedCodes: const [], expectedGeneration: 2,
      );
    }
    await vault.close();
    html.document.title = 'IAMINA_D7_${phase.toUpperCase()}_PASS';
  } catch (error) {
    if (db != null) {
      try {
        await db.close();
      } catch (_) {
        // Preserve the original failure.
      }
    }
    html.document.title = 'IAMINA_D7_FAIL:${error.runtimeType}';
  }
}
