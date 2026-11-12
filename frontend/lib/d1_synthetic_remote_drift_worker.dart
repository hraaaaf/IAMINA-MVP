// D1 isolated research: WebWorker serves a REAL DriftServer + SQLite3MC
// after a one-use transferred test key. NEVER used for clinical accounts.
// ignore: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'package:web/web.dart' as web;
import 'package:drift/remote.dart';
import 'package:drift/web.dart';
import 'package:drift/wasm.dart';
import 'package:sqlite3/wasm.dart';

const _owner = 'amina_vault_v1_native_731';
const _idb = 'd1_synthetic_remote_drift_731';

Future<void> _open(web.DedicatedWorkerGlobalScope self, JSObject msg) async {
  IndexedDbFileSystem? storage;
  String stage='VALIDATE';
  try {
    final owner=(msg['owner'] as JSString?)?.toDart;
    final epoch=(msg['epoch'] as JSNumber?)?.toDartInt;
    final keyJs=msg['key'] as JSUint8Array?;
    if(owner!=_owner||epoch==null||epoch<1||keyJs==null) {
      self.postMessage('FAIL_MISSING_OR_FOREIGN_OWNER_KEY'.toJS);
      return;
    }
    final key=keyJs.toDart;
    if(key.length!=32 || key.every((b)=>b==0)){
      self.postMessage('FAIL_INVALID_KEY'.toJS);return;
    }
    // Keep the key only in the worker and never log or serialize it.
    // The client sends a transferable Uint8Array; this is an experiment,
    // NOT a reviewed credential-admission mechanism.
    final hex=key.map((v)=>v.toRadixString(16).padLeft(2,'0')).join();
    key.fillRange(0,key.length,0);
    final port=msg['port'] as web.MessagePort;
    stage='IDB';
    storage=await IndexedDbFileSystem.open(dbName:_idb,writeAutomatically:false);
    stage='WASM';
    final sqlite=await WasmSqlite3.loadFromUrlString('sqlite3mc.wasm');
    sqlite.registerVirtualFileSystem(storage);
    stage='SQLITE';
    final sql=sqlite.open('/database',vfs:'multipleciphers-${storage.name}');
    try{
      stage='CIPHER';
      if(sql.select('PRAGMA cipher').isEmpty)throw StateError('CIPHER_UNAVAILABLE');
      stage='KEY';
      sql.execute("PRAGMA key = '$hex'");
      // Reject wrong key BEFORE exposing a DriftServer.
      stage='VERIFY';
      sql.select('SELECT count(*) FROM sqlite_master');
      final executor=WasmDatabase.opened(sql,closeUnderlyingOnClose:false);
      try{
        stage='SERVER';
        // A dedicated, one-use worker allows its sole owner to terminate the
        // server. Keep the executor open until the physical VFS is flushed.
        final server=DriftServer(executor,
          allowRemoteShutdown:true,closeConnectionAfterShutdown:false);
        self.postMessage('D1_REMOTE_READY'.toJS);
        await server.serve(port.channel());
      }finally{
        await executor.close();
      }
    }finally{
      sql.close();
    }
    stage='FLUSH';
    await storage.flush();
    await storage.close();
    storage=null;
    self.postMessage('D1_REMOTE_FLUSHED'.toJS);
  }catch(_){
    // Never include key, SQL string or database details in responses.
    self.postMessage('FAIL_$stage'.toJS);
  }finally{
    try{await storage?.close();}catch(_){}
  }
}
void main(){
  final self=globalContext as web.DedicatedWorkerGlobalScope;
  var connected=false;
  web.EventStreamProviders.messageEvent.forTarget(self).listen((event){
    if(connected){self.postMessage('FAIL_ALREADY_BOUND'.toJS);return;}
    connected=true;
    try{
      final msg=event.data as JSObject;
      unawaited(_open(self,msg));
    }catch(_){self.postMessage('FAIL_REQUEST'.toJS);}
  });
}
