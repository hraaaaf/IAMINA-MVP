import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> vault(int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 13),
      diabetesType: const drift.Value('type2'),
      treatment: const drift.Value('tablets'),
    ),
  );
  return db;
}

void main() {
  test('D7 local independent vaults roundtrip combined patient choices', () async {
    final a = await vault(734);
    final b = await vault(812);
    addTearDown(a.close);
    addTearDown(b.close);

    final aStore = PatientTreatmentDeclarationStore(a);
    final bStore = PatientTreatmentDeclarationStore(b);
    expect(await aStore.read(), isNull);
    expect(await bStore.read(), isNull);

    await aStore.write(
      state: 'declared', codes: ['oral_meds', 'insulin', 'lifestyle'],
    );
    final aValue = await aStore.read();
    expect(aValue?.ownerId, 734);
    expect(aValue?.version, 1);
    expect(aValue?.provenance, 'patient_declared');
    expect(aValue?.codes, ['oral_meds', 'insulin', 'lifestyle']);
    expect(aValue?.updatedAtUtc.isUtc, isTrue);
    expect(await bStore.read(), isNull);

    // Old clinical readers retain the original value; no guessed promotion.
    expect((await a.getProfileForLocalUserId(734))?.treatment, 'tablets');
    expect((await b.getProfileForLocalUserId(812))?.treatment, 'tablets');

    await bStore.write(state: 'unsure', codes: []);
    expect((await bStore.read())?.state, 'unsure');
    expect((await aStore.read())?.codes, hasLength(3));
  });

  test('D7 null, unsure, none and later are independent statements', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    expect(await store.read(), isNull); // no statement exists
    for (final state in ['not_answered','unsure','none_declared']) {
      await store.write(state: state, codes: []);
      expect((await store.read())?.state, state);
      expect((await store.read())?.codes, isEmpty);
    }
  });

  test('D7 invalid codes cannot mutate an existing declaration', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['insulin']);
    for (final codes in [
      ['insulin', 'insulin'], ['not-real'], <String>[],
    ]) {
      await expectLater(
        store.write(state: 'declared', codes: codes),
        throwsArgumentError,
      );
    }
    await expectLater(
      store.write(state: 'unsure', codes: ['insulin']),
      throwsArgumentError,
    );
    expect((await store.read())?.codes, ['insulin']);
  });

  test('D7 legacy mixed database cannot claim newly declared treatment', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(1),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 10, 13),
        treatment: const drift.Value('insulin'),
      ),
    );
    expect(() => PatientTreatmentDeclarationStore(db), throwsStateError);
    final rows = await db.customSelect(
      'SELECT * FROM patient_treatment_declarations_v1',
    ).get();
    expect(rows, isEmpty);
  });

  test('D7 new native device restores only its own declared treatments', () async {
    final a = await vault(734);
    final b = await vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    final aStore = PatientTreatmentDeclarationStore(a);
    final bStore = PatientTreatmentDeclarationStore(b);
    final recorded = DateTime.utc(2026, 10, 13, 14);
    expect(await aStore.restoreRemoteIfAbsent(
      state: 'declared', codes: ['insulin', 'lifestyle'],
      updatedAtUtc: recorded,
    ), isTrue);
    expect((await aStore.read())?.codes, ['insulin', 'lifestyle']);
    expect((await aStore.read())?.updatedAtUtc, recorded);
    expect(await bStore.read(), isNull);
  });

  test('D7 late server snapshot cannot overwrite local offline edit', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['oral_meds']);
    expect(await store.restoreRemoteIfAbsent(
      state: 'declared', codes: ['insulin'],
      updatedAtUtc: DateTime.utc(2026, 10, 13),
    ), isFalse);
    expect((await store.read())?.codes, ['oral_meds']);
  });

  test('D7 invalid server snapshot rejected without mutation', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await expectLater(store.restoreRemoteIfAbsent(
      state: 'declared', codes: ['insulin', 'insulin'],
      updatedAtUtc: DateTime.utc(2026, 10, 13),
    ), throwsArgumentError);
    expect(await store.read(), isNull);
  });

  test('D7 local edits stay pending until matching-generation server ack', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle']);
    final first = (await store.read())!;
    expect(first.syncStatus, 'pending');
    expect(first.baseServerUpdatedAtUtc, isNull);
    expect(first.localGeneration, 1);
    final serverTime = DateTime.utc(2026, 10, 13, 15);
    await store.write(state: 'declared', codes: ['lifestyle', 'oral_meds']);
    expect(await store.acknowledgeIfUnchanged(
      expectedGeneration: first.localGeneration,
      serverUpdatedAtUtc: serverTime,
    ), isFalse);
    final second = (await store.read())!;
    expect(second.syncStatus, 'pending');
    expect(second.localGeneration, 2);
    expect(await store.acknowledgeIfUnchanged(
      expectedGeneration: second.localGeneration,
      serverUpdatedAtUtc: serverTime,
    ), isTrue);
    final confirmed = (await store.read())!;
    expect(confirmed.syncStatus, 'confirmed');
    expect(confirmed.baseServerUpdatedAtUtc, serverTime);
    await store.write(state: 'declared', codes: ['insulin']);
    final third = (await store.read())!;
    expect(third.localGeneration, 3);
    expect(third.syncStatus, 'pending');
    expect(third.baseServerUpdatedAtUtc, serverTime);
  });

  test('D7 conflict persists until explicit reconciliation, without data loss', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle']);
    final first = (await store.read())!;
    expect(await store.markConflictIfUnchanged(first.localGeneration), isTrue);
    expect((await store.read())?.syncStatus, 'conflict');
    expect(await store.acknowledgeIfUnchanged(
      expectedGeneration: first.localGeneration,
      serverUpdatedAtUtc: DateTime.utc(2026, 10, 13),
    ), isFalse);
    await store.write(state: 'declared', codes: ['lifestyle', 'insulin']);
    final second = (await store.read())!;
    expect(second.syncStatus, 'conflict');
    expect(second.codes, ['lifestyle', 'insulin']);
    expect(second.localGeneration, first.localGeneration + 1);
  });

  test('D7 restored native snapshot begins confirmed with server revision', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    final timestamp = DateTime.utc(2026, 10, 13, 14);
    expect(await store.restoreRemoteIfAbsent(
      state: 'declared', codes: ['lifestyle'], updatedAtUtc: timestamp,
    ), isTrue);
    final restored = (await store.read())!;
    expect(restored.syncStatus, 'confirmed');
    expect(restored.localGeneration, 1);
    expect(restored.baseServerUpdatedAtUtc, timestamp);
    expect(restored.codes, ['lifestyle']);
  });

  test('D7 storage remains queryable after JSON encoding of treatment codes', () async {
    final db = await vault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle','oral_meds']);
    final raw = await db.customSelect(
      'SELECT codes_json FROM patient_treatment_declarations_v1',
    ).getSingle();
    expect(jsonDecode(raw.data['codes_json'] as String), ['lifestyle','oral_meds']);
    expect((await db.customSelect('PRAGMA user_version').getSingle())
        .data['user_version'], 12);
  });
}
