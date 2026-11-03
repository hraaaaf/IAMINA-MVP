// D18 CI-ONLY: full encrypted SQLite export -> off-browser archive ->
// physical restore in a FRESH Chromium profile using pinned sqlite3mc worker.
// No patient data, no clinical activation, no production restore entrypoint.
// ignore_for_file: experimental_member_use, deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';

import 'package:drift/remote.dart';
import 'package:drift/wasm.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;

import 'data/drift/database.dart';
import 'data/drift/d18_full_cipher_archive.dart';
import 'data/drift/d18_keyed_open_guard.dart';
import 'data/drift/d18_pre_cutover_cipher_adapter.dart';
import 'data/drift/d18_unpublished_cipher_connector_web.dart';
import 'data/drift/d18_vault_key_policy.dart';
import 'data/drift/patient_vault_scope.dart';

const _uuid='e2dbe28f-3eea-4410-86a7-274150e00018';
const _localPass='D18-CI-TEST-LOCAL-SECRET-2026-DO-NOT-USE';
const _archivePass='D18-CI-TEST-ARCHIVE-SECRET-2026-DO-NOT-USE';
const _marker='D18_SYNTHETIC_RESTORE_FULL_DB_MARKER_20261103';
final _scope=PatientVaultScope.deviceLocal(_uuid);

void stage(String s)=>html.document.documentElement?.dataset['d18RestoreStage']=s;
void check(bool value,String code){if(!value)throw StateError(code);}
String physicalName() => D18PreCutoverCipherAdapter.destinationFor(_scope);

