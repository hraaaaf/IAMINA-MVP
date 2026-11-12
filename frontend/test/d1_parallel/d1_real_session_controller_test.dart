import 'dart:async';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthChanged extends ChangeNotifier {
 void change()=>notifyListeners();
}
void main(){
 test('D1 integrated: old scope ticket revoked synchronously on logout',() async{
  final notifier=_AuthChanged();
  addTearDown(notifier.dispose);
  var owner=PatientVaultScope.nativeDjango(734);
  final gate=PatientVaultSessionController(
   authChanges:notifier,
   resolveScope:()=>Future.value(owner),
   openDatabase:(scope)=>AppDatabase.testPatientVault(NativeDatabase.memory(),scope),
  );
  addTearDown(gate.dispose);
  await gate.reconcile();
  final oldFence=gate.activeSessionFence!;
  final oldTicket=oldFence.beginOperation(currentScope:owner,currentAuthEpoch:AuthEpoch.value);
  expect(oldFence.canPublish(oldTicket,currentScope:owner,currentAuthEpoch:AuthEpoch.value),isTrue);
  owner=PatientVaultScope.nativeDjango(812);
  AuthEpoch.advance();
  notifier.change();
  expect(oldFence.isRetired,isTrue);
  expect(gate.activeSessionFence,isNull);
  expect(gate.activeDatabase,isNull);
  await gate.reconcile();
  expect(gate.activeScope?.nativeDjangoUserId,812);
  expect(gate.activeSessionFence,isNotNull);
  expect(oldFence.canPublish(oldTicket,currentScope:owner,currentAuthEpoch:AuthEpoch.value),isFalse);
 });
 test('D1 integrated: stale A async read cannot publish after account B',() async{
  final notifier=_AuthChanged();
  addTearDown(notifier.dispose);
  var owner=PatientVaultScope.nativeDjango(734);
  final gate=PatientVaultSessionController(
   authChanges:notifier,
   resolveScope:()=>Future.value(owner),
   openDatabase:(scope)=>AppDatabase.testPatientVault(NativeDatabase.memory(),scope),
  );
  addTearDown(gate.dispose);
  await gate.reconcile();
  final fence=gate.activeSessionFence!;
  final token=fence.beginOperation(currentScope:owner,currentAuthEpoch:AuthEpoch.value);
  final pending=Completer<String>();
  final result=pending.future.then((marker){
   fence.assertCanPublish(token,currentScope:owner,currentAuthEpoch:AuthEpoch.value);
   return marker;
  });
  owner=PatientVaultScope.nativeDjango(812);
  AuthEpoch.advance();
  notifier.change();
  pending.complete('synthetic-owner-A-data');
  await expectLater(result,throwsStateError);
  await gate.reconcile();
  expect(gate.activeScope?.nativeDjangoUserId,812);
 });
}
