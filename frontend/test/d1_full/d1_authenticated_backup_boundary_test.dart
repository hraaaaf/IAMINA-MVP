import 'dart:async';
import 'dart:convert';
import 'package:amina/data/drift/d1_authenticated_backup_boundary.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/d1_session_fence.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

// Deliberately NOT crypto: tests gate ordering, NEVER security of encryption.
class _FakeCipher implements D1AuthenticatedBackupCipher {
 bool deny=false;
 Completer<void>? wait;
 @override
 Future<String> seal({required String owner,required String plaintextJson}) async {
  if(wait!=null) await wait!.future;
  return jsonEncode({'format':'IAMINA_D1_BACKUP','version':1,'owner':owner,
    'ciphertext':base64Encode(utf8.encode(plaintextJson))});
 }
 @override
 Future<String> authenticateAndOpen({required String expectedOwner,
  required String sealedEnvelope}) async {
  if(wait!=null) await wait!.future;
  if(deny)throw StateError('INVALID_TAG_FROM_FAKE');
  final obj=jsonDecode(sealedEnvelope) as Map<String,dynamic>;
  if(obj['owner']!=expectedOwner)throw const FormatException('OWNER_MISMATCH');
  return utf8.decode(base64Decode(obj['ciphertext'] as String));
 }
}
void main(){
 final a=PatientVaultScope.nativeDjango(734);
 final b=PatientVaultScope.nativeDjango(812);
 late AppDatabase db;
 late _FakeCipher cipher;
 late D1SessionFence fence;
 PatientVaultScope? scope;
 var epoch=20;
 late D1AuthenticatedBackupBoundary boundary;
 setUp(() async{
  db=AppDatabase.testPatientVault(NativeDatabase.memory(),a);
  cipher=_FakeCipher();
  scope=a;epoch=20;fence=D1SessionFence(a,epoch);
  boundary=D1AuthenticatedBackupBoundary(db:db,sessionFence:fence,
   cipher:cipher,currentScope:()=>scope,currentAuthEpoch:()=>epoch);
  await db.into(db.patientProfiles).insert(
   PatientProfilesCompanion.insert(userId:const drift.Value(734),
     updatedAt:DateTime.utc(2026,11,12),
     diabetesType:const drift.Value('synthetic_a')));
 });
 tearDown(() async {fence.retire();await db.close();});
 test('D1 backup: export envelope is owner-labelled, not raw JSON',() async {
  final blob=await boundary.exportCiphertextOnly();
  final header=jsonDecode(blob) as Map<String,dynamic>;
  expect(header['owner'],a.databaseName);
  expect(blob, isNot(contains('"patientProfiles"')));
 });
 test('D1 backup: reject B identity before restore touches A',() async{
  final blob=await boundary.exportCiphertextOnly();
  scope=b;epoch++;
  await expectLater(boundary.restoreAuthenticatedOnly(blob),throwsStateError);
  expect((await db.select(db.patientProfiles).getSingle()).userId,734);
 });
 test('D1 backup: reject cryptographic failure before destructive restore',() async{
  final blob=await boundary.exportCiphertextOnly();
  cipher.deny=true;
  await expectLater(boundary.restoreAuthenticatedOnly(blob),throwsStateError);
  expect((await db.select(db.patientProfiles).getSingle()).diabetesType,'synthetic_a');
 });
 test('D1 backup: revoke A during async seal, ciphertext must not be published',() async{
  cipher.wait=Completer<void>();
  final result=boundary.exportCiphertextOnly();
  await Future<void>.delayed(const Duration(milliseconds:25));
  scope=b;epoch++;fence.retire();cipher.wait!.complete();
  await expectLater(result,throwsStateError);
 });
 test('D1 backup: reject plain legacy backup on restore',() async{
  final raw=await LocalBackupForTest.export(db);
  await expectLater(boundary.restoreAuthenticatedOnly(raw),throwsFormatException);
  expect((await db.select(db.patientProfiles).getSingle()).userId,734);
 });
}
// Placeholder intentionally delegates to scoped JSON for gate-negative test.
class LocalBackupForTest {
 static Future<String> export(AppDatabase db) async {
  return jsonEncode({'formatVersion':2,'vaultName':db.patientVaultScope!.databaseName});
 }
}