D18PreCutoverCipherAdapter adapter() => D18PreCutoverCipherAdapter(
  guard:D18KeyedOpenGuard(
    resolveAuthenticatedScope:() async=>_scope,
    readAuthEpoch:()=>1,
  ),
  openVerifiedWorker:openD18UnpublishedCipherWorker,
);
Future<Uint8List> rawCiphertext() async {
  final probe=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('d18_sqlite3mc.wasm'),
    driftWorkerUri:Uri.parse('d18_cipher_worker_correct.js'),
    databaseName:physicalName(),
  );
  final matches=probe.existingDatabases
      .where((x)=>x.$2==physicalName()).toList();
  check(matches.length==1,'D18_RESTORE_EXPECT_SINGLE_CIPHERTEXT');
  final bytes=await probe.exportDatabase(matches.single);
  check(bytes!=null && bytes.length>=1024,'D18_RESTORE_MISSING_BYTES');
  check(String.fromCharCodes(bytes!.take(16))!='SQLite format 3\u0000',
    'D18_RESTORE_EXPORTED_PLAINTEXT');
  check(!String.fromCharCodes(bytes).contains(_marker),
    'D18_RESTORE_EXPORTED_MARKER_PLAINTEXT');
  return bytes;
}
Future<D18FullCipherArchiveContents> importedArchive() async {
  final js=globalContext.getProperty('__D18_CI_IMPORTED_ARCHIVE'.toJS);
  check(js is JSString,'D18_RESTORE_INDEPENDENT_ARCHIVE_NOT_SUPPLIED');
  return D18FullCipherArchive.open(
    expectedScope:_scope, archive:(js as JSString).toDart,
    backupPassphrase:_archivePass,
  );
}
Future<void> assertWholeSchema(AppDatabase db) async {
  stage('verify_sqlite_schema_v12');
  final userVersion=await db.customSelect('PRAGMA user_version').getSingle();
  check(userVersion.read<int>('user_version')==12,'D18_RESTORE_VERSION');
  final tables=(await db.customSelect(
    "SELECT name FROM sqlite_master WHERE type='table'").get())
    .map((r)=>r.read<String>('name')).toSet();
  check(tables.containsAll(const {
    'patient_profiles','log_entries','chat_messages',
    'medication_events','reminders',
    'patient_treatment_declarations_v1',
    'd18_restore_parent','d18_restore_child',
  }), 'D18_RESTORE_TABLE_MISSING');
  final objects=(await db.customSelect(
    "SELECT name FROM sqlite_master WHERE name LIKE 'd18_restore_%'").get())
    .map((r)=>r.read<String>('name')).toSet();
  check(objects.containsAll(const {
    'd18_restore_parent','d18_restore_child','d18_restore_label_unique',
    'd18_restore_parent_view','d18_restore_child_trigger',
  }), 'D18_RESTORE_INDEX_VIEW_TRIGGER_MISSING');
  final parent=await db.customSelect(
    'SELECT id,label,hex(payload) AS payload,optional '
    'FROM d18_restore_parent WHERE id=3').getSingle();
  check(parent.read<int>('id')==3 && parent.read<String>('label')==_marker &&
    parent.read<String>('payload')=='0001FF2A' &&
    parent.read<String?>('optional')==null,
    'D18_RESTORE_ROW_BLOB_NULL_MISMATCH');
  final child=await db.customSelect(
    'SELECT parent_id,note FROM d18_restore_child WHERE id=5').getSingle();
  check(child.read<int>('parent_id')==3 &&
    child.read<String>('note')=='D18_SYNTHETIC_FK_CHILD',
    'D18_RESTORE_FOREIGN_CHILD_MISMATCH');
  final seq=await db.customSelect(
    "SELECT seq FROM sqlite_sequence WHERE name='d18_restore_parent'"
  ).getSingle();
  check(seq.read<int>('seq')==100,'D18_RESTORE_AUTOINCREMENT_SEQUENCE');
  final profile=await db.customSelect(
    'SELECT diabetes_type FROM patient_profiles WHERE user_id=1').getSingle();
  check(profile.read<String>('diabetes_type')==_marker,
    'D18_RESTORE_CLINICAL_TABLE_SENTINEL_LOST');
  final integrity=await db.customSelect('PRAGMA integrity_check').getSingle();
  check(integrity.data.values.single=='ok','D18_RESTORE_INTEGRITY_FAILED');
  check((await db.customSelect('PRAGMA foreign_key_check').get()).isEmpty,
    'D18_RESTORE_FK_FAILED');
}
Future<void> seedAndExport() async {
  stage('create_encrypted_vault_A');
  final enrolled=await D18VaultKeyPolicy.createForEmptyVault(
    scope:_scope,passphrase:_localPass);
  try {
    final vault=await adapter().openUnpublished(
      scope:_scope,keySession:enrolled.session,
      intent:D18CipherVaultOpenIntent.createFresh);
    try {
      await vault.database.customStatement(
        'INSERT INTO patient_profiles(user_id,updated_at,diabetes_type) '
        'VALUES(?,?,?)',[1,1700000000,_marker]);
      await vault.database.customStatement(
        'CREATE TABLE d18_restore_parent (id INTEGER PRIMARY KEY '
        'AUTOINCREMENT,label TEXT NOT NULL,payload BLOB,optional TEXT)');
      await vault.database.customStatement(
        'CREATE TABLE d18_restore_child (id INTEGER PRIMARY KEY,'
        'parent_id INTEGER NOT NULL REFERENCES d18_restore_parent(id),'
        'note TEXT)');
      await vault.database.customStatement(
        'INSERT INTO d18_restore_parent VALUES (?,?,?,?)',
        [3,_marker,Uint8List.fromList([0,1,255,42]),null]);
      await vault.database.customStatement(
        'INSERT INTO d18_restore_parent VALUES (?,?,?,?)',
        [100,'D18_CI_DELETED_MAX',Uint8List.fromList([22,7]),null]);
      await vault.database.customStatement(
        'DELETE FROM d18_restore_parent WHERE id=100');
      await vault.database.customStatement(
        'INSERT INTO d18_restore_child VALUES (?,?,?)',
        [5,3,'D18_SYNTHETIC_FK_CHILD']);
      await vault.database.customStatement(
        'CREATE UNIQUE INDEX d18_restore_label_unique '
        'ON d18_restore_parent(label)');
      await vault.database.customStatement(
        'CREATE VIEW d18_restore_parent_view AS '
        'SELECT id,label FROM d18_restore_parent');
      await vault.database.customStatement(
        'CREATE TRIGGER d18_restore_child_trigger '
        'AFTER INSERT ON d18_restore_child BEGIN '
        'UPDATE d18_restore_parent SET label=label '
        'WHERE id=NEW.parent_id; END');
      await assertWholeSchema(vault.database);
    } finally {await vault.close();}
  } finally {enrolled.session.lock();}
  stage('source_worker_closed_before_export');
  final bytes=await rawCiphertext();
  stage('seal_all_cipher_bytes_with_independent_archive_password');
  final archive=await D18FullCipherArchive.seal(
    scope:_scope,
    publicKeyEnvelopeJson:enrolled.publicEnvelopeJson,
    encryptedSqliteBytes:bytes,
    backupPassphrase:_archivePass,
  );
  check(!archive.contains(_marker) && !archive.contains(_uuid),
    'D18_RESTORE_ARCHIVE_LEAK');
  // Only the encrypted archive crosses from Chromium A to the Node test
  // process and then into Chromium B. It is written OUTSIDE browser storage.
  globalContext.setProperty('__D18_CI_EXPORTED_ARCHIVE'.toJS,archive.toJS);
}
Future<String> transferPhysicalRestore(
  D18FullCipherArchiveContents archive,D18VaultKeySession session,
  {bool crashAfterOneChunk=false},
) async {
  stage('request_exclusive_worker_restore');
  final worker=web.Worker('d18_unpublished_cipher_restore_worker.js'.toJS);
  final control=web.MessageChannel(),sql=web.MessageChannel();
  AppDatabase? db;
  try{
    final key=Uint8List.fromList(
      await session.requireUnlockedKeyForScope(_scope).extractBytes());
    final physical=Uint8List.fromList(archive.encryptedSqliteBytes);
    final keyBuffer=key.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final cipherBuffer=physical.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final message=JSObject()
      ..setProperty('type'.toJS,
        (crashAfterOneChunk ?
          'D18_CI_RESTORE_CRASH_AFTER_FIRST_PERSISTED_BLOCK' :
          'D18_CI_ENCRYPTED_RESTORE_FRESH').toJS)
      ..setProperty('scope'.toJS,_scope.databaseName.toJS)
      ..setProperty('name'.toJS,physicalName().toJS)
      ..setProperty('key'.toJS,keyBuffer)
      ..setProperty('ciphertext'.toJS,cipherBuffer);
    final ack=web.EventStreamProviders.messageEvent
      .forTarget(control.port1).first.timeout(const Duration(seconds:30));
    control.port1.start();
    try{
      worker.postMessage(message,<JSObject>[
        control.port2,sql.port2,keyBuffer,cipherBuffer].toJS);
    }finally{
      key.fillRange(0,key.length,0);
      physical.fillRange(0,physical.length,0);
    }
    final event=await ack;
    check(event.data is JSString,'D18_RESTORE_INVALID_ACK');
    final code=(event.data as JSString).toDart;
    if(code!='READY_RESTORED')return code;
    stage('restore_worker_authenticated_complete_schema');
    final link=await connectToRemoteAndInitialize(
      sql.port1.channel(explicitClose:true));
    db=AppDatabase.testPatientVault(link.executor,_scope);
    await assertWholeSchema(db);
    return code;
  }finally{
    try{await db?.close();}
    finally{
      control.port1.close();sql.port1.close();worker.terminate();
    }
  }
}
Future<void> doRestore({
  required bool expectAlreadyExists, bool crashAfterOneChunk=false,
}) async {
  final archive=await importedArchive();
  stage('unseal_independent_ciphertext_archive');
  final session=await D18VaultKeyPolicy.unlockWithPassphrase(
    scope:_scope,publicEnvelopeJson:archive.publicKeyEnvelopeJson,
    passphrase:_localPass);
  try{
    final status=await transferPhysicalRestore(archive,session,
      crashAfterOneChunk:crashAfterOneChunk);
    check(status==(crashAfterOneChunk ? 'D18_CI_PARTIAL_PERSISTED' :
      expectAlreadyExists ? 'CIPHERTEXT_ALREADY_EXISTS' : 'READY_RESTORED'),
      'D18_RESTORE_INVALID_PHYSICAL_RESPONSE');
  }finally{session.lock();}
}
Future<void> reopenAndValidate({bool wrongKey=false}) async {
  final archive=await importedArchive();
  D18VaultKeySession session;
  if(wrongKey){
    final other=await D18VaultKeyPolicy.createForEmptyVault(
      scope:_scope,passphrase:'D18-CI-WRONG-VAULT-KEY-PASSPHRASE-2026');
    session=other.session;
  }else{
    session=await D18VaultKeyPolicy.unlockWithPassphrase(
      scope:_scope,publicEnvelopeJson:archive.publicKeyEnvelopeJson,
      passphrase:_localPass);
  }
  try{
    stage(wrongKey ? 'wrong_cipher_key_must_fail' : 'reopen_restored_vault');
    if(wrongKey){
      var rejected=false;
      try {
        final wrong=await adapter().openUnpublished(
          scope:_scope,keySession:session,
          intent:D18CipherVaultOpenIntent.reopenExisting);
        await wrong.close();
      }on StateError catch(error){
        rejected=error.toString().contains('D18_WORKER_KEY_REJECTED');
      }
      check(rejected,'D18_RESTORE_WRONG_KEY_NOT_CRYPTOGRAPHIC_REJECTION');
    }else{
      final vault=await adapter().openUnpublished(
        scope:_scope,keySession:session,
        intent:D18CipherVaultOpenIntent.reopenExisting);
      try{await assertWholeSchema(vault.database);}
      finally{await vault.close();}
      stage('compare_physical_bytes_after_new_process');
      final current=await rawCiphertext();
      final saved=archive.encryptedSqliteBytes;
      check(current.length==saved.length,'D18_RESTORE_PHYSICAL_SIZE_DRIFT');
      for(var i=0;i<current.length;i++){
        if(current[i]!=saved[i])throw StateError('D18_RESTORE_PHYSICAL_BYTES_DRIFT');
      }
    }
  }finally{session.lock();}
}
// A deliberately interrupted import MUST NOT become an authenticated vault.
// The incomplete physical file is quarantined, requiring an explicit future
// recovery policy, and must never be silently replaced with a fresh key.
Future<void> verifyInterruptedImportCannotOpen() async {
  final archive=await importedArchive();
  final session=await D18VaultKeyPolicy.unlockWithPassphrase(
    scope:_scope,publicEnvelopeJson:archive.publicKeyEnvelopeJson,
    passphrase:_localPass);
  try{
    stage('crash_partial_file_must_not_authenticate');
    var rejected=false;
    try{
      final vault=await adapter().openUnpublished(
        scope:_scope,keySession:session,
        intent:D18CipherVaultOpenIntent.reopenExisting);
      await vault.close();
    }on StateError{rejected=true;}
    check(rejected,'D18_CRASH_PARTIAL_FILE_INCORRECTLY_ACCEPTED');
  }finally{session.lock();}
}

