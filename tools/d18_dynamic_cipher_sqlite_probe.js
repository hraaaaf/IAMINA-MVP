// Real Web CI-only: fresh per-vault random secrets into sqlite3mc dedicated
// DriftServer worker. Does NOT exercise clinical key policy or patient runtime.
'use strict';
const {chromium} = require('playwright');
const crypto = require('node:crypto');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'd18-dynamic-sql-'));
const secrets = {
  a: [...crypto.randomBytes(32)],
  b: [...crypto.randomBytes(32)],
  wrong: [...crypto.randomBytes(32)],
};
const phases = [
  ['create','a'],
  ['wrong_key','wrong'],
  ['read','a'],
  ['isolate_b','b'],
  ['physical_bytes','a'],
  ['read','a'],
];
const results = [];
async function verify(ctx,name,key) {
  const page = await ctx.newPage();
  const pageErrors = [];
  // This is a disposable synthetic-only runner, never clinical data.
  // Capture bounded JS startup diagnostics, redacting long hex secrets and URLs.
  const safeError = e => {
    const message = String(e.message || '').replace(/[a-f0-9]{32,}/gi, '[redacted]')
      .replace(/https?:\/\/[^\s]+/g, '[url]').slice(0, 320);
    return {name: e.name || 'PageError', message};
  };
  page.on('pageerror', e => pageErrors.push(safeError(e)));
  try {
    await page.addInitScript(keyBytes => {
      Object.defineProperty(window, '__D18_DYNAMIC_CI_KEY',
        {value: new Uint8Array(keyBytes), writable:false, configurable:false});
    }, key);
    await page.goto('http://127.0.0.1:7396/?phase='+name,
      {waitUntil:'domcontentloaded',timeout:45000});
    try {
      await page.waitForFunction(() =>
        document.title.startsWith('D18_DYNAMIC_SQL_PASS:') ||
        document.title.startsWith('D18_DYNAMIC_SQL_FAIL:'),
        null,{timeout:name.startsWith('guarded_')?120000:45000});
    } catch (_) {
      const state = await page.evaluate(() => ({
        title:document.title,
        stage:document.documentElement.dataset.d18DynamicStage||'no_stage',
        ready:document.readyState,
        flutterLoader:typeof window._flutter,
        mainScript:[...document.scripts].map(x => x.src && x.src.split('/').at(-1)).filter(Boolean),
      })).catch(()=>({title:'unknown',stage:'evaluation_failed',ready:'unknown'}));
      results.push({phase:name,pass:false,stage:state.stage,
        title:state.title,ready:state.ready,flutterLoader:state.flutterLoader,
        mainScript:state.mainScript,pageErrors});
      throw Error('D18_DYNAMIC_SQL_NO_VERDICT');
    }
    const out = await page.evaluate(() => ({
      title:document.title,
      stage:document.documentElement.dataset.d18DynamicStage||null,
      error:document.documentElement.dataset.d18DynamicError||null,
    }));
    const ok = out.title === 'D18_DYNAMIC_SQL_PASS:'+name;
    results.push({phase:name,pass:ok,
      ...(!ok?{error:out.error,stage:out.stage,pageErrors}: {})});
    if(!ok) throw new Error('D18 dynamic SQLite '+name+' rejected ('+out.error+')');
  } finally {
    await page.close();
  }
}
// Keep a genuine sqlite3mc DriftServer Worker open in one tab, then verify a
// second tab's dynamic worker cannot enter the SAME database. This checks the
// real worker's lock rather than the standalone synthetic Web Locks helper.
const ciVaultA = 'amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018_d18_ci_dynamic';
const ciVaultB = 'amina_vault_v1_device_e2dbe28f3eea441086a7274150b00018_d18_ci_dynamic';
async function openSyntheticOwnerPage(ctx) {
  const page=await ctx.newPage();
  await page.route('**/d18_ci_owner.html',route=>route.fulfill({
    status:200, contentType:'text/html',
    body:'<!doctype html><html><head><title>D18 Lock Owner</title></head><body></body></html>',
  }));
  await page.goto('http://127.0.0.1:7396/d18_ci_owner.html');
  return page;
}
async function workerOpenOnPage(page,name,key,retain) {
  return page.evaluate(async ({name,key,retain}) => {
    const w=new Worker('/d18_dynamic_cipher_sqlite_worker.js');
    const control=new MessageChannel(),sql=new MessageChannel();
    const raw=new Uint8Array(key);
    try {
      const answer=new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(Error('D18_OWNER_WORKER_TIMEOUT')),15000);
        control.port1.onmessage=ev=>{clearTimeout(timer);resolve(ev.data);};
      });
      w.postMessage({type:'D18_CI_DYNAMIC_SQL_OPEN',name,key:raw.buffer},
        [control.port2,sql.port2,raw.buffer]);
      const status=await answer;
      if(retain&&status==='READY') {
        window.__d18SqlOwner={w,control:control.port1,sql:sql.port1};
      } else {
        w.terminate();control.port1.close();sql.port1.close();
      }
      return status;
    }catch(e){
      w.terminate();control.port1.close();sql.port1.close();
      return 'WORKER_OPEN_TIMEOUT';
    }
  },{name,key,retain});
}
async function startOwner(ctx,phase,name,key) {
  const page=await openSyntheticOwnerPage(ctx);
  try {
    const code=await workerOpenOnPage(page,name,key,true);
    const pass=code==='READY';
    results.push({phase,pass});
    if(!pass)throw Error('D18_SQL_LOCK_'+phase+'_REJECTED_'+code);
    return page;
  }catch(e){await page.close();throw e;}
}
async function probeDenied(ctx,phase,name,key) {
  const page=await openSyntheticOwnerPage(ctx);
  try{
    const code=await workerOpenOnPage(page,name,key,false);
    const pass=code==='LOCK_UNAVAILABLE';
    results.push({phase,pass});
    if(!pass)throw Error('D18_SQL_LOCK_'+phase+'_NOT_DENIED_'+code);
  }finally{await page.close();}
}
async function terminateAndVerifyRelease(owner,observer,name,phase) {
  await owner.evaluate(()=>{
    const session=window.__d18SqlOwner;
    session.w.terminate();
    session.control.close();session.sql.close();
    delete window.__d18SqlOwner;
  });
  const released=await observer.waitForFunction(async name=>{
    const held=(await navigator.locks.query()).held;
    return !held.some(x=>x.name==='iamina:d18:ci:v1:'+name);
  },name,{timeout:15000}).then(()=>true).catch(()=>false);
  results.push({phase,pass:released});
  if(!released)throw Error('D18_SQL_LOCK_'+phase+'_NOT_RELEASED');
}
async function verifyActualWorkerLock(ctx) {
  let ownerA,ownerB,ownerA2,ownerB2;
  try {
    ownerA=await startOwner(ctx,'owner_a_ready',ciVaultA,secrets.a);
    // B stays writable while A is held open: physical DBs are independent.
    await verify(ctx,'create_b',secrets.b);
    ownerB=await startOwner(ctx,'owner_b_ready',ciVaultB,secrets.b);
    await probeDenied(ctx,'a_second_worker_denied',ciVaultA,secrets.a);
    await probeDenied(ctx,'b_second_worker_denied',ciVaultB,secrets.b);
    await terminateAndVerifyRelease(ownerA,ownerB,ciVaultA,
      'a_terminate_releases');
    await ownerA.close(); ownerA=null;
    ownerA2=await startOwner(ctx,'owner_a_reopened_b_still_held',ciVaultA,secrets.a);
    await probeDenied(ctx,'b_still_denied',ciVaultB,secrets.b);
    await terminateAndVerifyRelease(ownerB,ownerA2,ciVaultB,
      'b_terminate_releases');
    await ownerB.close(); ownerB=null;
    ownerB2=await startOwner(ctx,'owner_b_reopened_a_still_held',ciVaultB,secrets.b);
    await probeDenied(ctx,'a_still_denied',ciVaultA,secrets.a);
  }finally{
    for(const page of [ownerA,ownerB,ownerA2,ownerB2]){
      if(page)await page.close();
    }
  }
  // These are genuine separate IndexedDB/sqlite3mc stores across tab crashes.
  await verify(ctx,'read',secrets.a);
  await verify(ctx,'read_b',secrets.b);
}

