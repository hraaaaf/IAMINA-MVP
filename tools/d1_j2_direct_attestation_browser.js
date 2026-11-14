// D1 J1→J2 — cross-proof with Ed25519 verification DIRECTLY IN J2.
// All data and trust roots synthetic. No production issuer or migration.
'use strict';
const {chromium}=require('playwright');
const {generateKeyPairSync,sign,randomUUID}=require('node:crypto');
const fs=require('fs');
const {inventoryAndBackup,restore}=require('./d1_j1_synthetic_backup_restore_browser');
const origin='http://127.0.0.1:7481/';
const owner='amina_vault_v1_native_734';
const dir='d1-j2-verified-receipt-proof';
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',clinicalGo:false,
  issuer:'CI_EPHEMERAL_NOT_PRODUCTION',
  permissionToMigrate:false,checks:{},result:'NOT_RUN'};
function check(ok,label){if(!ok)throw Error('J2_DIRECT_RECEIPT '+label);}
async function seed(page){
 return page.evaluate(async owner=>{
  const r=indexedDB.open(owner,2);
  r.onupgradeneeded=()=>{
   const s=r.result.createObjectStore('records',{keyPath:'id'});
   s.createIndex('by_kind','kind',{unique:false});
  };
  const db=await new Promise((resolve,reject)=>{
   r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
  });
  try{
   const tx=db.transaction('records','readwrite');
   tx.objectStore('records').put({id:734,kind:'synthetic',
     stamp:new Date('2026-11-14T00:00:00Z'),
     payload:new Uint8Array([0,1,128,254,255]).buffer,
     text:'D1_J1_J2_SYNTHETIC_ONLY'});
   await new Promise((resolve,reject)=>{
     tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);
   });
  }finally{db.close();}
 },owner);
}
async function mutate(page){
 return page.evaluate(async owner=>{
  const r=indexedDB.open(owner);
  const db=await new Promise((res,rej)=>{
   r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);
  });
  try{
   const tx=db.transaction('records','readwrite');
   tx.objectStore('records').put({id:734,kind:'mutated-by-stale-writer',
     payload:new Uint8Array([8,8,8]).buffer});
   await new Promise((res,rej)=>{
    tx.oncomplete=res;tx.onerror=()=>rej(tx.error);tx.onabort=()=>rej(tx.error);
   });
  }finally{db.close();}
 },owner);
}
const requestBase={sourceName:owner,ownerType:'native',nativeId:734,
 remoteAccountVerified:true,sourcePossessionVerified:true,
 explicitConsent:true,writerRetirementAttested:true,
 // Dangerous old caller-provided fields deliberately supplied to verify
 // they are no longer sufficient to satisfy the new direct J2 gate.
 backupRestoreIndependentlyVerified:true,
 backupManifestSha256:'f'.repeat(64)};
const invoke=(page,request)=>page.evaluate(request=>
 IaminaD1J2PreflightCandidate.inspect(request),request);
const rawPublic=key=>key.export({format:'der',type:'spki'}).subarray(-32)
  .toString('base64url');
