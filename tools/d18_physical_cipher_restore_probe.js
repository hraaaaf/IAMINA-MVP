// D18 4/6: test EXACT ciphertext SQLite physical restoration on a new
// Chromium persistent profile. Archive exists temporarily OUTSIDE the browser.
// All patient-like data and passphrases are SYNTHETIC test fixtures.
'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'d18-cipher-full-restore-'));
const archivePath=path.join(root,'independent-sealed-vault.json');
const origin='http://127.0.0.1:7398/';
const results=[];
async function createProfile(name){
 return chromium.launchPersistentContext(path.join(root,name),{
   headless:true,locale:'fr-FR',
   args:['--no-sandbox','--disable-dev-shm-usage']});
}
async function phase(ctx,name,{importArchive=false,exportArchive=false}={}){
 const page=await ctx.newPage();
 try{
  const errors=[];
  page.on('pageerror',e=>errors.push(e.name));
  if(importArchive){
   const sealed=fs.readFileSync(archivePath,'utf8');
   if(!sealed.startsWith('{"format":"iamina-d18-whole-ciphertext-backup"'))
     throw Error('D18_ARCHIVE_NOT_A_VALID_INDEPENDENT_FILE');
   await page.addInitScript(value=>{
     Object.defineProperty(window,'__D18_CI_IMPORTED_ARCHIVE',
       {value,configurable:false,writable:false});
   },sealed);
  }
  await page.goto(origin+'?phase='+name,{
   waitUntil:'domcontentloaded',timeout:45000});
  await page.waitForFunction(()=>
    document.title.startsWith('D18_FULL_RESTORE_PASS:')||
    document.title.startsWith('D18_FULL_RESTORE_FAIL:'),
    null,{timeout:130000});
  const r=await page.evaluate(()=>({
    title:document.title,
    stage:document.documentElement.dataset.d18RestoreStage||null,
    error:document.documentElement.dataset.d18RestoreError||null,
  }));
  const pass=r.title==='D18_FULL_RESTORE_PASS:'+name;
  results.push({phase:name,pass,...(pass?{}:{
    stage:r.stage,error:r.error,pageErrors:errors.slice(0,5)})});
  if(!pass)throw Error('D18_FULL_RESTORE_PHASE_FAILED_'+name);
  if(exportArchive){
   const sealed=await page.evaluate(()=>window.__D18_CI_EXPORTED_ARCHIVE);
   if(typeof sealed!=='string'||sealed.length<1024||
      sealed.includes('D18_SYNTHETIC_RESTORE_FULL_DB_MARKER_20261103'))
     throw Error('D18_INDEPENDENT_ARCHIVE_NOT_SECURE');
   // This file is distinct from both browser profiles and is never
   // attached to CI artifacts or printed. It is removed at test completion.
   fs.writeFileSync(archivePath,sealed,{mode:0o600,flag:'wx'});
  }
 }finally{await page.close();}
}
(async()=>{
 let ctx;
 try{
  // Source A: key-policy enrolment, complete v12 SQLite schema, encrypted
  // persistence, worker closure/flush, export and second-layer sealing.
  ctx=await createProfile('browser-source-A');
  await phase(ctx,'export',{exportArchive:true});
  await ctx.close();ctx=null;
  // Third physical browser C: a wrong archive passphrase must refuse before
  // any ciphertext database is created.
  ctx=await createProfile('browser-rejected-C');
  await phase(ctx,'bad_archive',{importArchive:true});
  await phase(ctx,'restore_crash',{importArchive:true});
  await ctx.close();ctx=null;
  // The partial SQLite ciphertext is durable but MUST stay locked and may
  // not be overwritten or authenticated after a real browser restart.
  ctx=await createProfile('browser-rejected-C');
  await phase(ctx,'restore_crash_denied',{importArchive:true});
  await phase(ctx,'restore_crash_unreadable',{importArchive:true});
  await ctx.close();ctx=null;
  // RESTORE TARGET B is a completely new Chromium userDataDir.
  ctx=await createProfile('browser-fresh-B');
  await phase(ctx,'restore',{importArchive:true});
  await phase(ctx,'restore_again_denied',{importArchive:true});
  await phase(ctx,'wrong_key',{importArchive:true});
  await ctx.close();ctx=null;
  // A real independent Chromium restart MUST still authenticate/read B.
  ctx=await createProfile('browser-fresh-B');
  await phase(ctx,'reopen',{importArchive:true});
  await ctx.close();ctx=null;
  // Original source has not been modified, deleted or replaced.
  ctx=await createProfile('browser-source-A');
  await phase(ctx,'source_reopen',{importArchive:true});
 }catch(e){
  results.push({phase:'harness',pass:false,errorName:e.name||'Error',
    errorCode:String(e.message||'').replace(/[^A-Za-z0-9_]/g,'_').slice(0,140)});
 }finally{
  if(ctx)await ctx.close().catch(()=>{});
  // No plaintext patient data, no decrypted DEK or archive persists outside
  // the isolated CI runner after completion.
  fs.rmSync(root,{recursive:true,force:true});
 }
 fs.mkdirSync('d18-physical-restore-proof',{recursive:true});
 fs.writeFileSync('d18-physical-restore-proof/report.json',
  JSON.stringify({sha:process.env.GITHUB_SHA||null,
   kind:'synthetic-sqlite3mc-physical-restore-fresh-chromium',
   phases:results},null,2));
 console.log(JSON.stringify(results));
 const expected=['export','bad_archive','restore_crash',
  'restore_crash_denied','restore_crash_unreadable',
  'restore','restore_again_denied','wrong_key','reopen','source_reopen'];
 if(results.length!==expected.length ||
   results.some((r,i)=>!r.pass||r.phase!==expected[i])){
  process.exitCode=1;
 }
})().catch(e=>{
 console.error('D18_FULL_RESTORE_HARNESS_FATAL',e.name);
 process.exitCode=1;
});
