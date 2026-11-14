// D1/J2 SYNTHETIC only: read-only legacy migration preflight candidate.
// No access to clinical IndexedDB records, no copying/deleting, no authority.
// Receipt signature and live J1 digest are checked DIRECTLY within J2.
// The trust anchor is CI-injected SYNTHETIC ONLY, not a production issuer.
// Identity, possession and consent assertions remain externally unverified,
// so REVIEW never means authority to migrate patients.
(() => {
 'use strict';
 const native=/^amina_vault_v1_native_([1-9][0-9]*)$/;
 const device=/^amina_vault_v1_device_([0-9a-f]{32})$/;
 const reserved=/^(amina|amina_vault_v1_(native_|device_))/;
 // Capture the test root at module load. Request-supplied public keys are
 // always ignored. Without an independently provisioned trusted root this
 // control MUST fail closed. This fixture root is NOT a clinical trust root.
 const root=globalThis.IaminaD1J2SyntheticPinnedRoot || null;
 const sourceDigest=globalThis.IaminaD1J2SyntheticSourceDigest || null;
 const consumedNonces=new Set();
 const hashFormat=/^[a-f0-9]{64}$/;
 const b64urlDecode=s=>{
   const clean=s.replace(/-/g,'+').replace(/_/g,'/');
   const raw=atob(clean+'='.repeat((4-clean.length%4)%4));
   return Uint8Array.from(raw,c=>c.charCodeAt(0));
 };
 async function verifyReceipt(request,ownerName,ownerType) {
   if(!request?.receipt)return 'J2_SIGNED_RESTORE_RECEIPT_REQUIRED';
   if(!root||root.mode!=='ci-synthetic-not-production'||
      typeof root.publicKey!=='string'||!sourceDigest?.digest)
     return 'J2_TRUST_ROOT_OR_SOURCE_ORACLE_UNAVAILABLE';
   const {payload,signature}=request.receipt;
   if(!payload||typeof signature!=='string'||signature.length<40||
      payload.kind!=='iamina-d1-j1-ci-synthetic-witness'||
      payload.version!==2||
      payload.issuer!=='IAMINA_D1_CI_SYNTHETIC_ONLY'||
      payload.sourceName!==ownerName||
      payload.ownerType!==ownerType||
      !hashFormat.test(payload.sourceSha256||'')||
      payload.restoredSha256!==payload.sourceSha256||
      typeof payload.nonce!=='string'||
      !/^[0-9a-f-]{36}$/.test(payload.nonce)||
      !Number.isSafeInteger(payload.issuedAt)||
      !Number.isSafeInteger(payload.expiresAt)||
      payload.expiresAt<=payload.issuedAt||
      payload.expiresAt-payload.issuedAt>120000||
      Date.now()<payload.issuedAt-30000||
      Date.now()>payload.expiresAt)
     return 'J2_SIGNED_RESTORE_RECEIPT_INVALID';
   if(consumedNonces.has(payload.nonce))
     return 'J2_RECEIPT_NONCE_REPLAY';
   try {
     if(!globalThis.isSecureContext||!crypto?.subtle)
       return 'J2_SIGNATURE_VERIFIER_UNAVAILABLE';
     const key=await crypto.subtle.importKey(
       'raw',b64urlDecode(root.publicKey),{name:'Ed25519'},false,['verify']);
     const valid=await crypto.subtle.verify(
       {name:'Ed25519'},key,b64urlDecode(signature),
       new TextEncoder().encode(JSON.stringify(payload)));
     if(!valid)return 'J2_SIGNED_RESTORE_RECEIPT_INVALID';
     // Two independent digest reads narrow accidental races, but do not
     // fence an offline old writer that ignores our lock protocol.
     const first=await sourceDigest.digest(ownerName);
     if(first!==payload.sourceSha256)
       return 'J2_LIVE_SOURCE_DIGEST_CHANGED';
     const second=await sourceDigest.digest(ownerName);
     if(second!==first)
       return 'J2_SOURCE_CHANGED_DURING_CHECK';
     consumedNonces.add(payload.nonce);
     return null;
   } catch (_) {
     return 'J2_RECEIPT_OR_SOURCE_VERIFICATION_FAILED';
   }
 }
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
   if(request.writerRetirementAttested!==true)
     return deny('J2_WRITER_FENCING_PROOF_REQUIRED');
   const failure=await verifyReceipt(request,name,n?'native':'device');
   if(failure)return deny(failure);
   // The signed receipt test root, live hash oracle, and replay cache are
   // SYNTHETIC + in memory only. Do not use as real provenance, identity,
   // rollback proof or migration permission.
   return Object.freeze({
     code:'J2_READY_FOR_EXTERNAL_SECURITY_REVIEW',
     readyForHumanReview:true,authorizedToMigrate:false,
     scopeKind:n?'native':'device',sourceName:name,
     requiredExternalGates:[
       'independent_identity_and_possession_validation',
       'production_trust_root_and_server_side_signed_receipt',
       'backup_hash_and_new_profile_restore_verification',
       'server_persisted_nonce_and_account_identity',
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