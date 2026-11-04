// D18 synthetic ONLY: browser-process restart proof of all-schema logical copy.
// Generated app tables, FK, view, index, trigger, BLOB, NULL and sequence tested.
'use strict';
const {chromium}=require('playwright');
const crypto=require('node:crypto');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-full-copy-'));
const key=[...crypto.randomBytes(32)];
const abortKey=[...crypto.randomBytes(32)];
const crashKey=[...crypto.randomBytes(32)];
const results=[];
// P0-A diagnostic: inventory the ACTUAL browser storage created by pinned
// Drift WasmDatabase.open(sharedIndexedDb), not a hand-written IDB fixture.
// Read-only schema metadata; no keys, values, ciphertext, patients or secrets.
async function inspectPhysicalDriftStorage(context) {
  const page=await context.newPage();
  try {
    await page.route('**/d18_p0a_vfs_metadata.html',route=>route.fulfill({
      status:200,contentType:'text/html',
      body:'<!doctype html><title>D18 P0-A metadata-only synthetic</title>'
    }));
    await page.goto('http://127.0.0.1:7396/d18_p0a_vfs_metadata.html',
      {waitUntil:'domcontentloaded',timeout:30000});
    const info=await page.evaluate(async()=>{
      if(typeof indexedDB.databases!=='function')return {
        supported:false,idb:[],opfsSupported:false,opfsNames:[]
      };
      const discovered=await indexedDB.databases();
      const idb=[];
      for(const candidate of discovered.slice(0,32)){
        if(!candidate.name||!Number.isInteger(candidate.version))continue;
        const schema=await new Promise((resolve,reject)=>{
          const request=indexedDB.open(candidate.name);
          request.onupgradeneeded=()=>{
            // Fail if metadata inspection would create a database.
            request.transaction.abort();
            reject(Error('D18_VFS_INVENTORY_OPENED_NEW_DATABASE'));
          };
          request.onsuccess=()=>{
            const db=request.result;
            const record={
              name:db.name,version:db.version,
              stores:Array.from(db.objectStoreNames),
            };
            db.close();
            resolve(record);
          };
          request.onerror=()=>reject(request.error||Error('D18_VFS_IDB_OPEN'));
          request.onblocked=()=>reject(Error('D18_VFS_IDB_BLOCKED'));
        });
        idb.push(schema);
      }
      const opfsNames=[];
      const opfsSupported=typeof navigator.storage?.getDirectory==='function';
      if(opfsSupported){
        const root=await navigator.storage.getDirectory();
        for await(const [name] of root.entries()){
          if(opfsNames.length>=32)break;
          opfsNames.push(name);
        }
      }
      return {supported:true,idb,opfsSupported,opfsNames};
    });
    const pass=info.supported && info.idb.some(db=>db.stores.length>0);
    results.push({phase:'real_drift_source_vfs_metadata',pass,
      metadata:info});
    if(!pass)throw Error('D18_P0A_REAL_DRIFT_VFS_NOT_OBSERVED');
  } finally {await page.close();}
}

