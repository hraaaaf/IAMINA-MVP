// ignore_for_file: experimental_member_use, avoid_web_libraries_in_flutter, deprecated_member_use
// D18 CI-ONLY: disposable whole-schema source -> separately KEYED sqlite3mc.
// NEVER import this file from the application or use it with patient records.
// No cutover, no source deletion, no plaintext destination or static key.
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
const dstName='amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018_d18_ci_dynamic';
const abortName='amina_vault_v1_device_e2dbe28f3eea441086a7274150b00018_d18_ci_dynamic';
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
  final opened=await WasmDatabase.open(
    databaseName:srcName,sqlite3Uri:Uri.parse('sqlite3.wasm'),
    driftWorkerUri:Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs:false);
  check(opened.chosenImplementation.name=='sharedIndexedDb',
    'UNSUPPORTED_SOURCE_STORAGE');
  final q=opened.resolvedExecutor;
  await q.ensureOpen(const NoMigrations());
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
Future<Encrypted> openDestination({String databaseName=dstName}) async {
  stage('keyed_worker_handshake');
  final keyField=databaseName==abortName ? '__D18_FULL_ABORT_KEY' : '__D18_FULL_KEY';
  final k=globalContext.getProperty(keyField.toJS);
  check(k is JSUint8Array,'NO_DYNAMIC_TEST_KEY');
  final bytes=Uint8List.fromList((k as JSUint8Array).toDart);
  check(bytes.length==32,'INVALID_KEY_LENGTH');
  final worker=web.Worker('d18_dynamic_cipher_sqlite_worker.js'.toJS);
  final control=web.MessageChannel(),sql=web.MessageChannel();
  try{
    final buffer=bytes.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final payload=JSObject()
      ..setProperty('type'.toJS,'D18_CI_DYNAMIC_SQL_OPEN'.toJS)
      ..setProperty('name'.toJS,databaseName.toJS)
      ..setProperty('key'.toJS,buffer);
    final ready=web.EventStreamProviders.messageEvent.forTarget(control.port1)
      .first.timeout(const Duration(seconds:25));
    control.port1.start();
    worker.postMessage(payload,<JSObject>[control.port2,sql.port2,buffer].toJS);
    bytes.fillRange(0,bytes.length,0);
    final status=((await ready).data as JSString).toDart;
    check(status=='READY','DESTINATION_OPEN_REJECTED');
    final c=await connectToRemoteAndInitialize(
      sql.port1.channel(explicitClose:true));
    await c.ensureOpen(const NoMigrations());
    return Encrypted(worker,control.port1,sql.port1,c.executor);
  }catch(_){control.port1.close();sql.port1.close();worker.terminate();rethrow;}
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
Future<void> migrate() async {
  stage('preflight_source');
  final src=await openSource();
  late final Snap original;
  try{
    await integrity(src);
    original=await snapshot(src);
    check(original.schema.any((x)=>x['name']=='d18_child_trigger')&&
      original.schema.any((x)=>x['name']=='d18_parent_view')&&
      original.schema.any((x)=>x['name']=='d18_parent_label_idx'),
      'MISSING_DYNAMIC_SCHEMA');
  }finally{await src.close();}
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
      for(final seq in original.seq){
        await q.runCustom(
          'INSERT OR REPLACE INTO sqlite_sequence(name,seq) VALUES(?,?)',
          [seq['name'],seq['seq']]);
      }
      for(final kind in ['index','view','trigger']){
        for(final o in original.schema.where((o)=>
          o['type']==kind && o['sql']!=null)){
          await q.runCustom(o['sql'] as String,[]);
        }
      }
      await q.runCustom('PRAGMA user_version='+original.version.toString(),[]);
      await integrity(q);
      compare(original,await snapshot(q));
      await q.runCustom('COMMIT',[]);
    }catch(_){await q.runCustom('ROLLBACK',[]);rethrow;}
  }finally{await target.close();}
  stage('original_preserved');
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
  final dst=await openDestination();
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
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final phase=Uri.base.queryParameters['phase']??'';
  try{
    switch(phase){
      case 'seed':await seed();break;
      case 'abort_rollback':await abortRollback();break;
      case 'migrate':await migrate();break;
      case 'verify':await verify();break;
      case 'physical_bytes':await raw();break;
      default:throw StateError('INVALID_PHASE');
    }
    html.document.title='D18_FULL_PASS:'+phase;
  }catch(e){
    html.document.documentElement?.dataset['d18FullError']=e.runtimeType.toString();
    html.document.title='D18_FULL_FAIL:'+phase;
  }
  runApp(const SizedBox.shrink());
}
