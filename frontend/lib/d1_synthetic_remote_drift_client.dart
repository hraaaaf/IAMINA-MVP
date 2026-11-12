// D1 CI only; exercises a real remote Drift QueryExecutor in the worker.
// Fake 32-byte test key: not sourced from any patient/login. No app bootstrap.
// ignore: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';
import 'package:drift/remote.dart';
import 'package:drift/web.dart';
import 'package:web/web.dart' as web;

Future<void> main() async{
  final phase=Uri.base.queryParameters['phase']??'';
  html.document.title='D1_REMOTE_RUNNING';
  if(!{'seed','reopen','wrong_key','missing_key'}.contains(phase)){
    html.document.title='D1_REMOTE_FAIL_PHASE';return;
  }
  web.Worker? worker;
  try{
    worker=web.Worker('d1_synthetic_remote_drift_worker.js'.toJS);
    final handshake=Completer<String>();
    web.EventStreamProviders.messageEvent.forTarget(worker).listen((event){
      final msg=(event.data as JSString).toDart;
      if(!handshake.isCompleted)handshake.complete(msg);
    });
    final ports=web.MessageChannel();
    final message=JSObject()
      ..['owner']='amina_vault_v1_native_731'.toJS
      ..['epoch']=17.toJS
      ..['port']=ports.port2;
    final bytes=Uint8List.fromList(List.generate(32,(i)=>i+1));
    if(phase=='wrong_key')bytes[0]=51;
    final jsKey=bytes.toJS;
    if(phase!='missing_key')message['key']=jsKey;
    worker.postMessage(message,phase=='missing_key' ?
      [ports.port2].toJS : [ports.port2, (jsKey['buffer'] as JSArrayBuffer)].toJS);
    bytes.fillRange(0,bytes.length,0);
    final result=await handshake.future.timeout(const Duration(seconds:25));
    if(phase=='missing_key'||phase=='wrong_key'){
      html.document.title=(
        phase=='missing_key'&&result=='FAIL_MISSING_OR_FOREIGN_OWNER_KEY'||
        phase=='wrong_key'&&result=='FAIL_VERIFY'
      ) ? 'D1_REMOTE_PASS_${phase.toUpperCase()}' : 'D1_REMOTE_FAIL_NEGATIVE';
      return;
    }
    if(result!='D1_REMOTE_READY')throw StateError('UNEXPECTED_HANDSHAKE');
    final database=await connectToRemoteAndInitialize(
      ports.port1.channel(), singleClientMode:true,
    );
    try{
      if(phase=='seed'){
        await database.runCustom('CREATE TABLE IF NOT EXISTS d1_remote_records (marker TEXT NOT NULL)');
        await database.runCustom('DELETE FROM d1_remote_records');
        await database.runInsert('INSERT INTO d1_remote_records(marker) VALUES (?)',
          ['D1_DRIFT_REMOTE_SYNTHETIC_731']);
      }
      final rows=await database.runSelect(
        'SELECT marker FROM d1_remote_records', [],
      );
      if(rows.length!=1||rows.single['marker']!='D1_DRIFT_REMOTE_SYNTHETIC_731')
        throw StateError('INVALID_DRIFT_REMOTE_ROW');
    }finally{
      await database.close();
    }
    html.document.title='D1_REMOTE_PASS_${phase.toUpperCase()}';
  }catch(_){
    html.document.title='D1_REMOTE_FAIL_OPERATION';
  }finally{
    worker?.terminate();
  }
}
