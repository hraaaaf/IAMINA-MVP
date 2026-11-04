// ignore_for_file: experimental_member_use, avoid_web_libraries_in_flutter, deprecated_member_use
// D18 stage 3: synthetic whole-schema copy via the unpublished encrypted worker.
// NEVER import this file from the application or use it with patient records.
// No patient cutover, no source deletion, no plaintext destination, no fixed key.
import 'dart:convert';
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'package:drift/drift.dart';
import 'package:drift/remote.dart';
import 'package:drift/wasm.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';

const srcName='d18_ci_full_schema_plain_20261102';
const dstName='amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018_d18_cipher_v1';
const abortName='amina_vault_v1_device_e2dbe28f3eea441086a7274150b00018_d18_cipher_v1';
const crashName='amina_vault_v1_device_e2dbe28f3eea441086a7274150c00018_d18_cipher_v1';
const marker='D18_CI_FULL_SCHEMA_SENTINEL_20261102';
final scope=PatientVaultScope.deviceLocal('e2dbe28f-3eea-4410-86a7-274150a00018');
void stage(String s)=>html.document.documentElement?.dataset['d18FullStage']=s;
void check(bool b,String code){if(!b)throw StateError(code);}
String ident(String s)=>'"'+s.replaceAll('"','""')+'"';

