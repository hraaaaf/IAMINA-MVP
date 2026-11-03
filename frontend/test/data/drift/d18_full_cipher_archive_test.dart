// D18 step 4/6 archive proof only, no browser DB restoration.
// Synthetic ciphertext and secrets; this DOES NOT prove sqlite3mc keying.
import 'dart:convert';
import 'dart:typed_data';

import 'package:amina/data/drift/d18_full_cipher_archive.dart';
import 'package:amina/data/drift/d18_vault_key_policy.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final a=PatientVaultScope.deviceLocal('e2dbe28f-3eea-4410-86a7-274150f00018');
  final b=PatientVaultScope.deviceLocal('e2dbe28f-3eea-4410-86a7-274150900018');
  const localPass='D18-CI-SYNTHETIC-LOCAL-PASSPHRASE-2026';
  const backupPass='D18-CI-SYNTHETIC-INDEPENDENT-BACKUP-PASSPHRASE-2026';

  test('opaque ciphertext and public key envelope survive independent '
      'round-trip without exposing vault identity or secrets', () async {
    final enrollment=await D18VaultKeyPolicy.createForEmptyVault(
      scope:a,passphrase:localPass);
    addTearDown(enrollment.session.lock);
    final opaque=Uint8List.fromList(List<int>.generate(4096,
      (i)=>(i*17+31)%256));
    final archive=await D18FullCipherArchive.seal(
      scope:a,publicKeyEnvelopeJson:enrollment.publicEnvelopeJson,
      encryptedSqliteBytes:opaque,backupPassphrase:backupPass);
    final outer=jsonDecode(archive) as Map<String,dynamic>;
    expect(outer['format'],D18FullCipherArchive.format);
    expect(outer.keys,isNot(contains('vault')));
    expect(outer.keys,isNot(contains('physicalCiphertext')));
    expect(archive,isNot(contains(a.databaseName)));
    expect(archive,isNot(contains(localPass)));
    expect(archive,isNot(contains(backupPass)));
    expect(archive,isNot(contains(enrollment.offlineRecoveryCode)));
    expect(archive,isNot(contains(enrollment.publicEnvelopeJson)));

    final reopened=await D18FullCipherArchive.open(
      expectedScope:a,archive:archive,backupPassphrase:backupPass);
    expect(reopened.vaultName,a.databaseName);
    expect(reopened.schemaVersion,12);
    expect(reopened.publicKeyEnvelopeJson,enrollment.publicEnvelopeJson);
    expect(reopened.encryptedSqliteBytes,orderedEquals(opaque));
    // The separate local passphrase must still unlock the restored envelope.
    final unlocked=await D18VaultKeyPolicy.unlockWithPassphrase(
      scope:a,publicEnvelopeJson:reopened.publicKeyEnvelopeJson,
      passphrase:localPass);
    unlocked.lock();
    expect(unlocked.isLocked,isTrue);

    // Wrong owner, wrong backup passphrase and a modified auth tag fail closed.
    await expectLater(
      D18FullCipherArchive.open(
        expectedScope:b,archive:archive,backupPassphrase:backupPass),
      throwsA(anything));
    await expectLater(
      D18FullCipherArchive.open(
        expectedScope:a,archive:archive,
        backupPassphrase:'D18-CI-WRONG-ARCHIVE-PASSWORD-2026'),
      throwsA(anything));
    final modified=Map<String,dynamic>.from(outer);
    final encoded=modified['sealed'] as String;
    final at=encoded.length~/2;
    modified['sealed']=encoded.substring(0,at)+
      (encoded[at]=='A'?'B':'A')+encoded.substring(at+1);
    await expectLater(
      D18FullCipherArchive.open(expectedScope:a,
        archive:jsonEncode(modified),backupPassphrase:backupPass),
      throwsA(anything));
  });

  test('plaintext SQLite, missing public envelope and invalid input rejected '
      'before any storage write', () async {
    final stock=Uint8List.fromList(
      [...'SQLite format 3\u0000'.codeUnits,...List<int>.filled(2000,0)]);
    final opaque=Uint8List.fromList(
      List<int>.generate(1024,(i)=>(i*3+1)%256));
    await expectLater(D18FullCipherArchive.seal(
      scope:a,publicKeyEnvelopeJson:'',encryptedSqliteBytes:opaque,
      backupPassphrase:backupPass),throwsA(anything));
    final enrollment=await D18VaultKeyPolicy.createForEmptyVault(
      scope:a,passphrase:localPass);
    addTearDown(enrollment.session.lock);
    await expectLater(D18FullCipherArchive.seal(
      scope:a,publicKeyEnvelopeJson:enrollment.publicEnvelopeJson,
      encryptedSqliteBytes:stock,backupPassphrase:backupPass),
      throwsA(isA<FormatException>()));
    await expectLater(D18FullCipherArchive.seal(
      scope:a,publicKeyEnvelopeJson:enrollment.publicEnvelopeJson,
      encryptedSqliteBytes:Uint8List(50),backupPassphrase:backupPass),
      throwsA(isA<FormatException>()));
    await expectLater(D18FullCipherArchive.open(
      expectedScope:a,archive:'{"format":"wrong"}',
      backupPassphrase:backupPass),throwsA(isA<FormatException>()));
  });
}
