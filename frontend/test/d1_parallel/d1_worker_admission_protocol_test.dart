import 'dart:async';
import 'dart:typed_data';

import 'package:amina/data/drift/d1_worker_admission_protocol.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

final class _FakeWorker implements D1EncryptedWorkerPort {
  bool cipherOk = true;
  bool closed = false;
  final pending = Completer<void>();
  bool blockOpen = false;
  Uint8List? received;
  @override
  Future<void> openWithKey(String ownerName, Uint8List key) async {
    received = Uint8List.fromList(key);
    if (blockOpen) await pending.future;
  }
  @override
  Future<bool> verifyEncryptedConnection() async => cipherOk;
  @override
  Future<void> close() async { closed = true; }
}
void main() {
  final a = PatientVaultScope.nativeDjango(734);
  final b = PatientVaultScope.nativeDjango(812);
  final syntheticKey = Uint8List.fromList(List<int>.generate(32,(i)=>i+1));
  test('D1-A: reject audit namespace, no query before key', () {
    expect(() => D1WorkerAdmissionProtocol(
      scope:PatientVaultScope.auditOnly(),authEpoch:1,
      currentEpoch:()=>1,currentScope:()=>a,
    ),throwsStateError);
    final gate=D1WorkerAdmissionProtocol(scope:a,authEpoch:1,
      currentEpoch:()=>1,currentScope:()=>a);
    expect(gate.assertQueryAllowed,throwsStateError);
  });
  test('D1-A: deny missing/zero key or unverified cipher, close on failure', () async {
    final gate=D1WorkerAdmissionProtocol(scope:a,authEpoch:2,
      currentEpoch:()=>2,currentScope:()=>a);
    final worker=_FakeWorker()..cipherOk=false;
    await expectLater(gate.admit(keyMaterial:Uint8List(32),port:worker),throwsStateError);
    expect(worker.closed,isFalse); // rejected before opening
    await expectLater(gate.admit(keyMaterial:syntheticKey,port:worker),throwsStateError);
    expect(worker.closed,isTrue);
    expect(gate.assertQueryAllowed,throwsStateError);
  });
  test('D1-A: fake verified cipher admits owner A, not B', () async {
    var current=a;
    final gate=D1WorkerAdmissionProtocol(scope:a,authEpoch:7,
      currentEpoch:()=>7,currentScope:()=>current);
    final worker=_FakeWorker();
    await gate.admit(keyMaterial:syntheticKey,port:worker);
    expect(gate.ready,isTrue);
    gate.assertQueryAllowed();
    current=b;
    expect(gate.ready,isFalse);
    expect(gate.assertQueryAllowed,throwsStateError);
    gate.retire();
    expect(gate.assertQueryAllowed,throwsStateError);
  });
  test('D1-A: auth epoch switch DURING open denies publication, closes worker',() async{
    var epoch=12;
    final gate=D1WorkerAdmissionProtocol(scope:a,authEpoch:12,
      currentEpoch:()=>epoch,currentScope:()=>a);
    final worker=_FakeWorker()..blockOpen=true;
    final pending=gate.admit(keyMaterial:syntheticKey,port:worker);
    await Future<void>.delayed(Duration.zero);
    epoch=13;
    gate.retire();
    worker.pending.complete();
    await expectLater(pending,throwsStateError);
    expect(worker.closed,isTrue);
    expect(gate.ready,isFalse);
  });
}