final class NoMigrations implements QueryExecutorUser {
  const NoMigrations();
  @override
  int get schemaVersion=>12;
  @override
  Future<void> beforeOpen(QueryExecutor e,OpeningDetails d) async {}
}
Future<QueryExecutor> openSource() async {
  // This is a REOPEN-only synthetic migration. Never silently create an
  // empty plaintext source on failed persistence across page lifetimes.
  stage('source_probe_before_reopen');
  final existing = await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    databaseName:srcName);
  check(existing.existingDatabases.any((entry)=>entry.$2==srcName),
    'D18_SOURCE_MISSING_BEFORE_REOPEN');
  stage('source_open_wasm_indexeddb');
  final opened=await WasmDatabase.open(
    databaseName:srcName,sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs:false);
  stage('source_implementation_preflight');
  check(opened.chosenImplementation.name=='sharedIndexedDb',
    'UNSUPPORTED_SOURCE_STORAGE');
  final q=opened.resolvedExecutor;
  stage('source_ensure_open_no_migrations');
  await q.ensureOpen(const NoMigrations());
  stage('source_open_ready');
  return q;
}
final class Encrypted {
  final web.Worker worker;
  final web.MessagePort control,sql;
  final QueryExecutor q;
  const Encrypted(this.worker,this.control,this.sql,this.q);
  Future<void> close() async {
    try{await q.close();}
    finally{control.close();sql.close();worker.terminate();}
  }
}
Future<Encrypted> openDestination({
  String databaseName=dstName,
  bool reopen=false,
}) async {
  stage('candidate_cipher_worker_handshake');
  const suffix='_d18_cipher_v1';
  check(databaseName.endsWith(suffix),'CANDIDATE_DESTINATION_SUFFIX');
  final scope=databaseName.substring(0,databaseName.length-suffix.length);
  check(RegExp(r'^amina_vault_v1_device_[0-9a-f]{32}$').hasMatch(scope),
      'CANDIDATE_INVALID_SCOPE');
  final field=databaseName==abortName ? '__D18_FULL_ABORT_KEY' :
    databaseName==crashName ? '__D18_FULL_CRASH_KEY' : '__D18_FULL_KEY';
  final key=globalContext.getProperty(field.toJS);
  check(key is JSUint8Array,'D18_CANDIDATE_TEST_KEY_MISSING');
  final bytes=Uint8List.fromList((key as JSUint8Array).toDart);
  check(bytes.length==32,'D18_CANDIDATE_TEST_KEY_INVALID');
  final worker=web.Worker('d18_unpublished_cipher_worker.js'.toJS);
  final control=web.MessageChannel(), sql=web.MessageChannel();
  try {
    final buffer=bytes.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final request=JSObject()
      ..setProperty('type'.toJS,'D18_UNPUBLISHED_KEYED_OPEN'.toJS)
      ..setProperty('scope'.toJS,scope.toJS)
      ..setProperty('name'.toJS,databaseName.toJS)
      ..setProperty('intent'.toJS,
          (reopen ? 'reopenExisting' : 'createFresh').toJS)
      ..setProperty('key'.toJS,buffer);
    final ack=web.EventStreamProviders.messageEvent
        .forTarget(control.port1).first.timeout(const Duration(seconds:25));
    control.port1.start();
    worker.postMessage(request,<JSObject>[control.port2,sql.port2,buffer].toJS);
    bytes.fillRange(0,bytes.length,0);
    final event=await ack;
    check(event.data is JSString,'D18_CANDIDATE_ACK_INVALID');
    final status=(event.data as JSString).toDart;
    check(status==(reopen ? 'READY_EXISTING_AUTHENTICATED' : 'READY_FRESH'),
        'D18_CANDIDATE_NOT_AUTHENTICATED');
    final conn=await connectToRemoteAndInitialize(
        sql.port1.channel(explicitClose:true));
    await conn.ensureOpen(const NoMigrations());
    return Encrypted(worker,control.port1,sql.port1,conn.executor);
  }catch(_){
    control.port1.close();sql.port1.close();worker.terminate();
    rethrow;
  }
}
Future<void> seed() async {
  stage('seed_generated_schema');
  final opened=await WasmDatabase.open(
    databaseName:srcName,sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs:false);
  final db=AppDatabase.testPatientVault(opened.resolvedExecutor,scope);
  try {
    await db.customSelect('SELECT count(*) FROM sqlite_master').getSingle();
    await db.customStatement('CREATE TABLE "d18_parent" (id INTEGER PRIMARY KEY '
      'AUTOINCREMENT,label TEXT NOT NULL,payload BLOB,optional TEXT)');
    await db.customStatement('CREATE TABLE "d18_child" (id INTEGER PRIMARY KEY,'
      'parent_id INTEGER NOT NULL REFERENCES "d18_parent"(id),note TEXT)');
    await db.customStatement('INSERT INTO "d18_parent" VALUES(?,?,?,?)',
      [3,marker,Uint8List.fromList([0,1,255,42]),null]);
    await db.customStatement('INSERT INTO "d18_parent" VALUES(?,?,?,?)',
      [100,'CI_DELETED_MAX',Uint8List.fromList([22,7]),null]);
    await db.customStatement('DELETE FROM "d18_parent" WHERE id=100');
    await db.customStatement('INSERT INTO "d18_child" VALUES(?,?,?)',
      [5,3,'CI_FK_CHILD']);
    await db.customStatement('CREATE UNIQUE INDEX "d18_parent_label_idx" '
      'ON "d18_parent"(label)');
    await db.customStatement('CREATE VIEW "d18_parent_view" AS '
      'SELECT id,label FROM "d18_parent"');
    await db.customStatement('CREATE TRIGGER "d18_child_trigger" '
      'AFTER INSERT ON "d18_child" BEGIN '
      'UPDATE "d18_parent" SET label=label WHERE id=NEW.parent_id; END');
    final check1=await db.customSelect('PRAGMA integrity_check').getSingle();
    check(check1.data.values.single=='ok','BAD_SEED_INTEGRITY');
    check((await db.customSelect('PRAGMA foreign_key_check').get()).isEmpty,
      'BAD_SEED_FOREIGN_KEY');
  }finally{await db.close();}
  // Require seed durability after closing its connection. A subsequent
  // migration page must not generate a fresh empty SQLite source.
  stage('seed_probe_persisted_source');
  final persisted=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    databaseName:srcName);
  check(persisted.existingDatabases.any((entry)=>entry.$2==srcName),
    'D18_SEED_NOT_PERSISTED');
}
final class Snap {
  final List<Map<String,Object?>> schema,seq;
  final Map<String,List<Map<String,Object?>>> data;
  final int version;
  const Snap(this.schema,this.seq,this.data,this.version);
}
Future<Snap> snapshot(QueryExecutor q) async {
  final schema=await q.runSelect(
    "SELECT type,name,tbl_name,sql FROM sqlite_master "
    "WHERE name NOT LIKE 'sqlite_%' AND "
    "type IN ('table','index','view','trigger') ORDER BY type,name",[]);
  final data=<String,List<Map<String,Object?>>>{};
  for(final row in schema.where((o)=>o['type']=='table')){
    final n=row['name'] as String;
    data[n]=await q.runSelect('SELECT * FROM '+ident(n)+' ORDER BY rowid',[]);
  }
  final seq=await q.runSelect('SELECT name,seq FROM sqlite_sequence ORDER BY name',[]);
  final v=await q.runSelect('PRAGMA user_version',[]);
  check(v.length==1,'MISSING_USER_VERSION');
  return Snap(schema,seq,data,v.single['user_version'] as int);
}
String canonicalValue(Object? v) {
  if(v is Uint8List)return 'blob:'+base64Encode(v);
  if(v is List<int>)return 'blob:'+base64Encode(v);
  return jsonEncode(v);
}
String canonicalRows(List<Map<String,Object?>> items)=>jsonEncode(
  items.map((r)=>{for(final k in (r.keys.toList()..sort()))k:canonicalValue(r[k])})
    .toList());
