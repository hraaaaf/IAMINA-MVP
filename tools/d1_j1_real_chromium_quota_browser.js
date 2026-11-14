// D1 synthetic real-Chromium quota exhaustion probe, via DevTools Storage API.
// Isolated browser profiles and actual encrypted SQLite3MC bytes only.
// Browser-specific, NOT an all-platform clinical quota/recovery certification.
'use strict';
const {chromium}=require('playwright');
const {createHash}=require('node:crypto');
const fs=require('fs');
const {exportArchive,importArchive,root,meta,marker}=
  require('./d1_j1_physical_cipher_backup_failure_browser');
const folder='d1-j1-real-browser-quota-proof';
const sha=o=>createHash('sha256').update(JSON.stringify(o)).digest('hex');
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',
  engine:'Playwright Chromium CDP Storage.overrideQuotaForOrigin',
  clinicalGo:false,result:'NOT_RUN'};
function check(ok,label){if(!ok)throw Error('D1_REAL_QUOTA '+label);}
(async()=>{
 fs.mkdirSync(folder,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const contexts=[];
 async function page(phase){
  const ctx=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  contexts.push(ctx);
  const p=await ctx.newPage();
  await p.goto(root+'?phase='+phase,{waitUntil:'domcontentloaded'});
  if(phase==='source'){
    await p.waitForFunction(()=>{
      const s=document.body?.textContent||'';
      return s.includes('"scope":"synthetic encrypted IndexedDB export/restore, separate browser profiles"') &&
        s.includes('"result":"SOURCE_READY"');
    },null,{timeout:60000});
  }else{
    // Target deliberately blocks on a user click and has no result JSON yet.
    await p.waitForSelector('#d1-fresh-profile-restore-trigger',
      {state:'attached',timeout:60000});
  }
  return {ctx,p};
 }
 try{
  const src=await page('source');
  const archive=await exportArchive(src.p);
  const digest=sha(archive);
  const backup=JSON.stringify(archive);
  const recovery=await src.p.evaluate(
    ()=>sessionStorage.getItem('d1_fixture_recovery'));
  check(!backup.includes(marker)&&!backup.includes(recovery),
    'backup_not_proven_ciphertext_only');
  const limited=await page('target');
  const cdp=await limited.ctx.newCDPSession(limited.p);
  await cdp.send('Storage.overrideQuotaForOrigin',{
    origin:new URL(root).origin,quotaSize:4096
  });
  const storage=await limited.p.evaluate(async()=>{
    const q=await navigator.storage.estimate();
    return {quota:q.quota,usage:q.usage};
  });
  proof.quotaReported=storage.quota;
  proof.limitRequestedBytes=4096;
  check(typeof storage.quota==='number'&&storage.quota<=4096,
    'CDP quota override not effective');
  let error;
  try{await importArchive(limited.p,archive,digest);}
  catch(e){error=String(e);}
  proof.actualStorageError=error?.slice(0,280)??null;
  proof.realBrowserQuotaDeniedImport=!!error&&
    (/QuotaExceededError|quota|Quota/i.test(error));
  check(proof.realBrowserQuotaDeniedImport,
    'real browser did not reject storage limit');
  const state=await limited.p.evaluate(async ({storeName,headerName})=>({
    ciphertextStorePresent:(await indexedDB.databases()).some(x=>x.name===storeName),
    sealedHeaderPresent:!!localStorage.getItem(headerName)
  }),meta);
  proof.noSealedEnvelopeAfterQuota=!state.sealedHeaderPresent;
  check(proof.noSealedEnvelopeAfterQuota,
    'quota created a falsely sealed vault');
  const original=await exportArchive(src.p);
  proof.sourcePreserved=sha(original)===digest;
  check(proof.sourcePreserved,'quota changed original ciphertext');

  // Restore to a genuinely new unrestricted browser storage profile.
  const fresh=await page('target');
  await importArchive(fresh.p,archive,digest);
  proof.cipherBytesMatchInFreshProfile=sha(await exportArchive(fresh.p))===digest;
  check(proof.cipherBytesMatchInFreshProfile,'fresh profile cipher mismatch');
  await fresh.p.evaluate(code=>
    sessionStorage.setItem('d1_fixture_recovery',code),recovery);
  await fresh.p.locator('#d1-fresh-profile-restore-trigger').evaluate(e=>e.click());
  await fresh.p.waitForFunction(()=>{
    const text=document.body?.textContent||'';
    return text.includes('"result":"PASS"')||text.includes('"result":"FAIL"');
  },null,{timeout:50000});
  const report=JSON.parse(await fresh.p.locator('body').innerText());
  proof.actualSqlite3mcRecovered=report.result==='PASS'&&
    report.restoredOriginalRecord===true&&report.wrongRecoveryRejected===true;
  check(proof.actualSqlite3mcRecovered,'real encrypted SQLite3MC recovery failed');
  proof.result='PASS_ACTUAL_CHROMIUM_QUOTA_DENIAL_AND_FRESH_RECOVERY';
 }catch(e){
  proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2700);throw e;
 }finally{
  fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J1_CHROMIUM_REAL_QUOTA='+JSON.stringify(proof));
  for(const ctx of contexts)await ctx.close().catch(()=>{});
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});
