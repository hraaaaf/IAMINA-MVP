// D1 J1→J2 TEST-ONLY cross-proof: the test runner plays an independent
// witness and checks an Ed25519 receipt against a NEW browser profile restore
// and an unchanged LIVE synthetic source before invoking J2 preflight.
//
// This is not a production trust root: the short-lived private key exists
// only in the CI runner. Real trusted issuer/auth/anti-replay absent.
// No clinical records, migration, destructive rollback or GO are possible.
'use strict';
const {chromium}=require('playwright');
const {generateKeyPairSync,sign,verify,randomUUID}=require('node:crypto');
const fs=require('fs');
const {inventoryAndBackup,restore}=require('./d1_j1_synthetic_backup_restore_browser');
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',
  clinicalGo:false,realIssuerConnected:false,permissionToMigrate:false,
  rollbackMode:'old source preserved; incomplete staging quarantined',
  checks:{},result:'NOT_RUN'};
const dir='d1-j1-j2-integrated-proof';
const origin='http://127.0.0.1:7481/';
const owner='amina_vault_v1_native_734';
const expectedOwner=734;
function assert(v,k){if(!v)throw Error('J1J2_ASSERT_'+k);}
function req(r){return new Promise((resolve,reject)=>{
  r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
});}
async function seed(page){
  return page.evaluate(async name=>{
    const p=req=>new Promise((res,rej)=>{
      req.onsuccess=()=>res(req.result);req.onerror=()=>rej(req.error);
    });
    const create=indexedDB.open(name,2);
    create.onupgradeneeded=()=>{
      const store=create.result.createObjectStore('records',{keyPath:'id'});
      store.createIndex('by_kind','kind',{unique:false});
    };
    const db=await p(create);
    try{
      const tx=db.transaction('records','readwrite');
      tx.objectStore('records').put({id:734,kind:'synthetic-test',
        stamp:new Date('2026-11-14T00:00:00Z'),
        payload:new Uint8Array([0,1,128,254,255]).buffer,
        text:'D1_SYNTHETIC_734'});
      await new Promise((res,rej)=>{
        tx.oncomplete=res;tx.onerror=()=>rej(tx.error);
        tx.onabort=()=>rej(tx.error);
      });
    }finally{db.close();}
  },owner);
}
async function mutate(page){
  return page.evaluate(async name=>{
    const open=indexedDB.open(name);
    const db=await new Promise((res,rej)=>{
      open.onsuccess=()=>res(open.result);open.onerror=()=>rej(open.error);
    });
    try{
      const tx=db.transaction('records','readwrite');
      tx.objectStore('records').put({id:734,kind:'changed-after-backup',
        payload:new Uint8Array([9,9,9]).buffer});
      await new Promise((res,rej)=>{
        tx.oncomplete=res;tx.onerror=()=>rej(tx.error);
        tx.onabort=()=>rej(tx.error);
      });
    }finally{db.close();}
  },owner);
}
const attested={sourceName:owner,ownerType:'native',nativeId:expectedOwner,
  remoteAccountVerified:true,sourcePossessionVerified:true,
  explicitConsent:true,writerRetirementAttested:true};
const wire=async(page,request)=>page.evaluate(
  request=>IaminaD1J2PreflightCandidate.inspect(request),request);

