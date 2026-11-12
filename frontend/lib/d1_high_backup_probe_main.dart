// D1 browser crypto/backup E2E: synthetic only, no active patient route.
// ignore: avoid_web_libraries_in_flutter
import 'dart:convert';
import 'dart:html' as html;
import 'dart:typed_data';

import 'package:drift/drift.dart' as drift;
import 'data/drift/database.dart';
import 'data/drift/d1_authenticated_backup_boundary.dart';
import 'data/drift/d1_webcrypto_backup_cipher.dart';
import 'data/drift/d1_web_encrypted_vault.dart';
import 'data/drift/local_backup.dart';
import 'data/drift/patient_vault_scope.dart';
import 'services/d1_session_fence.dart';

const marker = 'D1_WEBCRYPTO_FAKE_GLUCOSE_731';
Future<void> main() async {
 html.document.title='D1_BACKUP_RUNNING';
 var stage='START';
 final scope=PatientVaultScope.nativeDjango(731);
 final foreign=PatientVaultScope.nativeDjango(812);
 var epoch=17;
 var unlocked=true;
 D1WebEncryptedVaultLease? lease;
 D1WebCryptoBackupCipher? cipher;
 D1SessionFence? fence;
 try{
  stage='OPEN_DB';
  final dbKey=Uint8List.fromList(List.generate(32,(i)=>i+1));
  lease=await D1WebEncryptedVaultAdmission.open(
   scope:scope,authEpoch:epoch,currentScope:()=>scope,currentEpoch:()=>epoch,
   isUnlocked:()=>unlocked,keyMaterial:dbKey,
  );
  final db=lease.database;
  stage='SEED_PROFILE';
  await db.into(db.patientProfiles).insert(
   PatientProfilesCompanion.insert(
    userId:const drift.Value(731),
    updatedAt:DateTime.utc(2026,11,12),
    diabetesType:const drift.Value('synthetic_type1'),
   ),
  );
  await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
   createdAt:DateTime.utc(2026,11,12),
   bloodSugar:121.0,
   clientUuid:marker,
  ));
  final recovery=Uint8List.fromList(List.generate(32,(i)=>i+44));
  cipher=D1WebCryptoBackupCipher(recovery);
  recovery.fillRange(0,recovery.length,0);
  fence=D1SessionFence(scope,epoch);
  final boundary=D1AuthenticatedBackupBoundary(
   db:db,sessionFence:fence,cipher:cipher,
   currentScope:()=>scope,currentAuthEpoch:()=>epoch,
  );
  stage='SEAL';
  final blob=await boundary.exportCiphertextOnly();
  final second=await boundary.exportCiphertextOnly();
  if(blob==second||blob.contains(marker)||
    blob.contains('"patientProfiles"')||blob.contains('"logEntries"')){
   throw StateError('NOT_ENCRYPTED_OR_NONCE_REUSED');
  }
  final header=jsonDecode(blob) as Map<String,dynamic>;
  if(header['owner']!=scope.databaseName||header['format']!='IAMINA_D1_BACKUP'){
   throw StateError('WRONG_ENVELOPE');
  }
  stage='RAW_API_REFUSAL';
  var rawExportRefused=false;
  try{await LocalBackup.exportVaultJson(db);}
  on StateError catch(e){
   rawExportRefused=e.message.toString().contains('D1_WEB_PLAINTEXT');
  }
  if(!rawExportRefused)throw StateError('RAW_EXPORT_PUBLIC');
  var rawRestoreRefused=false;
  try{await LocalBackup.restoreVaultJson(db,'{}');}
  on StateError catch(e){
   rawRestoreRefused=e.message.toString().contains('D1_WEB_PLAINTEXT');
  }
  if(!rawRestoreRefused)throw StateError('RAW_RESTORE_PUBLIC');
  stage='TAMPER';
  final badCiphertext=header['ciphertext'] as String;
  final altered={...header,
    'ciphertext':(badCiphertext.startsWith('A')?'B':'A')+
      badCiphertext.substring(1)};
  var tamperRejected=false;
  try{
   await boundary.restoreAuthenticatedOnly(jsonEncode(altered));
  }catch(_){tamperRejected=true;}
  if(!tamperRejected)throw StateError('TAMPER_ACCEPTED');
  stage='WRONG_KEY';
  final wrongKey=D1WebCryptoBackupCipher(
   Uint8List.fromList(List.generate(32,(i)=>i+75)),
  );
  var wrongRejected=false;
  try{
   await wrongKey.authenticateAndOpen(
     expectedOwner:scope.databaseName,sealedEnvelope:blob,
   );
  }catch(_){wrongRejected=true;}finally{wrongKey.dispose();}
  if(!wrongRejected)throw StateError('WRONG_KEY_ACCEPTED');
  stage='FOREIGN';
  var foreignRejected=false;
  try{
   await cipher.authenticateAndOpen(
    expectedOwner:foreign.databaseName,sealedEnvelope:blob,
   );
  }catch(_){foreignRejected=true;}
  if(!foreignRejected)throw StateError('FOREIGN_ACCEPTED');
  stage='RESTORE';
  await db.delete(db.logEntries).go();
  if((await db.select(db.logEntries).get()).isNotEmpty)
    throw StateError('DELETE_NOT_EXECUTED');
  await boundary.restoreAuthenticatedOnly(blob);
  final restored=await db.select(db.logEntries).get();
  if(restored.length!=1||restored.single.clientUuid!=marker)
    throw StateError('RESTORE_NOT_ATOMIC');
  stage='MALFORMED';
  final root=jsonDecode(await cipher.authenticateAndOpen(
    expectedOwner:scope.databaseName,sealedEnvelope:blob,
  )) as Map<String,dynamic>;
  (root['logEntries'] as List<dynamic>)[0]['bloodSugar']='NOT_A_NUMBER';
  final broken=await cipher.seal(
   owner:scope.databaseName,plaintextJson:jsonEncode(root),
  );
  var rollbackRefused=false;
  try{
   await boundary.restoreAuthenticatedOnly(broken);
  }catch(_){rollbackRefused=true;}
  if(!rollbackRefused)throw StateError('CORRUPT_RECORD_ACCEPTED');
  final safe=await db.select(db.logEntries).get();
  if(safe.length!=1||safe.single.clientUuid!=marker)
    throw StateError('ROLLBACK_LOST_PREEXISTING_DATA');
  stage='EPOCH';
  epoch++;
  var revoked=false;
  try{await boundary.restoreAuthenticatedOnly(blob);}
  catch(_){revoked=true;}
  if(!revoked)throw StateError('REVOKED_SESSION_RESTORED');
  unlocked=false;
  fence.retire();
  stage='CLOSE';
  await lease.retire();
  lease=null;
  cipher.dispose();
  cipher=null;
  html.document.title='D1_BACKUP_PASS';
 }catch(_){
  html.document.title='D1_BACKUP_FAIL_$stage';
 }finally{
  fence?.retire();
  cipher?.dispose();
  try{await lease?.retire();}catch(_){}
 }
}
