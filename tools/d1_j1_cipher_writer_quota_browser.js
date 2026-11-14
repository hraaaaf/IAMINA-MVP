// D1 J1 adversarial CI-only encrypted SQLite3MC writer-vs-backup rehearsal.
// NO real patient, no production writer fencing, no atomic WAL guarantee.
// Uses the actual encrypted Drift source/target synthetic Flutter fixture.
'use strict';
const fs=require('fs');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const {exportArchive,importArchive,meta,root,marker}=
  require('./d1_j1_physical_cipher_backup_failure_browser');
const folder='d1-j1-physical-writer-quota-proof';
const proof={
  head:process.env.D1_CANDIDATE_SHA||'unknown',clinicalGo:false,
  mode:'actual SQLite3MC synthetic SQL writer during backup finalization; synthetic quota tx abort',
  liveConcurrentSqliteAtomicSnapshotProven:false,
  browserQuotaExceededReproduced:false,
  result:'NOT_RUN',checks:{}
};
const digest=o=>createHash('sha256').update(JSON.stringify(o)).digest('hex');
function check(x,label){if(!x)throw Error('D1_J1_RACE_QUOTA '+label);}
async function readFixture(page,expected){
 await page.waitForFunction(expected=>{
   const s=document.body?.textContent||'';
   return s.includes('"scope":"synthetic encrypted IndexedDB export/restore, separate browser profiles"') &&
      (s.includes('"result":"'+expected+'"')||s.includes('"result":"FAIL"'));
 },expected,{timeout:50000});
 const raw=await page.locator('body').innerText();
 const start=raw.indexOf('{"scope"');
 // The synthetic source also has a test-only button appended after JSON.
 const end=raw.indexOf('}',start)+1;
 const r=JSON.parse(raw.slice(start,end));
 check(r.result===expected,'fixture:'+JSON.stringify(r).slice(0,350));
 return r;
}
(async()=>{
 fs.mkdirSync(folder,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const contexts=[];
 const page=async(mode)=>{
  const ctx=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  contexts.push(ctx);
  const tab=await ctx.newPage();
  const errors=[];tab.on('pageerror',err=>errors.push(String(err).slice(0,1000)));
  await tab.goto(root+'?phase='+mode+'&race=1',{waitUntil:'domcontentloaded'});
  if(mode==='target')
   await tab.waitForSelector('#d1-fresh-profile-restore-trigger',{timeout:45000});
  return {tab,errors};
 };
 try {
  const source=await page('source');
  await readFixture(source.tab,'SOURCE_READY');
  const recovery=await source.tab.evaluate(
    ()=>sessionStorage.getItem('d1_fixture_recovery'));
  check(typeof recovery==='string'&&recovery.length>40,
    'missing_synthetic_recovery');
  const before=await exportArchive(source.tab);
  const beforeHash=digest(before);
  proof.sourceBeforeWriterSha256=beforeHash;
  check(!JSON.stringify(before).includes(recovery)&&
    !JSON.stringify(before).includes(marker),
    'unencrypted_source_backup');

  let exportCompleted=false;
  const pending=exportArchive(source.tab,9000).then(x=>{
    exportCompleted=true;return x;
  });
  await source.tab.waitForFunction(
    ()=>globalThis.__d1SyntheticSnapshotCaptured===true,
    null,{timeout:20000});
  // The snapshot's records were read while the writer is still idle.
  await source.tab.locator('#d1-synthetic-encrypted-write-after-backup')
    .evaluate(e=>e.click());
  await source.tab.waitForFunction(
    ()=>localStorage.getItem('d1_synthetic_race_state')==='COMMITTED',
    null,{timeout:15000});
  proof.checks.realEncryptedSqlWriteDuringBackupWindow=!exportCompleted;
  check(proof.checks.realEncryptedSqlWriteDuringBackupWindow,
    'actual_flutter_sql_write_not_in_backup_window');
  const stale=await pending;
  const staleHash=digest(stale);
  const after=await exportArchive(source.tab);
  const liveHash=digest(after);
  proof.sourceAfterWriterSha256=liveHash;
  proof.checks.backupFrozenBeforeLateSqlWrite=staleHash===beforeHash;
  check(proof.checks.backupFrozenBeforeLateSqlWrite,
    'snapshot_bytes_changed_unexpectedly_after_capture');
  proof.checks.liveSourceChangedAfterActualSqlWrite=liveHash!==staleHash;
  check(proof.checks.liveSourceChangedAfterActualSqlWrite,
    'old_backup_unexpectedly_equal_live_store');

  // An integration gate must DENY the stale archive and never silently
  // consider it a complete record of the owner's clinical state.
  function optimisticFence(snapshot,live){
    if(digest(snapshot)!==digest(live))
      throw Error('D1_CIPHER_SOURCE_CHANGED_DURING_BACKUP');
    return true;
  }
  let staleDenied=false;
  try{optimisticFence(stale,after);}
  catch(e){staleDenied=String(e).includes('D1_CIPHER_SOURCE_CHANGED_DURING_BACKUP');}
  check(staleDenied,'stale_cipher_backup_admitted');
  proof.checks.staleCipherBackupRefused=true;
  check(optimisticFence(after,await exportArchive(source.tab)),
    'stable_after_snapshot_changed');
  proof.checks.quiescentSourceDoubleReadMatches=true;

  const quota=await page('target');
  let quotaRejected=false;
  try{
    await importArchive(quota.tab,after,liveHash,{simulateQuotaAbort:true});
  }catch(e){
    quotaRejected=String(e).includes('D1_SYNTHETIC_QUOTA_TX_ABORTED');
  }
  check(quotaRejected,'injected_abort_not_observed');
  proof.checks.injectedQuotaLikeTransactionAbort=true;
  const partial=await quota.tab.evaluate(async({storeName,headerName})=>({
    dbExists:(await indexedDB.databases()).some(x=>x.name===storeName),
    sealedHeader:!!localStorage.getItem(headerName)
  }),meta);
  check(partial.dbExists&&!partial.sealedHeader,
    'quota_abort_staging_should_remain_quarantined');
  proof.checks.quotaAbortLeavesNoSealedHeader=true;
  let overwritten=false;
  try{await importArchive(quota.tab,after,liveHash);overwritten=true;}
  catch(e){check(String(e).includes('D1_RESTORE_TARGET_NOT_EMPTY'),
    'quota_abort_retry_wrong_refusal');}
  check(!overwritten,'quota_abort_target_overwritten');
  proof.checks.quotaAbortTargetOverwriteDenied=true;

  const unchanged=await exportArchive(source.tab);
  check(digest(unchanged)===liveHash,'quota_test_changed_source');
  proof.checks.sourcePreservedAfterAbortedRestore=true;

  const fresh=await page('target');
  await importArchive(fresh.tab,after,liveHash);
  const afterRestore=await exportArchive(fresh.tab);
  check(digest(afterRestore)===liveHash,
    'clean_restore_not_byte_equivalent');
  proof.checks.cleanRestoreCipherBytesMatch=true;
  await fresh.tab.evaluate(recoveryCode=>
    sessionStorage.setItem('d1_fixture_recovery',recoveryCode),recovery);
  await fresh.tab.locator('#d1-fresh-profile-restore-trigger')
    .evaluate(e=>e.click());
  const recovered=await readFixture(fresh.tab,'PASS');
  proof.checks.preAndPostWriterRowsRecoveredFromSqlite3mc=
    recovered.restoredOriginalRecord===true&&
    recovered.concurrentSqlWriteRecovered===true&&
    recovered.wrongRecoveryRejected===true;
  check(proof.checks.preAndPostWriterRowsRecoveredFromSqlite3mc,
    'fresh_profile_missing_actual_writer_record');
  proof.checks.noPageErrors=[
    source,quota,fresh
  ].every(x=>x.errors.length===0);
  check(proof.checks.noPageErrors,'page_errors');
  proof.result='PASS_RACE_DETECTED_QUOTA_ABORT_QUARANTINED_SYNTHETIC';
 }catch(e){
  proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2700);throw e;
 }finally{
  fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J1_CIPHER_WRITER_QUOTA='+JSON.stringify(proof));
  for(const ctx of contexts)await ctx.close().catch(()=>{});
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});