// CI-only cooperative source lock implementation. Not part of shipped app.
// The clinical writer protocol must adopt this gate in D18 lot 2/3.
function installSourceWriteGate() {
  window.__D18AcquireSourceWriteLock=name=>new Promise(resolve=>{
    if(!navigator.locks || typeof navigator.locks.request!=='function'){
      resolve({ok:false});return;
    }
    let settled=false;
    let finished;
    const done=new Promise(r=>{finished=r;});
    navigator.locks.request('iamina:d18:ci:source:'+name,
      {mode:'exclusive'}, async()=>{
      let unlock;
      const held=new Promise(r=>{unlock=r;});
      settled=true;
      resolve({ok:true,release:()=>{
        unlock();
        return done;
      }});
      await held;
      finished();
    }).catch(()=>{
      if(!settled)resolve({ok:false});
      finished();
    });
  });
}
async function phase(context,step){
  const page=await context.newPage();
  try{
    await page.addInitScript(installSourceWriteGate);
    await page.addInitScript(keys=>{
      Object.defineProperty(window,'__D18_FULL_KEY',
        {value:new Uint8Array(keys.a),configurable:false,writable:false});
      Object.defineProperty(window,'__D18_FULL_ABORT_KEY',
        {value:new Uint8Array(keys.b),configurable:false,writable:false});
      Object.defineProperty(window,'__D18_FULL_CRASH_KEY',
        {value:new Uint8Array(keys.c),configurable:false,writable:false});
    },{a:key,b:abortKey,c:crashKey});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.name));
    await page.goto('http://127.0.0.1:7396/?phase='+step,
      {waitUntil:'domcontentloaded',timeout:45000});
    await page.waitForFunction(()=>
      document.title.startsWith('D18_FULL_PASS:')||
      document.title.startsWith('D18_FULL_FAIL:'),
      null,{timeout:60000});
    const output=await page.evaluate(()=>({
      title:document.title,
      stage:document.documentElement.dataset.d18FullStage||null,
      error:document.documentElement.dataset.d18FullError||null,
      failureClass:document.documentElement.dataset.d18FullFailureClass||null,
    }));
    const pass=output.title==='D18_FULL_PASS:'+step;
    results.push({phase:step,pass,...(!pass?{
      stage:output.stage,error:output.error,
      failureClass:output.failureClass,errors}: {})});
    if(!pass)throw Error('D18_FULL_'+step+'_FAILED');
  }finally{await page.close();}
}
// Two real tabs of the same origin open the SAME stock SQLite source.
// An independent BEGIN IMMEDIATE must not be granted before owner releases.
// Accept SQLITE_BUSY or queued-until-release; NEVER accept overlapping grants.
async function concurrentSourceLock(context) {
  const owner=await context.newPage(), rival=await context.newPage();
  let recorded=false;
  try {
    await owner.addInitScript(installSourceWriteGate);
    await rival.addInitScript(installSourceWriteGate);
    await owner.goto('http://127.0.0.1:7396/?phase=hold_source_lock',
      {waitUntil:'domcontentloaded',timeout:45000});
    await owner.waitForFunction(()=>
      document.documentElement.dataset.d18FullStage==='source_write_gate_held' ||
      document.title.startsWith('D18_FULL_FAIL:'),
      null,{timeout:40000});
    const ownerReady=await owner.evaluate(()=>({
      held:document.documentElement.dataset.d18FullStage==='source_write_gate_held',
      title:document.title,
    }));
    if(!ownerReady.held)throw Error('D18_SOURCE_OWNER_FAILED_BEFORE_LOCK');
    await rival.goto('http://127.0.0.1:7396/?phase=compete_source_lock',
      {waitUntil:'domcontentloaded',timeout:45000});
    // A cooperating writer MUST reach the origin-wide gate while owner holds
    // it. It may not reach SQLite until the gate is explicitly released.
    await rival.waitForFunction(()=>
      ['writer_waits_source_gate','writer_gate_acquired',
       'writer_attempts_immediate_transaction','writer_immediate_granted'].includes(
        document.documentElement.dataset.d18FullStage) ||
        document.title.startsWith('D18_FULL_FAIL:'),
      null,{timeout:35000});
    let early='pending';
    try {
      await rival.waitForFunction(()=>
        document.title.startsWith('D18_FULL_PASS:') ||
        document.title.startsWith('D18_FULL_FAIL:') ||
        document.documentElement.dataset.d18FullStage==='writer_immediate_granted',
        null,{timeout:1500});
      early=await rival.evaluate(()=>
        document.documentElement.dataset.d18FullStage || document.title);
    }catch(_){}
    const noOverlappingWriter=
      early!=='writer_gate_acquired' &&
      early!=='writer_attempts_immediate_transaction' &&
      early!=='writer_immediate_granted' &&
      !early.startsWith('D18_FULL_PASS:') &&
      !early.startsWith('D18_FULL_FAIL:');
    if(!noOverlappingWriter)
      throw Error('D18_COMPETING_SQLITE_WRITER_GRANTED_WHILE_OWNER_HELD');
    await owner.evaluate(()=>window.postMessage(
      'D18_CI_RELEASE_SOURCE',window.location.origin));
    await owner.waitForFunction(()=>
      document.title.startsWith('D18_FULL_PASS:') ||
      document.title.startsWith('D18_FULL_FAIL:'),
      null,{timeout:25000});
    await rival.waitForFunction(()=>
      document.title.startsWith('D18_FULL_PASS:') ||
      document.title.startsWith('D18_FULL_FAIL:'),
      null,{timeout:25000});
    const ownerPass=(await owner.title())==='D18_FULL_PASS:hold_source_lock';
    const rivalPass=(await rival.title())==='D18_FULL_PASS:compete_source_lock';
    const after=await rival.evaluate(()=>
      document.documentElement.dataset.d18FullStage || null);
    results.push({phase:'hold_source_lock',pass:ownerPass},
      {phase:'compete_source_lock',pass:rivalPass && noOverlappingWriter,
        noOverlappingWriter,stageAfterRelease:after});
    recorded=true;
    if(!ownerPass||!rivalPass)throw Error('D18_SOURCE_LOCK_PROOF_FAILED');
  }catch(e){
    if(!recorded)results.push({phase:'hold_source_lock',pass:false},
      {phase:'compete_source_lock',pass:false,errorName:e.name||'Error'});
    throw e;
  }finally{await rival.close();await owner.close();}
}
(async()=>{
  let ctx;
  try{
    ctx=await chromium.launchPersistentContext(profile,{
      headless:true,locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'seed');
    await phase(ctx,'patient_factory_create');
    await inspectPhysicalDriftStorage(ctx);
    await phase(ctx,'abort_rollback');
    await concurrentSourceLock(ctx);
    await phase(ctx,'crash_uncommitted');
    // Fault is the actual Worker.terminate() with open SQL transaction.
    // Close entire Chromium process before asking a fresh process to recover.
    await ctx.close();ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{
      headless:true,locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'crash_recover');
    await phase(ctx,'patient_factory_reopen');
    await phase(ctx,'migrate');
    await ctx.close();ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{
      headless:true,locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'verify');
    await phase(ctx,'physical_bytes');
  }catch(e){
    results.push({phase:'harness',pass:false,errorName:e.name||'Error'});
  }finally{
    if(ctx)await ctx.close();
    fs.rmSync(profile,{recursive:true,force:true});
    key.fill(0);
    abortKey.fill(0);
    crashKey.fill(0);
  }
  fs.mkdirSync('d18-full-vault-proof',{recursive:true});
  fs.writeFileSync('d18-full-vault-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA||null,kind:'synthetic_all_schema_sqlite3mc',
    results,
  },null,2));
  console.log(JSON.stringify(results));
  const expected=['seed','patient_factory_create',
    'real_drift_source_vfs_metadata','abort_rollback','hold_source_lock',
    'compete_source_lock','crash_uncommitted',
    'crash_recover','patient_factory_reopen',
    'migrate','verify','physical_bytes'];
  if(results.length!==12||results.some((v,i)=>!v.pass||v.phase!==expected[i]))
    process.exitCode=1;
})().catch(e=>{
  console.error('D18_FULL_VAULT_HARNESS_FATAL',e.name);
  process.exitCode=1;
});
