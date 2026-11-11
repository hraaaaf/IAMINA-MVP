import 'dart:async';

import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/d1_session_fence.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final a = PatientVaultScope.nativeDjango(734);
  final b = PatientVaultScope.nativeDjango(812);

  test('D1-C: no unowned or audit vault can issue a clinical fence', () {
    expect(() => D1SessionFence(PatientVaultScope.auditOnly(), 3),throwsStateError);
    expect(() => D1SessionFence(a, -1),throwsStateError);
  });

  test('D1-C: A->logout->B->A, revoked A tickets never revived', () {
    final oldA = D1SessionFence(a, 10);
    final oldTicket = oldA.beginOperation(currentScope:a,currentAuthEpoch:10);
    expect(oldA.canPublish(oldTicket,currentScope:a,currentAuthEpoch:10),isTrue);
    oldA.retire();
    expect(oldA.canPublish(oldTicket,currentScope:a,currentAuthEpoch:10),isFalse);
    expect(oldA.canPublish(oldTicket,currentScope:b,currentAuthEpoch:11),isFalse);
    final sessionB=D1SessionFence(b,11);
    final ticketB=sessionB.beginOperation(currentScope:b,currentAuthEpoch:11);
    expect(sessionB.canPublish(ticketB,currentScope:b,currentAuthEpoch:11),isTrue);
    expect(sessionB.canPublish(ticketB,currentScope:a,currentAuthEpoch:11),isFalse);
    sessionB.retire();
    final freshA=D1SessionFence(a,12);
    final freshTicket=freshA.beginOperation(currentScope:a,currentAuthEpoch:12);
    expect(freshA.canPublish(freshTicket,currentScope:a,currentAuthEpoch:12),isTrue);
    expect(oldA.canPublish(oldTicket,currentScope:a,currentAuthEpoch:12),isFalse);
  });

  test('D1-C: stale async completion is discarded after switch', () async {
    final fence=D1SessionFence(a,31);
    final ticket=fence.beginOperation(currentScope:a,currentAuthEpoch:31);
    final pending=Completer<String>();
    final result=pending.future.then((value){
      fence.assertCanPublish(ticket,currentScope:b,currentAuthEpoch:32);
      return value;
    });
    fence.retire();
    pending.complete('synthetic-measure-from-A');
    await expectLater(result,throwsStateError);
  });

  test('D1-C: epoch change alone rejects stale publish and operations', () {
    final fence=D1SessionFence(a,5);
    final ticket=fence.beginOperation(currentScope:a,currentAuthEpoch:5);
    expect(fence.canPublish(ticket,currentScope:a,currentAuthEpoch:6),isFalse);
    expect(()=>fence.beginOperation(currentScope:a,currentAuthEpoch:6),throwsStateError);
  });

  test('D1-C: audit namespace cannot be mistaken for a device session', () {
    const uuid='ab234567-1234-4abc-8def-123456789abc';
    final device=PatientVaultScope.deviceLocal(uuid);
    final fence=D1SessionFence(device,12);
    final ticket=fence.beginOperation(currentScope:device,currentAuthEpoch:12);
    expect(fence.canPublish(ticket,currentScope:a,currentAuthEpoch:12),isFalse);
  });
}