void compare(Snap a,Snap b){
  check(a.version==b.version,'VERSION_MISMATCH');
  check(jsonEncode(a.schema)==jsonEncode(b.schema),'SCHEMA_MISMATCH');
  check(jsonEncode(a.seq)==jsonEncode(b.seq),'AUTOINCREMENT_MISMATCH');
  check(a.data.length==b.data.length,'TABLES_MISMATCH');
  for(final n in a.data.keys){
    check(b.data.containsKey(n),'MISSING_TABLE');
    check(canonicalRows(a.data[n]!)==canonicalRows(b.data[n]!),
      'ROW_CONTENT_MISMATCH');
  }
}
Future<void> integrity(QueryExecutor q) async {
  final v=await q.runSelect('PRAGMA integrity_check',[]);
  check(v.length==1&&v.single.values.single=='ok','INTEGRITY_FAILURE');
  check((await q.runSelect('PRAGMA foreign_key_check',[])).isEmpty,
    'FOREIGN_KEY_FAILURE');
}
Future<void> abortRollback() async {
  stage('fault_injection_transaction');
  final original=await openSource();
  late final Snap before;
  try{await integrity(original);before=await snapshot(original);}
  finally{await original.close();}
  final interrupted=await openDestination(databaseName:abortName);
  try{
    await interrupted.q.runCustom('BEGIN IMMEDIATE',[]);
    try{
      await interrupted.q.runCustom(
        'CREATE TABLE "d18_injected_partial" (id INTEGER PRIMARY KEY)',[]);
      await interrupted.q.runCustom(
        'INSERT INTO "d18_injected_partial" VALUES(1)',[]);
      throw StateError('EXPECTED_INJECTED_COPY_FAILURE');
    }catch(e){
      check(e is StateError && e.message=='EXPECTED_INJECTED_COPY_FAILURE',
        'UNEXPECTED_FAULT');
      await interrupted.q.runCustom('ROLLBACK',[]);
    }
  }finally{await interrupted.close();}
  stage('fault_injection_independent_reopen');
  final restarted=await openDestination(databaseName:abortName);
  try{
    final objects=await restarted.q.runSelect(
      "SELECT name FROM sqlite_master WHERE name='d18_injected_partial'",[]);
    check(objects.isEmpty,'PARTIAL_SCHEMA_SURVIVED_ROLLBACK');
    final v=await restarted.q.runSelect('PRAGMA user_version',[]);
    check(v.length==1 && v.single.values.single==0,
      'PARTIAL_SCHEMA_VERSION_SURVIVED_ROLLBACK');
  }finally{await restarted.close();}
  final sourceAfter=await openSource();
  try{compare(before,await snapshot(sourceAfter));await integrity(sourceAfter);}
  finally{await sourceAfter.close();}
}
// A genuine unclean worker termination with an OPEN, uncommitted transaction.
// Never perform this against real patients. Do not invoke ROLLBACK/close on
// the crashed worker: only the restarted storage engine can recover the journal.
Future<void> crashUncommitted() async {
  stage('crash_source_preflight');
  final source=await openSource();
  try {
    await integrity(source);
    final before=await snapshot(source);
    check(before.schema.any((s)=>s['name']=='d18_child_trigger'),
      'CRASH_SOURCE_UNSEEDED');
  } finally { await source.close(); }
  final doomed=await openDestination(databaseName:crashName);
  stage('crash_transaction_open');
  await doomed.q.runCustom('BEGIN IMMEDIATE',[]);
  await doomed.q.runCustom(
    'CREATE TABLE "d18_crash_partial" (id INTEGER PRIMARY KEY, marker TEXT)',[]);
  await doomed.q.runCustom(
    'INSERT INTO "d18_crash_partial" VALUES (?, ?)',[1,marker]);
  final visible=await doomed.q.runSelect(
    'SELECT marker FROM "d18_crash_partial" WHERE id=1',[]);
  check(visible.length==1 && visible.single['marker']==marker,
    'CRASH_UNCOMMITTED_WRITE_NOT_VISIBLE');
  // This is the fault injection: no COMMIT, ROLLBACK, executor.close or
  // DriftServer.shutdown. The next CI phase uses a NEW Chromium process.
  stage('crash_worker_force_terminate');
  doomed.worker.terminate();
  doomed.control.close();
  doomed.sql.close();
}

