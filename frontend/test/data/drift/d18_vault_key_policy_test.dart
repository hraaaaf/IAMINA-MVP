import 'dart:convert';

import 'package:amina/data/drift/d18_vault_key_policy.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

const _first = 'd18-passphrase-2026-synthetic-strong-ONE';
const _next = 'd18-passphrase-2026-synthetic-strong-TWO';
final _a = PatientVaultScope.deviceLocal('7e0bb410-2c7f-4d3e-9b61-36f092c76210');
final _b = PatientVaultScope.deviceLocal('7e0bb410-2c7f-4d3e-9b61-36f092c76211');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('A: passphrase unlock binds the key to exactly one patient scope', () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);
    final dataKey = await created.session.requireUnlockedKey().extractBytes();
    expect(dataKey.length, 32);
    expect(created.publicEnvelopeJson, isNot(contains(_first)));
    expect(created.publicEnvelopeJson, isNot(contains(created.offlineRecoveryCode)));
    expect(created.publicEnvelopeJson, isNot(contains(_a.databaseName)));
    final envelope = jsonDecode(created.publicEnvelopeJson) as Map<String,dynamic>;
    expect(envelope['iterations'], 600000);
    expect(envelope['cipher'], 'aes-256-gcm');

    final reopened = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: _a, publicEnvelopeJson: created.publicEnvelopeJson,
      passphrase: _first,
    );
    expect(await reopened.requireUnlockedKey().extractBytes(), dataKey);
    reopened.lock();
    expect(reopened.isLocked, isTrue);
    expect(() => reopened.requireUnlockedKey(), throwsStateError);

    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: created.publicEnvelopeJson,
        passphrase: _next,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _b, publicEnvelopeJson: created.publicEnvelopeJson,
        passphrase: _first,
      ), throwsA(isA<Exception>()),
    );
    expect(created.session.isLocked, isFalse);
  });

  test('offline code independently restores data key and resets passphrase',
      () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);
    final dataKey = await created.session.requireUnlockedKey().extractBytes();
    final recovered = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
    );
    expect(await recovered.requireUnlockedKey().extractBytes(), dataKey);
    recovered.lock();

    final replacement = await D18VaultKeyPolicy.resetAfterRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
      newPassphrase: _next,
    );
    addTearDown(replacement.session.lock);
    expect(replacement.offlineRecoveryCode, isNot(created.offlineRecoveryCode));
    expect(await replacement.session.requireUnlockedKey().extractBytes(), dataKey);
    final unlocked = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: _a,
      publicEnvelopeJson: replacement.publicEnvelopeJson,
      passphrase: _next,
    );
    expect(await unlocked.requireUnlockedKey().extractBytes(), dataKey);
    unlocked.lock();

    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
        passphrase: _first,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );
    final newRecovery = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a, publicEnvelopeJson: replacement.publicEnvelopeJson,
      offlineRecoveryCode: replacement.offlineRecoveryCode,
    );
    expect(await newRecovery.requireUnlockedKey().extractBytes(), dataKey);
    newRecovery.lock();
  });

  test('rejects forged, malformed, cross-vault, audit and unscoped input',
      () async {
    final created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _first,
    );
    addTearDown(created.session.lock);

    final corrupted = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    final cipher = corrupted['recoveryWrappedKey'] as String;
    final offset = cipher.length ~/ 2;
    corrupted['recoveryWrappedKey'] =
      '${cipher.substring(0,offset)}${cipher[offset]=='A'?'B':'A'}${cipher.substring(offset+1)}';
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _a, publicEnvelopeJson: jsonEncode(corrupted),
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );

    final forged = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    forged['iterations'] = 2000000000;
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: jsonEncode(forged),
        passphrase: _first,
      ), throwsFormatException,
    );
    final extra = jsonDecode(created.publicEnvelopeJson)
        as Map<String, dynamic>;
    extra['plaintextKey'] = 'MUST_NOT_BE_ALLOWED';
    await expectLater(
      D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a, publicEnvelopeJson: jsonEncode(extra),
        passphrase: _first,
      ), throwsFormatException,
    );
    await expectLater(
      D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _b, publicEnvelopeJson: created.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      ), throwsA(isA<Exception>()),
    );
    await expectLater(
      D18VaultKeyPolicy.createForEmptyVault(
        scope: PatientVaultScope.auditOnly(), passphrase: _first,
      ), throwsStateError,
    );
    await expectLater(
      D18VaultKeyPolicy.createForEmptyVault(scope: _a, passphrase: 'short'),
      throwsArgumentError,
    );
    expect(() => created.session.lock(), returnsNormally);
  });
}