(async () => {
  let ctx;
  try {
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    // Test the newest risk first: report schema failures without running the
    // entire historical A/B suite before reaching the new keyed-open gate.
    await verify(ctx,'guarded_open',secrets.a);
    await verify(ctx,'candidate_missing',secrets.a);
    await verify(ctx,'candidate_create',secrets.a);
    await verify(ctx,'candidate_create_exists',secrets.a);
    // Physical existence is checked under the worker's real Web Lock.
    // No sqlite3mc connection must be opened for a rejected intent.
    await verify(ctx,'intent_reopen_missing',secrets.a);
    await verify(ctx,'intent_create',secrets.a);
    await verify(ctx,'intent_create_exists',secrets.a);
    // Wrong key must be rejected against EXISTING ciphertext, without
    // changing its stored bytes or replacing the database.
    await verify(ctx,'intent_wrong_key',secrets.wrong);
    await verify(ctx,...phases[0].map((x,i)=>i===1?secrets[x]:x));
    await ctx.close(); ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    // Fresh Chromium PROCESS, same persistent profile, only public envelope
    // retained. Policy must unwrap the DEK and reopen the REAL v12 keyed DB.
    // Negative recovery precedes correct-key reopen: the failed attempt
    // must not reset, overwrite, or unlock the existing encrypted v12 store.
    await verify(ctx,'intent_reopen',secrets.a);
    await verify(ctx,'candidate_wrong_key',secrets.wrong);
    await verify(ctx,'candidate_reopen',secrets.a);
    await verify(ctx,'candidate_physical_bytes',secrets.a);
    await verify(ctx,'guarded_wrong_passphrase',secrets.wrong);
    await verify(ctx,'guarded_reopen',secrets.a);
    for(const [name,k] of phases.slice(1,5))await verify(ctx,name,secrets[k]);
    await ctx.close(); ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await verify(ctx,'read',secrets.a);
    await verifyActualWorkerLock(ctx);

  }catch(e){
    results.push({phase:'harness',pass:false,error:String(e).slice(0,250)});
  }finally{
    if(ctx) await ctx.close();
    fs.rmSync(profile,{recursive:true,force:true});
  }
  // Results contain phase names/status ONLY. Secret values never logged.
  fs.mkdirSync('d18-dynamic-sql-proof',{recursive:true});
  fs.writeFileSync('d18-dynamic-sql-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA||null,results,
  },null,2));
  console.log(JSON.stringify(results));
  const expected=['guarded_open','candidate_missing','candidate_create',
    'candidate_create_exists',
    'intent_reopen_missing','intent_create','intent_create_exists',
    'intent_wrong_key', phases[0][0], 'intent_reopen',
    'candidate_wrong_key','candidate_reopen',
    'candidate_physical_bytes',
    'guarded_wrong_passphrase','guarded_reopen',
    ...phases.slice(1).map(p=>p[0]),
    'owner_a_ready','create_b','owner_b_ready',
    'a_second_worker_denied','b_second_worker_denied',
    'a_terminate_releases','owner_a_reopened_b_still_held',
    'b_still_denied','b_terminate_releases',
    'owner_b_reopened_a_still_held','a_still_denied','read','read_b'];
  if(results.length!==expected.length||results.some((p,i)=>
    !p.pass||p.phase!==expected[i]))process.exitCode=1;
})().catch(e=>{
  console.error('D18_DYNAMIC_SQL_HARNESS_FATAL', e.name);
  process.exitCode=1;
});