const issue=(privateKey,sourceSha,overrides={})=>{
 const payload={kind:'iamina-d1-j1-ci-synthetic-witness',version:2,
   issuer:'IAMINA_D1_CI_SYNTHETIC_ONLY',sourceName:owner,ownerType:'native',
   sourceSha256:sourceSha,restoredSha256:sourceSha,nonce:randomUUID(),
   issuedAt:Date.now(),expiresAt:Date.now()+90000,...overrides};
 return {payload,signature:sign(null,Buffer.from(JSON.stringify(payload)),
  privateKey).toString('base64url')};
};
(async()=>{
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const keys=generateKeyPairSync('ed25519');
  const fake=generateKeyPairSync('ed25519');
  const pub=rawPublic(keys.publicKey);
  const makeContext=async({pin=true,workers='allow'}={})=>{
   const ctx=await browser.newContext({locale:'en-US',serviceWorkers:workers});
   if(pin)await ctx.addInitScript(publicKey=>{
    Object.defineProperty(globalThis,'IaminaD1J2SyntheticPinnedRoot',{
      value:Object.freeze({mode:'ci-synthetic-not-production',publicKey}),
      configurable:false,writable:false
    });
   },pub);
   const page=await ctx.newPage();
   await page.goto(origin,{waitUntil:'load'});
   return {ctx,page};
  };
  const source=await makeContext();
  const a=source.page;
  await seed(a);
  const saved=await inventoryAndBackup(a,[owner]);
  const exposed=await a.evaluate(async owner=>
    IaminaD1J2SyntheticSourceDigest.digest(owner),owner);
  check(saved.sha256===exposed,'digest_j1_j2_not_equal');
  proof.checks.j1AndLiveDigestByteEquivalent=true;
  proof.sourceSha256=saved.sha256;

  const noReceipt=await invoke(a,requestBase);
  check(noReceipt.code==='J2_SIGNED_RESTORE_RECEIPT_REQUIRED',
   'caller_flags_wrongly_accepted');
  proof.checks.declarativeBackupFlagDenied=true;

  const restoreContext=await makeContext({workers:'block'});
  await restore(restoreContext.page,saved);
  const restored=await inventoryAndBackup(restoreContext.page,[owner]);
  check(restored.sha256===saved.sha256,'independent_restore_failed');
  proof.checks.independentProfileRestored=true;

  const withoutPin=await makeContext({pin:false});
  await seed(withoutPin.page);
  const noRoot=await invoke(withoutPin.page,{
    ...requestBase,receipt:issue(keys.privateKey,saved.sha256)
  });
  check(noRoot.code==='J2_TRUST_ROOT_OR_SOURCE_ORACLE_UNAVAILABLE',
    'missing_trust_anchor_was_accepted');
  proof.checks.missingTrustRootDenied=true;

  const freshValid=()=>issue(keys.privateKey,saved.sha256);
  const forgedIssuer=issue(fake.privateKey,saved.sha256);
  const bad=await invoke(a,{...requestBase,receipt:forgedIssuer});
  check(bad.code==='J2_SIGNED_RESTORE_RECEIPT_INVALID',
    'arbitrary_signer_accepted');
  proof.checks.untrustedSignerDenied=true;

  const ownerMismatch=issue(keys.privateKey,saved.sha256,{
    sourceName:'amina_vault_v1_native_812'
  });
  const mismatch=await invoke(a,{...requestBase,receipt:ownerMismatch});
  check(mismatch.code==='J2_SIGNED_RESTORE_RECEIPT_INVALID',
    'other_owner_witness_accepted');
  proof.checks.otherOwnerReceiptDenied=true;
  const damaged=freshValid();
  damaged.payload.sourceSha256='0'.repeat(64);
  const tamper=await invoke(a,{...requestBase,receipt:damaged});
  check(tamper.code==='J2_SIGNED_RESTORE_RECEIPT_INVALID',
    'tamper_accepted');
  proof.checks.tamperedReceiptDenied=true;

  const expired=issue(keys.privateKey,saved.sha256,{
    issuedAt:Date.now()-120000,expiresAt:Date.now()-60000
  });
  const past=await invoke(a,{...requestBase,receipt:expired});
  check(past.code==='J2_SIGNED_RESTORE_RECEIPT_INVALID',
    'expired_receipt_accepted');
  proof.checks.expiredReceiptDenied=true;

  const valid=freshValid();
  const ready=await invoke(a,{...requestBase,receipt:valid});
  check(ready.code==='J2_READY_FOR_EXTERNAL_SECURITY_REVIEW'&&
    ready.authorizedToMigrate===false,'valid_receipt_granted_migration_or_failed');
  proof.checks.verifiedInsideJ2ReviewOnly=true;
  const replay=await invoke(a,{...requestBase,receipt:valid});
  check(replay.code==='J2_RECEIPT_NONCE_REPLAY',
    'nonce_replay_in_same_tab_accepted');
  proof.checks.inMemoryNonceReplayDenied=true;

  // Cross-profile replay is intentionally not prevented by a browser cache.
  // It needs a server-side persisted nonce register; note explicit gap.
  proof.serverSideReplayProtected=false;

  const prior=freshValid();
  await mutate(a);
  const live=(await inventoryAndBackup(a,[owner])).sha256;
  check(live!==saved.sha256,'stale_writer_mutation_did_not_change_source');
  const stale=await invoke(a,{...requestBase,receipt:prior});
  check(stale.code==='J2_LIVE_SOURCE_DIGEST_CHANGED',
    'stale_hash_receipt_accepted');
  proof.checks.staleSourceReceiptDeniedByJ2=true;

  const crashed=await makeContext({workers:'block'});
  let interruption=false;
  try{await restore(crashed.page,saved,{simulateAbortAfterDatabase:1});}
  catch(e){interruption=String(e).includes('J1_SIMULATED_POWER_LOSS_STAGED_PARTIAL');}
  check(interruption,'interruption_not_injected');
  let didOverwrite=false;
  try{await restore(crashed.page,saved);didOverwrite=true;}catch(e){
   check(String(e).includes('J1_RESTORE_TARGET_NOT_EMPTY'),
    'partial_stage_wrong_failure');
  }
  check(!didOverwrite,'partial_stage_resumed');
  proof.checks.partialStagingQuarantined=true;
  const recovery=await makeContext({workers:'block'});
  await restore(recovery.page,saved);
  check((await inventoryAndBackup(recovery.page,[owner])).sha256===saved.sha256,
    'fresh_recovery_after_interruption_failed');
  proof.checks.independentRecoveryAfterInterruption=true;
  proof.checks.sourcePreservedFromRestoreBeforeLateMutation=true;

  // Even a new valid (post-mutation) witness must not bypass old SW fence.
  const installed=await a.evaluate(async()=>{
   const r=await navigator.serviceWorker.register('/j2-legacy-sw.js');
   await navigator.serviceWorker.ready;return !!r.active;
  });
  check(installed,'sw_not_installed');
  const blocked=await invoke(a,{...requestBase,
    receipt:issue(keys.privateKey,live)});
  check(blocked.code==='J2_UNFENCED_INSTALLED_WORKER',
    'installed_legacy_writer_accepted');
  proof.checks.installedWriterDenied=true;

  await Promise.all([source.ctx.close(),withoutPin.ctx.close(),
    restoreContext.ctx.close(),crashed.ctx.close(),recovery.ctx.close()]);
  proof.result='PASS_BROWSER_J2_SIGNATURE_GATE_ONLY';
 }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2500);throw e;}
 finally{
  fs.writeFileSync(dir+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J2_DIRECT_SIGNED_GATE='+JSON.stringify(proof));
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});