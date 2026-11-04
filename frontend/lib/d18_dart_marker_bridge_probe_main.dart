// D18 CI-ONLY Flutter Web entrypoint. No real patient credentials or runtime.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;
import 'package:flutter/widgets.dart';
import 'data/drift/d18_pre_cutover_atomic_promotion.dart';
import 'data/drift/d18_pre_cutover_idb_marker_store_web.dart';
import 'data/drift/patient_vault_scope.dart';

final scope=PatientVaultScope.nativeDjango(734);
const store=D18PreCutoverIndexedDbMarkerStore();
const shaA='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
const shaB='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';

D18CutoverProof proof()=>D18CutoverProof(
  sourceName:scope.databaseName,
  targetName:scope.databaseName+'_d18_cipher_v1',
  sourceLogicalSha256:shaA,targetLogicalSha256:shaA,
  persistedCiphertextSha256:shaB,schemaVersion:12,
  sourcePresent:true,targetPresent:true,
  sourceIntegrityOk:true,targetIntegrityOk:true,
  sourceForeignKeysOk:true,targetForeignKeysOk:true,
  authenticatedCiphertextReopened:true,
  independentRecoveryArchiveVerified:true,
);
D18PreCutoverAtomicPromotion contract()=>D18PreCutoverAtomicPromotion(
  scope:scope,markerStore:store,
  resolveAuthenticatedScope:() async=>scope,readAuthEpoch:()=>1,
  isKeyLocked:()=>false,allPlaintextWritersQuiesced:()=>true,
  exclusiveOriginBarrierHeld:()=>true,
  // Explicit test fixture ONLY; live marker promotion stays denied by default.
  allowUnfencedSyntheticFixture:true,
  inspectUnderBarrier:() async=>proof(),
);
void check(bool ok,String code){
  if(!ok)throw StateError(code);
}
Future<void> mustReject(Future<void> Function() operation,String code) async {
  var denied=false;
  try{await operation();}on StateError{denied=true;}
  check(denied,code);
}
Future<void> phase(String name) async {
  switch(name){
    case 'prepare':
      check((await contract().prepare()).phase==D18CutoverPhase.prepared,
        'D18_DART_PREPARE_NOT_PENDING');
      break;
    case 'read_prepared':
      check((await contract().inspectMarker())?.phase==
        D18CutoverPhase.prepared,'D18_DART_PENDING_NOT_READABLE');
      break;
    case 'stale_prepare':
      await mustReject(() async{await contract().prepare();},
        'D18_DART_STALE_PREPARE_ACCEPTED');
      break;
    case 'activate':
      check((await contract().activateForSyntheticTest(
        explicitSyntheticApproval:true)).phase==
        D18CutoverPhase.ciphertextActive,'D18_DART_ACTIVATION_FAILED');
      break;
    case 'read_active':
      check((await contract().inspectMarker())?.phase==
        D18CutoverPhase.ciphertextActive,'D18_DART_ACTIVE_LOST');
      break;
    case 'replay_denied':
      await mustReject(() async{await contract().activateForSyntheticTest(
        explicitSyntheticApproval:true);},'D18_DART_REPLAY_ACCEPTED');
      break;
    case 'other_scope_empty':
      check(await store.read(PatientVaultScope.nativeDjango(812))==null,
        'D18_DART_CROSS_PATIENT_MARKER');
      break;
    case 'audit_scope_denied':
      await mustReject(() async{
        await store.read(PatientVaultScope.auditOnly());
      },'D18_DART_AUDIT_SCOPE_ACCEPTED');
      break;
    case 'reverse_transition_denied':
      final active=await store.read(scope);
      check(active?.phase==D18CutoverPhase.ciphertextActive,
        'D18_DART_NOT_ACTIVE_FOR_REVERSE');
      await mustReject(() async{
        await store.compareAndSwap(
          scope:scope,expected:active,
          next:active!.withPhase(D18CutoverPhase.prepared));
      },'D18_DART_REVERSE_ACCEPTED');
      break;
    default:throw StateError('D18_DART_BAD_PHASE');
  }
}
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final step=Uri.base.queryParameters['phase']??'';
  try{
    await phase(step);
    html.document.title='D18_DART_MARKER_PASS:'+step;
  }catch(e){
    // Diagnostics only; never dump a key, SQL or a browser storage payload.
    html.document.documentElement?.dataset['d18DartMarkerError']=
      e.runtimeType.toString();
    html.document.title='D18_DART_MARKER_FAIL:'+step;
  }
  runApp(const SizedBox.shrink());
}
