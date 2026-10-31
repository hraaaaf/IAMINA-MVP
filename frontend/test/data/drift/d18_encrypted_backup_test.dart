import 'dart:convert';

import 'package:amina/data/drift/d18_encrypted_backup.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

const _secret = 'iamina-test-backup-phrase-2026';
const _uuid1 = '3af99710-b61c-449d-b790-1abd12e68934';
const _uuid2 = '3af99710-b61c-449d-b790-1abd12e68935';
const _uuid3 = '3af99710-b61c-449d-b790-1abd12e68936';

AppDatabase _vault(int id) => AppDatabase.testPatientVault(
  NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('encrypted D18 backup restores only D18 within same patient scope', () async {
    final source = _vault(734), target = _vault(734);
    addTearDown(source.close);
    addTearDown(target.close);
    await PatientProgressiveDemographicsStore(source).update(
      updateBirthYear: true, birthYear: 1987,
      updateGenderIdentity: true, genderIdentity: 'woman',
    );
    await PatientWeightHistoryStore(source).append(
      clientUuid: _uuid1, value: '72.50', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 14, 8, 0),
    );
    final encrypted = await D18EncryptedBackup.exportEncrypted(
      source, passphrase: _secret,
    );
    final outer = jsonDecode(encrypted) as Map<String, dynamic>;
    expect(outer['format'], 'iamina-d18-encrypted');
    expect(outer.keys, isNot(contains('vault')));
    expect(encrypted, isNot(contains('1987')));
    expect(encrypted, isNot(contains('72.50')));
    final preview = await D18EncryptedBackup.open(
      encrypted, passphrase: _secret,
    );
    expect(preview.sourceOwner, 734);
    expect(preview.hasDemographics, true);
    expect(preview.observationCount, 1);
    await D18EncryptedBackup.restoreInto(target, preview);
    final details = await PatientProgressiveDemographicsStore(target).read();
    final history = await PatientWeightHistoryStore(target).recent();
    expect(details?.birthYear, 1987);
    expect(details?.genderIdentity, 'woman');
    expect(history.single.valueHundredths, 7250);
    expect(history.single.clientUuid, _uuid1);

    // No overwrite: retry must preserve a healthy existing target.
    await expectLater(
      D18EncryptedBackup.restoreInto(target, preview), throwsStateError,
    );
    expect((await PatientWeightHistoryStore(target).recent()).length, 1);
  });

  test('bad phrase and ciphertext tampering cannot decrypt or write', () async {
    final source = _vault(734);
    addTearDown(source.close);
    await PatientProgressiveDemographicsStore(source).update(
      updateBirthYear: true, birthYear: 1985,
    );
    final raw = await D18EncryptedBackup.exportEncrypted(
      source, passphrase: _secret,
    );
    await expectLater(
      D18EncryptedBackup.open(raw, passphrase: 'incorrect-passphrase'),
      throwsA(anything),
    );
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final sealed = data['sealed'] as String;
    final n = sealed.length ~/ 2;
    data['sealed'] = '${sealed.substring(0, n)}${sealed[n] == 'A' ? 'B' : 'A'}${sealed.substring(n + 1)}';
    await expectLater(
      D18EncryptedBackup.open(jsonEncode(data), passphrase: _secret),
      throwsA(anything),
    );
  });

  test('cannot restore a different Django patient; no clinical records deleted',
      () async {
    final source = _vault(734), other = _vault(812);
    addTearDown(source.close);
    addTearDown(other.close);
    await PatientProgressiveDemographicsStore(source).update(
      updateBirthYear: true, birthYear: 1985,
    );
    await PatientProgressiveDemographicsStore(other).update(
      updateBirthYear: true, birthYear: 1991,
    );
    final encrypted = await D18EncryptedBackup.exportEncrypted(
      source, passphrase: _secret,
    );
    final preview = await D18EncryptedBackup.open(
      encrypted, passphrase: _secret,
    );
    await expectLater(
      D18EncryptedBackup.restoreInto(other, preview), throwsStateError,
    );
    expect((await PatientProgressiveDemographicsStore(other).read())?.birthYear,
        1991);
    expect(await PatientWeightHistoryStore(other).recent(), isEmpty);
  });

  test('device-only recovery explicitly opts into a new empty local vault',
      () async {
    final source = AppDatabase.testPatientVault(
      NativeDatabase.memory(),
      PatientVaultScope.deviceLocal('4b53bce1-51cc-4701-879e-6f239b1a3ba3'),
    );
    final target = AppDatabase.testPatientVault(
      NativeDatabase.memory(),
      PatientVaultScope.deviceLocal('4b53bce1-51cc-4701-879e-6f239b1a3ba4'),
    );
    addTearDown(source.close);
    addTearDown(target.close);
    await PatientProgressiveDemographicsStore(source).update(
      updateBirthYear: true, birthYear: 1994,
    );
    final encrypted = await D18EncryptedBackup.exportEncrypted(
      source, passphrase: _secret,
    );
    final preview = await D18EncryptedBackup.open(
      encrypted, passphrase: _secret,
    );
    await expectLater(
      D18EncryptedBackup.restoreInto(target, preview), throwsStateError,
    );
    await D18EncryptedBackup.restoreInto(target, preview,
        allowDeviceTransfer: true);
    expect((await PatientProgressiveDemographicsStore(target).read())?.birthYear,
        1994);
  });

  test('weight correction is append-only, latest view, and purge deletes family',
      () async {
    final db = _vault(734);
    addTearDown(db.close);
    final weights = PatientWeightHistoryStore(db);
    await weights.append(
      clientUuid: _uuid1, value: '75', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 14),
    );
    await weights.append(
      clientUuid: _uuid2, value: '73', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 15),
    );
    await weights.append(
      clientUuid: _uuid3, value: '72', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 15),
      replacesUuid: _uuid2,
    );
    final latest = await weights.recent();
    expect(latest.length, 2);
    expect(latest.any((x) => x.clientUuid == _uuid2), false);
    expect(latest.any((x) => x.clientUuid == _uuid3), true);
    expect((await weights.exportOwnedRows()).length, 3);
    await weights.deleteFamily(_uuid3);
    expect((await weights.exportOwnedRows()).length, 1);
    expect((await weights.recent()).single.clientUuid, _uuid1);
  });
}
