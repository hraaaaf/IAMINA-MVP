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
        null,{timeout:45000});
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
async function verifyActualWorkerLock(ctx) {
  const name = 'amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018_d18_ci_dynamic';
  const owner = await ctx.newPage();
  try {
    await owner.route('**/d18_ci_owner.html', route => route.fulfill({
      status:200,contentType:'text/html',
      body:'<!doctype html><html><head><title>D18 Lock Owner</title></head><body></body></html>',
    }));
    await owner.goto('http://127.0.0.1:7396/d18_ci_owner.html');
    const code = await owner.evaluate(async ({name,key}) => {
      const w = new Worker('/d18_dynamic_cipher_sqlite_worker.js');
      const control = new MessageChannel(), sql = new MessageChannel();
      const raw = new Uint8Array(key);
      const response = new Promise((resolve,reject) => {
        const timeout=setTimeout(()=>reject(Error('OWNER_WORKER_TIMEOUT')),12000);
        control.port1.onmessage=event=>{
          clearTimeout(timeout);
          resolve(event.data);
        };
      });
      w.postMessage({type:'D18_CI_DYNAMIC_SQL_OPEN',name,key:raw.buffer},
        [control.port2,sql.port2,raw.buffer]);
      window.__d18SqlOwner = {w,control:control.port1,sql:sql.port1};
      return response;
    },{name,key:secrets.a});
    const passed = code==='READY';
    results.push({phase:'owner_holds_lock',pass:passed});
    if(!passed) throw Error('D18_REAL_OWNER_NOT_READY');
    await verify(ctx,'lock_denied',secrets.a);
    await owner.evaluate(()=>{
      window.__d18SqlOwner.w.terminate();
      window.__d18SqlOwner.control.close();
      window.__d18SqlOwner.sql.close();
    });
    await owner.waitForFunction(async name => {
      const state=await navigator.locks.query();
      return !state.held.some(lock=>lock.name==='iamina:d18:ci:v1:'+name);
    },name,{timeout:12000});
  } finally {
    await owner.close();
  }
  await verify(ctx,'read',secrets.a);
}

(async () => {
  let ctx;
  try {
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await verify(ctx,...phases[0].map((x,i)=>i===1?secrets[x]:x));
    await ctx.close(); ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
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
  const expected=[...phases.map(p=>p[0]),
    'owner_holds_lock','lock_denied','read'];
  if(results.length!==expected.length||results.some((p,i)=>
    !p.pass||p.phase!==expected[i]))process.exitCode=1;
})().catch(e=>{
  console.error('D18_DYNAMIC_SQL_HARNESS_FATAL', e.name);
  process.exitCode=1;
});