Future<void> verifyFailedArchiveWithoutCreatingVault() async {
  final envelope=globalContext.getProperty('__D18_CI_IMPORTED_ARCHIVE'.toJS);
  check(envelope is JSString,'D18_RESTORE_TEST_ARCHIVE_MISSING');
  var rejected=false;
  try{
    await D18FullCipherArchive.open(
      expectedScope:_scope,archive:(envelope as JSString).toDart,
      backupPassphrase:'D18-CI-WRONG-INDEPENDENT-BACKUP-PASS');
  }catch(_){rejected=true;}
  check(rejected,'D18_RESTORE_WRONG_ARCHIVE_PASSWORD_ACCEPTED');
  final probe=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('d18_sqlite3mc.wasm'),
    driftWorkerUri:Uri.parse('d18_cipher_worker_correct.js'),
    databaseName:physicalName());
  check(!probe.existingDatabases.any((x)=>x.$2==physicalName()),
    'D18_RESTORE_FAILED_ARCHIVE_CREATED_CIPHERTEXT');
}
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final p=Uri.base.queryParameters['phase'] ?? '';
  try {
    switch(p){
      case 'export':await seedAndExport();break;
      case 'bad_archive':await verifyFailedArchiveWithoutCreatingVault();break;
      case 'restore':await doRestore(expectAlreadyExists:false);break;
      case 'restore_crash':
        await doRestore(expectAlreadyExists:false,
          crashAfterOneChunk:true);break;
      case 'restore_crash_denied':
        await doRestore(expectAlreadyExists:true);break;
      case 'restore_crash_unreadable':
        await verifyInterruptedImportCannotOpen();break;
      case 'restore_again_denied':
        await doRestore(expectAlreadyExists:true);break;
      case 'wrong_key':await reopenAndValidate(wrongKey:true);break;
      case 'reopen':await reopenAndValidate();break;
      case 'source_reopen':await reopenAndValidate();break;
      default:throw StateError('D18_RESTORE_BAD_TEST_PHASE');
    }
    html.document.title='D18_FULL_RESTORE_PASS:'+p;
  }catch(error){
    // Never print stack traces, keys, archive bytes or decrypted content.
    html.document.documentElement?.dataset['d18RestoreError']=
      error.runtimeType.toString();
    html.document.title='D18_FULL_RESTORE_FAIL:'+p;
  }
  runApp(const SizedBox.shrink());
}