Future<void> verifyCrashRecovery() async {
  stage('crash_recovery_new_process');
  final crashed=await openDestination(databaseName:crashName);
  try {
    await integrity(crashed.q);
    final tables=await crashed.q.runSelect(
      "SELECT name FROM sqlite_master WHERE name='d18_crash_partial'",[]);
    check(tables.isEmpty,'CRASH_PARTIAL_SCHEMA_SURVIVED');
    final version=await crashed.q.runSelect('PRAGMA user_version',[]);
    check(version.length==1 && version.single.values.single==0,
      'CRASH_PARTIAL_DB_MARKED_READY');
  } finally {await crashed.close();}
  stage('crash_source_still_intact');
  final source=await openSource();
  try {
    await integrity(source);
    final after=await snapshot(source);
    check(after.schema.any((s)=>s['name']=='d18_child_trigger') &&
      after.version==12 &&
      after.data['d18_parent']?.length==1 &&
      after.data['d18_child']?.length==1 &&
      after.seq.any((s)=>s['name']=='d18_parent' && s['seq']==100),
      'CRASH_SOURCE_SCHEMA_OR_SEQUENCE_MODIFIED');
    final row=after.data['d18_parent']!.single;
    final child=after.data['d18_child']!.single;
    check(row['id']==3 && row['label']==marker &&
      canonicalValue(row['payload'])==
        canonicalValue(Uint8List.fromList([0,1,255,42])) &&
      row['optional']==null && child['parent_id']==3 &&
      child['id']==5 && child['note']=='CI_FK_CHILD',
      'CRASH_SOURCE_CONTENT_MODIFIED');
  } finally {await source.close();}
}
// Synthetic source write gate: SQLite BEGIN IMMEDIATE is held during the
// entire source snapshot -> keyed copy -> parity verification. This POC does
// not yet implement the actual clinical runtime's cutover / account gate.
// CI-only cross-tab cooperative gate. The real application must enforce the
// SAME gate for every writer before a clinical migration can be considered safe.
// An ordinary SQLite transaction alone does not isolate clients multiplexed
// through one shared worker / SQLite connection.
Future<JSObject> acquireSourceGate() async {
  final fn=globalContext.getProperty('__D18AcquireSourceWriteLock'.toJS);
  check(fn is JSFunction, 'SOURCE_GATE_NOT_INSTALLED');
  final lease=await globalContext.callMethod<JSPromise<JSObject>>(
    '__D18AcquireSourceWriteLock'.toJS,srcName.toJS).toDart;
  check((lease.getProperty('ok'.toJS) as JSBoolean).toDart,
    'SOURCE_GATE_UNAVAILABLE');
  return lease;
}
Future<void> releaseSourceGate(JSObject lease) async {
  await lease.callMethod<JSPromise<JSAny?>>('release'.toJS).toDart;
}
Future<void> holdSourceWriteLock() async {
  stage('source_gate_owner_acquire');
  final gate=await acquireSourceGate();
  try {
    stage('source_lock_begin');
    final q=await openSource();
    var locked=false;
    try {
      await q.runCustom('BEGIN IMMEDIATE',[]);
      locked=true;
      stage('source_write_gate_held');
      await html.window.onMessage
        .firstWhere((event)=>event.data=='D18_CI_RELEASE_SOURCE')
        .timeout(const Duration(seconds:25));
    } finally {
      try {if(locked) await q.runCustom('ROLLBACK',[]);}
      finally {await q.close();}
    }
  } finally {await releaseSourceGate(gate);}
}
Future<void> competeSourceWriteLock() async {
  // Never open the physical source before acquiring this same-origin gate.
  // The test exercises a genuine second tab following the writer protocol.
  stage('writer_waits_source_gate');
  final gate=await acquireSourceGate();
  try {
    stage('writer_gate_acquired');
    final q=await openSource();
    try {
      stage('writer_attempts_immediate_transaction');
      await q.runCustom('BEGIN IMMEDIATE',[]);
      stage('writer_immediate_granted');
      await q.runCustom('ROLLBACK',[]);
    } finally {await q.close();}
  } finally {await releaseSourceGate(gate);}
}
Future<void> migrate() async {
  stage('preflight_acquire_source_origin_gate');
  final gate=await acquireSourceGate();
  try {
    await migrateWithSourceGateHeld();
  } finally {await releaseSourceGate(gate);}
}
Future<void> migrateWithSourceGateHeld() async {
  stage('preflight_lock_source_before_snapshot');
  final src=await openSource();
  var locked=false;
  late final Snap original;
  try{
    // Strict preflight: no retries, no re-seed, no skipped assertions.
    stage('preflight_begin_immediate');
    await src.runCustom('BEGIN IMMEDIATE',[]);
    locked=true;
    stage('preflight_integrity_under_lock');
    await integrity(src);
    stage('preflight_snapshot_under_lock');
    original=await snapshot(src);
    // Fail closed on *which* synthetic schema invariant is missing.
    // Avoid logging any SQL, patient-like values, or full schema contents.
    stage('preflight_check_source_version');
    check(original.version==12, 'D18_SOURCE_VERSION_NOT_12');
    stage('preflight_check_source_table');
    check(original.schema.any((x)=>x['name']=='d18_parent')&&
      original.schema.any((x)=>x['name']=='d18_child'),
      'D18_SOURCE_SYNTHETIC_TABLES_MISSING');
    stage('preflight_check_source_index');
    check(original.schema.any((x)=>x['name']=='d18_parent_label_idx'),
      'D18_SOURCE_SYNTHETIC_INDEX_MISSING');
    stage('preflight_check_source_view');
    check(original.schema.any((x)=>x['name']=='d18_parent_view'),
      'D18_SOURCE_SYNTHETIC_VIEW_MISSING');
    stage('preflight_check_source_trigger');
    check(original.schema.any((x)=>x['name']=='d18_child_trigger'),
      'D18_SOURCE_SYNTHETIC_TRIGGER_MISSING');
    stage('preflight_schema_validated');
    stage('ensure_new_destination');
    final probe=await WasmDatabase.probe(
      sqlite3Uri:Uri.parse('d18_sqlite3mc.wasm'),
      driftWorkerUri:Uri.parse('d18_cipher_worker_correct.js'),
      databaseName:dstName);
    check(!probe.existingDatabases.any((e)=>e.$2==dstName),
      'DESTINATION_ALREADY_EXISTS');
    final target=await openDestination();
    try{
      final q=target.q;
      await q.runCustom('PRAGMA foreign_keys=ON',[]);
      final f=await q.runSelect('PRAGMA foreign_keys',[]);
      check(f.length==1&&f.single.values.single==1,'FK_NOT_ENABLED');
      await q.runCustom('BEGIN IMMEDIATE',[]);
      try{
        await q.runCustom('PRAGMA defer_foreign_keys=ON',[]);
        for(final o in original.schema.where((o)=>o['type']=='table')){
          await q.runCustom(o['sql'] as String,[]);
        }
        for(final table in original.data.entries){
          for(final row in table.value){
            final columns=row.keys.toList();
            final sql='INSERT INTO '+ident(table.key)+' ('+
              columns.map(ident).join(',')+') VALUES ('+
              List.filled(columns.length,'?').join(',')+')';
            await q.runCustom(sql,columns.map((k)=>row[k]).toList());
          }
        }
        // sqlite_sequence.name is not UNIQUE: do not use REPLACE.
        await q.runCustom('DELETE FROM sqlite_sequence',[]);
        for(final seq in original.seq){
          await q.runCustom(
            'INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)',
            [seq['name'],seq['seq']]);
        }
        for(final kind in ['index','view','trigger']){
          for(final o in original.schema.where((x)=>
            x['type']==kind && x['sql']!=null)){
            await q.runCustom(o['sql'] as String,[]);
          }
        }
        await q.runCustom('PRAGMA user_version='+original.version.toString(),[]);
        await integrity(q);
        compare(original,await snapshot(q));
        await q.runCustom('COMMIT',[]);
      }catch(_){await q.runCustom('ROLLBACK',[]);rethrow;}
    }finally{await target.close();}
    // Still under BEGIN IMMEDIATE on source: an uncooperative writer cannot
    // change data between initial capture and the final compare.
    stage('source_compare_inside_write_gate');
    await integrity(src);
    compare(original,await snapshot(src));
  }finally{
    try{if(locked)await src.runCustom('ROLLBACK',[]);}
    finally{await src.close();}
  }
  stage('original_preserved_after_write_gate');
  final unchanged=await openSource();
  try{await integrity(unchanged);compare(original,await snapshot(unchanged));}
  finally{await unchanged.close();}
}
Future<void> verify() async {
  stage('cross_process_compare');
  final source=await openSource();
  late final Snap old;
  try{await integrity(source);old=await snapshot(source);}
  finally{await source.close();}
  final dst=await openDestination(reopen:true);
  try{
    await integrity(dst.q);
    compare(old,await snapshot(dst.q));
    final child=await dst.q.runSelect('SELECT parent_id '
      'FROM "d18_child" WHERE id=5',[]);
    check(child.length==1&&child.single['parent_id']==3,'CHILD_LOST');
  }finally{await dst.close();}
}
Future<void> raw() async {
  stage('ciphertext_at_rest');
  final probe=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('d18_sqlite3mc.wasm'),
    driftWorkerUri:Uri.parse('d18_cipher_worker_correct.js'),
    databaseName:dstName);
  final matches=probe.existingDatabases.where((e)=>e.$2==dstName).toList();
  check(matches.length==1,'CIPHER_FILE_MISSING');
  final bytes=await probe.exportDatabase(matches.single);
  check(bytes!=null&&bytes.length>100,'CIPHER_BYTES_MISSING');
  final b=bytes!;
  check(String.fromCharCodes(b.take(16))!='SQLite format 3\u0000',
    'PLAINTEXT_SQLITE_HEADER');
  final chars=String.fromCharCodes(b);
  for(final value in [marker,'d18_parent','d18_child','d18_child_trigger']){
    check(!chars.contains(value),'PLAINTEXT_CONTENT');
  }
}
// CI negative control: never create a plaintext source or ciphertext target
// when a migration preflight fails, even if this browser has no prior vault.
Future<void> assertNoCipherDestination() async {
  stage('negative_assert_no_cipher_destination');
  final probe=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('d18_sqlite3mc.wasm'),
    driftWorkerUri:Uri.parse('d18_cipher_worker_correct.js'),
    databaseName:dstName);
  check(!probe.existingDatabases.any((entry)=>entry.$2==dstName),
    'D18_NEGATIVE_CREATED_CIPHERTEXT');
}
Future<void> assertMissingSourceUntouched() async {
  stage('negative_assert_missing_source_untouched');
  final source=await WasmDatabase.probe(
    sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    databaseName:srcName);
  check(!source.existingDatabases.any((entry)=>entry.$2==srcName),
    'D18_NEGATIVE_CREATED_PLAINTEXT_SOURCE');
  await assertNoCipherDestination();
}
Future<void> seedWithMissingTrigger() async {
  // Deliberately corrupt only a disposable synthetic schema object after
  // seeding. No original patient data exists or may be supplied here.
  await seed();
  stage('negative_drop_synthetic_trigger');
  final q=await openSource();
  try {
    await q.runCustom('DROP TRIGGER "d18_child_trigger"',[]);
    await integrity(q);
    final s=await snapshot(q);
    check(!s.schema.any((row)=>row['name']=='d18_child_trigger'),
      'D18_NEGATIVE_TRIGGER_STILL_PRESENT');
  } finally {await q.close();}
}
Future<void> assertMissingTriggerUntouched() async {
  stage('negative_assert_incomplete_source_untouched');
  final q=await openSource();
  try {
    await integrity(q);
    final snap=await snapshot(q);
    check(snap.version==12 && 
      !snap.schema.any((row)=>row['name']=='d18_child_trigger') &&
      snap.schema.any((row)=>row['name']=='d18_parent') &&
      snap.schema.any((row)=>row['name']=='d18_child') &&
      snap.schema.any((row)=>row['name']=='d18_parent_label_idx') &&
      snap.schema.any((row)=>row['name']=='d18_parent_view'),
      'D18_NEGATIVE_INCOMPLETE_SCHEMA_CHANGED');
    final parents=snap.data['d18_parent'];
    final children=snap.data['d18_child'];
    check(parents!=null && parents.length==1 &&
      parents.single['id']==3 && parents.single['label']==marker &&
      children!=null && children.length==1 &&
      children.single['id']==5 && children.single['parent_id']==3 &&
      snap.seq.any((row)=>row['name']=='d18_parent' && row['seq']==100),
      'D18_NEGATIVE_SOURCE_CONTENT_CHANGED');
  } finally {await q.close();}
  await assertNoCipherDestination();
}
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final phase=Uri.base.queryParameters['phase']??'';
  try{
    switch(phase){
      case 'seed':await seed();break;
      case 'seed_missing_trigger':await seedWithMissingTrigger();break;
      case 'migrate':await migrate();break;
      case 'assert_missing_source_untouched':
        await assertMissingSourceUntouched();break;
      case 'assert_missing_trigger_untouched':
        await assertMissingTriggerUntouched();break;
      case 'verify':await verify();break;
      case 'physical_bytes':await raw();break;
      default:throw StateError('INVALID_PHASE');
    }
    html.document.title='D18_CANDIDATE_MIGRATION_PASS:'+phase;
  }catch(e){
    // A safe whitelist of synthetic failure codes, never raw exception text:
    // SQL errors can expose user-supplied content in future implementations.
    const safeCodes=<String>[
      'D18_SOURCE_MISSING_BEFORE_REOPEN',
      'D18_SEED_NOT_PERSISTED',
      'D18_SOURCE_VERSION_NOT_12',
      'D18_SOURCE_SYNTHETIC_TABLES_MISSING',
      'D18_SOURCE_SYNTHETIC_INDEX_MISSING',
      'D18_SOURCE_SYNTHETIC_VIEW_MISSING',
      'D18_SOURCE_SYNTHETIC_TRIGGER_MISSING',
    ];
    final message=e.toString();
    final code=safeCodes.where((s)=>message.contains(s)).firstOrNull
        ?? 'D18_CI_UNCLASSIFIED_ERROR';
    html.document.documentElement?.dataset['d18FullError']=code;
    html.document.title='D18_CANDIDATE_MIGRATION_FAIL:'+phase;
  }
  runApp(const SizedBox.shrink());
}
