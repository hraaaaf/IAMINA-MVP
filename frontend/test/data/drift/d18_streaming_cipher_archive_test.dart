// D18 P0-D PRE-CUTOVER only: synthetic already-encrypted-like bytes.
// This is NOT real sqlite3mc worker export, browser storage or clinical restore.
import 'dart:convert';
import 'dart:typed_data';
import 'package:crypto/crypto.dart' show sha256;
import 'package:amina/data/drift/d18_streaming_cipher_archive.dart';
import 'package:amina/data/drift/d18_vault_key_policy.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final a=PatientVaultScope.deviceLocal(
      'e2dbe28f-3eea-4410-86a7-274150a00018');
  final b=PatientVaultScope.deviceLocal(
      'e2dbe28f-3eea-4410-86a7-274150b00018');
  const local='D18-CI-LOCAL-KEY-TEST-NOT-A-PATIENT-2026';
  const archivePass='D18-CI-STREAM-ARCHIVE-TEST-NOT-A-PATIENT-2026';

  Future<List<List<int>>> archive(
      PatientVaultScope scope,String envelope,Uint8List bytes) =>
    D18StreamingCipherArchive.seal(
      scope:scope,publicKeyEnvelopeJson:envelope,
      backupPassphrase:archivePass,
      // A 17 MiB SINGLE source segment must still produce bounded frames.
      encryptedSqliteChunks:Stream<List<int>>.value(bytes),
    ).toList();

  test('17 MiB+ ciphertext is chunked and exact after verified final frame',
      () async {
    final enrolled=await D18VaultKeyPolicy.createForEmptyVault(
      scope:a,passphrase:local);
    addTearDown(enrolled.session.lock);
    final physical=Uint8List(17*1024*1024+107);
    for(var i=0;i<physical.length;i+=4096) {
      physical[i]=(i~/4096)%256;
    }
    final frames=await archive(a,enrolled.publicEnvelopeJson,physical);
    expect(frames.length,greaterThan(270));
    final header=jsonDecode(utf8.decode(frames.first)) as Map<String,dynamic>;
    expect(header['format'],D18StreamingCipherArchive.format);
    expect(header.containsKey('scope'),false);
    expect(utf8.decode(frames.first),isNot(contains(a.databaseName)));
    expect(utf8.decode(frames.first),isNot(contains(archivePass)));

    final staged=BytesBuilder(copy:false);
    final manifest=await D18StreamingCipherArchive.restoreIntoQuarantine(
      expectedScope:a,backupPassphrase:archivePass,
      archiveChunks:Stream<List<int>>.fromIterable(frames),
      stageEncryptedChunk:(chunk) async {staged.add(chunk);});
    final restored=staged.takeBytes();
    expect(manifest.vaultName,a.databaseName);
    expect(manifest.schemaVersion,12);
    expect(manifest.publicKeyEnvelopeJson,enrolled.publicEnvelopeJson);
    expect(manifest.bytes,physical.length);
    expect(manifest.chunks,greaterThan(256));
    expect(restored.length,physical.length);
    expect(sha256.convert(restored),sha256.convert(physical));
    expect(manifest.sha256,sha256.convert(physical).toString());
  });

  test('wrong passphrase, other patient, damaged chunk and missing final'
       ' are denied',() async {
    final enrolled=await D18VaultKeyPolicy.createForEmptyVault(
      scope:a,passphrase:local);
    addTearDown(enrolled.session.lock);
    final physical=Uint8List.fromList(
      List<int>.generate(4096,(i)=>(17*i+13)%256));
    final frames=await archive(a,enrolled.publicEnvelopeJson,physical);
    Future<D18StreamingArchiveManifest> open(
      List<List<int>> input,{String password=archivePass,
      PatientVaultScope? scope}) =>
      D18StreamingCipherArchive.restoreIntoQuarantine(
        expectedScope:scope??a,backupPassphrase:password,
        archiveChunks:Stream<List<int>>.fromIterable(input),
        stageEncryptedChunk:(_) async {});

    await expectLater(open(frames,
      password:'D18-CI-STREAM-ARCHIVE-WRONG-PASSWORD-2026'),throwsA(anything));
    await expectLater(open(frames,scope:b),throwsA(anything));
    await expectLater(open(frames.sublist(0,frames.length-1)),
      throwsA(isA<FormatException>()));

    final changed=List<List<int>>.from(frames);
    final chunk=jsonDecode(utf8.decode(changed[1])) as Map<String,dynamic>;
    final sealed=chunk['sealed'] as String;
    chunk['sealed']=sealed.replaceRange(2,3,sealed[2]=='A'?'B':'A');
    changed[1]=utf8.encode(jsonEncode(chunk)+'\n');
    await expectLater(open(changed),throwsA(anything));
  });

  test('plaintext SQLite is rejected and cancellation never produces proof',
      () async {
    final enrolled=await D18VaultKeyPolicy.createForEmptyVault(
      scope:a,passphrase:local);
    addTearDown(enrolled.session.lock);
    final plaintext=Uint8List.fromList([
      ...'SQLite format 3\u0000'.codeUnits,
      ...List<int>.filled(4096,0),
    ]);
    await expectLater(archive(a,enrolled.publicEnvelopeJson,plaintext),
      throwsA(isA<FormatException>()));
    await expectLater(archive(a,'',Uint8List(4096)),
      throwsA(isA<FormatException>()));
    final valid=await archive(a,enrolled.publicEnvelopeJson,
      Uint8List(4096));
    var stagedChunks=0;
    await expectLater(D18StreamingCipherArchive.restoreIntoQuarantine(
      expectedScope:a,backupPassphrase:archivePass,
      archiveChunks:Stream<List<int>>.fromIterable(valid),
      stageEncryptedChunk:(_) async {
        stagedChunks++;
        throw StateError('D18_SYNTHETIC_CANCEL');
      }),throwsStateError);
    expect(stagedChunks,1);
  });
}
