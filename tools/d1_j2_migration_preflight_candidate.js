// D1/J2 SYNTHETIC only: read-only legacy migration preflight candidate.
// No access to clinical IndexedDB records, no copying/deleting, no authority.
// Caller attestations are NOT independently verified here: success only means
// READY FOR HUMAN/SECURITY REVIEW, NEVER permission to migrate patients.
(() => {
 'use strict';
 const native=/^amina_vault_v1_native_([1-9][0-9]*)$/;
 const device=/^amina_vault_v1_device_([0-9a-f]{32})$/;
 const reserved=/^(amina|amina_vault_v1_(native_|device_))/;
 const deny=(code,details={})=>Object.freeze({
   code,readyForHumanReview:false,authorizedToMigrate:false,...details
 });
 async function inspect(request){
   // No implicit account inference from bearer, email, browser storage or
   // the old "amina" database. All authority must be separately established.
   if(typeof indexedDB.databases!=='function')
     return deny('J2_INDEXEDDB_INVENTORY_UNSUPPORTED');
   let databases;
   try{
     databases=await indexedDB.databases();
     if(!Array.isArray(databases)||databases.some(x=>typeof x.name!=='string'))
       return deny('J2_INVENTORY_AMBIGUOUS');
   }catch(e){return deny('J2_INDEXEDDB_INVENTORY_FAILED');}
   if(typeof navigator.serviceWorker?.getRegistrations!=='function')
     return deny('J2_SERVICE_WORKER_INVENTORY_UNSUPPORTED');
   let writers;
   try{writers=await navigator.serviceWorker.getRegistrations();}
   catch(e){return deny('J2_SERVICE_WORKER_INVENTORY_FAILED');}
   // An installed worker is still capable of executing offline: no claim
   // that new code can decommission it remotely.
   if(writers.length!==0)return deny('J2_UNFENCED_INSTALLED_WORKER',
     {writerRegistrations:writers.length});
   const rawNames=databases.map(x=>x.name).filter(n=>reserved.test(n));
   if(!rawNames.length)return deny('J2_NO_MIGRATABLE_LEGACY_SOURCE');
   if(rawNames.includes('amina'))return deny('J2_LEGACY_UNOWNED_AMBIGUOUS');
   if(rawNames.some(n=>!native.test(n)&&!device.test(n)))
     return deny('J2_LEGACY_NAMESPACE_UNTRUSTED');
   if(rawNames.length!==1)return deny('J2_MULTIPLE_LEGACY_OWNERS');
   const name=rawNames[0],n=name.match(native),d=name.match(device);
   if(!request||request.sourceName!==name)
     return deny('J2_EXPLICIT_SOURCE_SELECTION_REQUIRED');
   if(n){
     if(request.ownerType!=='native'||
        !Number.isSafeInteger(request.nativeId)||request.nativeId<=0||
        String(request.nativeId)!==n[1])
       return deny('J2_NATIVE_IDENTITY_SCOPE_MISMATCH');
     if(request.remoteAccountVerified!==true)
       return deny('J2_VERIFIED_REMOTE_ACCOUNT_REQUIRED');
   }else{
     if(request.ownerType!=='device'||request.deviceScopeId!==d[1]||
        request.deviceOwnershipVerified!==true)
       return deny('J2_VERIFIED_DEVICE_OWNER_REQUIRED');
   }
   if(request.sourcePossessionVerified!==true)
     return deny('J2_SOURCE_POSSESSION_REQUIRED');
   if(request.explicitConsent!==true)
     return deny('J2_EXPLICIT_PATIENT_CONSENT_REQUIRED');
   if(request.backupRestoreIndependentlyVerified!==true||
      !/^[0-9a-f]{64}$/.test(request.backupManifestSha256||''))
     return deny('J2_INDEPENDENT_BACKUP_RESTORE_PROOF_REQUIRED');
   if(request.writerRetirementAttested!==true)
     return deny('J2_WRITER_FENCING_PROOF_REQUIRED');
   // Passing a boolean here is merely a test fixture; do not turn an
   // asserted bit into clinical authorization. Actual migration requires
   // signed/verifiable evidence and independent security/human review.
   return Object.freeze({
     code:'J2_READY_FOR_EXTERNAL_SECURITY_REVIEW',
     readyForHumanReview:true,authorizedToMigrate:false,
     scopeKind:n?'native':'device',sourceName:name,
     requiredExternalGates:[
       'independent_identity_and_possession_validation',
       'backup_hash_and_new_profile_restore_verification',
       'installed_pwa_writer_retirement_on_every_target_device',
       'patient_consent_record_and_reversible_migration',
       'independent_security_review_and_human_go'
     ]
   });
 }
 Object.defineProperty(globalThis,'IaminaD1J2PreflightCandidate',{
   value:Object.freeze({inspect}),configurable:false,writable:false
 });
})();