(async()=>{
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const source=await browser.newContext({locale:'en-US',serviceWorkers:'allow'});
  const a=await source.newPage();
  await a.goto(origin);
  await seed(a);
  const initial=await inventoryAndBackup(a,[owner]);
  assert(initial.payload.databases.length===1,'one_owner_backup');
  assert(initial.payload.databases[0].name===owner,'source_name');
  proof.initialSourceSha256=initial.sha256;

  // J2 MUST NOT advance on the caller-supplied backup flag alone.
  const notLinked=await wire(a,{...attested,
    backupRestoreIndependentlyVerified:false,
    backupManifestSha256:initial.sha256});
  assert(notLinked.code==='J2_INDEPENDENT_BACKUP_RESTORE_PROOF_REQUIRED',
    'missing_J1_witness_must_deny');
  proof.checks.missingWitnessDenied=true;

  const clean=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  const b=await clean.newPage();await b.goto(origin);
  const restored=await restore(b,initial);
  assert(restored===true,'fresh_profile_restore');
  const target=await inventoryAndBackup(b,[owner]);
  assert(target.sha256===initial.sha256,'independent_recovery_hash');
  proof.checks.independentRecoveryMatches=true;

  const issuer=generateKeyPairSync('ed25519');
  const attacker=generateKeyPairSync('ed25519');
  const expiresAt=Date.now()+120000;
  const payload={version:1,sourceName:owner,sourceSha256:initial.sha256,
    restoredSha256:target.sha256,nonce:randomUUID(),expiresAt,
    kind:'iamina-d1-j1-ci-synthetic-witness'};
  const canonical=JSON.stringify(payload);
  const receipt={payload,signature:sign(null,Buffer.from(canonical),
    issuer.privateKey).toString('base64url')};
  const verified=(r,key=issuer.publicKey,sourceSha=initial.sha256,
     sourceName=owner)=>{
    if(!r||r.payload?.kind!=='iamina-d1-j1-ci-synthetic-witness'||
       r.payload?.version!==1||r.payload?.sourceName!==sourceName||
       r.payload?.sourceSha256!==sourceSha||
       r.payload?.restoredSha256!==r.payload?.sourceSha256||
       !Number.isSafeInteger(r.payload?.expiresAt)||
       Date.now()>r.payload.expiresAt||
       typeof r.signature!=='string')return false;
    try{
      return verify(null,Buffer.from(JSON.stringify(r.payload)),
        key,Buffer.from(r.signature,'base64url'));
    }catch(e){return false;}
  };
  assert(verified(receipt),'trusted_receipt');
  proof.checks.witnessSignatureAndSourceBound=true;

  // Integration gate is implemented only in this trusted CI harness. The
  // existing J2 candidate still accepts declarative booleans, so this is
  // NOT production authorization or fully connected J1→J2.
  const current=await inventoryAndBackup(a,[owner]);
  assert(verified(receipt,issuer.publicKey,current.sha256,owner),
    'current_source_unchanged');
  const review=await wire(a,{...attested,
    backupRestoreIndependentlyVerified:true,
    backupManifestSha256:receipt.payload.sourceSha256});
  assert(review.code==='J2_READY_FOR_EXTERNAL_SECURITY_REVIEW' &&
    review.authorizedToMigrate===false,'review_only');
  proof.checks.sourceBoundReviewOnly=true;

  const forged={payload:{...receipt.payload,sourceName:
      'amina_vault_v1_native_812'},signature:receipt.signature};
  assert(!verified(forged),'tampered_receipt_accepted');
  proof.checks.tamperedReceiptRejected=true;
  const wrongIssuer={
    payload:receipt.payload,
    signature:sign(null,Buffer.from(JSON.stringify(receipt.payload)),
      attacker.privateKey).toString('base64url')
  };
  assert(!verified(wrongIssuer),'self_signed_receipt_accepted');
  proof.checks.selfSignedReceiptRejected=true;
  assert(!verified(receipt,issuer.publicKey,initial.sha256,
    'amina_vault_v1_native_812'),'owner_switch_receipt_accepted');
  proof.checks.ownerMismatchRejected=true;
  const expiredPayload={...receipt.payload,expiresAt:Date.now()-1};
  const expired={payload:expiredPayload,
    signature:sign(null,Buffer.from(JSON.stringify(expiredPayload)),
      issuer.privateKey).toString('base64url')};
  assert(!verified(expired),'expired_receipt_accepted');
  proof.checks.expiredReceiptRejected=true;

  // A mid-restore crash leaves partial STAGING. It must NEVER be advertised
  // as rolled back or usable; the original source remains intact and a new
  // empty profile can be restored from the verified archive.
  const partial=await browser.newContext({
    locale:'en-US',serviceWorkers:'block'});
  const c=await partial.newPage();await c.goto(origin);
  let interrupted=false;
  try{await restore(c,initial,{simulateAbortAfterDatabase:1});}
  catch(e){interrupted=String(e).includes(
    'J1_SIMULATED_POWER_LOSS_STAGED_PARTIAL');}
  assert(interrupted,'expected_interruption_not_observed');
  proof.checks.interruptionObserved=true;
  let overwriteDenied=false;
  try{await restore(c,initial);}
  catch(e){overwriteDenied=String(e).includes('J1_RESTORE_TARGET_NOT_EMPTY');}
  assert(overwriteDenied,'partial_staging_was_silently_resumed');
  proof.checks.partialDestinationQuarantined=true;
  // The full data might exist in partial staging, but no verified witness
  // is issued for that aborted session, hence no migration may proceed.
  const afterInterrupt=await inventoryAndBackup(a,[owner]);
  assert(afterInterrupt.sha256===initial.sha256,
    'source_corrupted_by_interruption');
  proof.checks.originalPreservedAfterCrash=true;
  const resume=await browser.newContext({
    locale:'en-US',serviceWorkers:'block'});
  const d=await resume.newPage();await d.goto(origin);
  await restore(d,initial);
  const fresh=await inventoryAndBackup(d,[owner]);
  assert(fresh.sha256===initial.sha256,'new_profile_recovery_failed');
  proof.checks.recoveredInNewEmptyProfile=true;

  // After backup, a stale offline writer is free to mutate the old source.
  // Compare against LIVE source data, not an earlier signed manifest.
  await mutate(a);
  const changed=await inventoryAndBackup(a,[owner]);
  assert(changed.sha256!==initial.sha256,'mutation_undetected');
  assert(!verified(receipt,issuer.publicKey,changed.sha256,owner),
    'stale_receipt_accepted_after_source_change');
  proof.checks.staleReceiptDeniedAfterSourceMutation=true;
  // Still never authorize migration merely because J2 returned REVIEW.
  assert(review.authorizedToMigrate===false,'clinical_gate_not_closed');

  // Installed Service Worker is a separate writer fence (tested on source).
  const installed=await a.evaluate(async()=>{
    const r=await navigator.serviceWorker.register('/j2-legacy-sw.js');
    await navigator.serviceWorker.ready;return !!r.active;
  });
  assert(installed,'installed_service_worker');
  const blocked=await wire(a,{...attested,
    backupRestoreIndependentlyVerified:true,
    backupManifestSha256:initial.sha256});
  assert(blocked.code==='J2_UNFENCED_INSTALLED_WORKER' &&
    blocked.authorizedToMigrate===false,
    'legacy_offline_writer_bypassed');
  proof.checks.activeLegacyWorkerBlocks=true;
  await Promise.all([source.close(),clean.close(),partial.close(),
    resume.close()]);
  proof.result='PASS_SYNTHETIC_CROSS_GATE_NO_CLINICAL_AUTHORITY';
 }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,3000);
   throw e;}
 finally{
  fs.writeFileSync(dir+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J1_J2_INTEGRATED_GATES='+JSON.stringify(proof));
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});