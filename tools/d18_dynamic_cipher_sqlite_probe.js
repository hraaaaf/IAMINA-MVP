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
  page.on('pageerror', e => pageErrors.push(e.name || 'PageError'));
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
      })).catch(()=>({title:'unknown',stage:'evaluation_failed',ready:'unknown'}));
      results.push({phase:name,pass:false,stage:state.stage,
        title:state.title,ready:state.ready,pageErrorNames:pageErrors});
      throw Error('D18_DYNAMIC_SQL_NO_VERDICT');
    }
    const out = await page.evaluate(() => ({
      title:document.title,
      stage:document.documentElement.dataset.d18DynamicStage||null,
      error:document.documentElement.dataset.d18DynamicError||null,
    }));
    const ok = out.title === 'D18_DYNAMIC_SQL_PASS:'+name;
    results.push({phase:name,pass:ok,
      ...(!ok?{error:out.error,stage:out.stage,pageErrorNames:pageErrors}: {})});
    if(!ok) throw new Error('D18 dynamic SQLite '+name+' rejected ('+out.error+')');
  } finally {
    await page.close();
  }
}
(async () => {
  let ctx;
  try {
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await verify(ctx,...phases[0].map((x,i)=>i===1?secrets[x]:x));
    await ctx.close(); ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      args:['--no-sandbox','--disable-dev-shm-usage']});
    for(const [name,k] of phases.slice(1,5))await verify(ctx,name,secrets[k]);
    await ctx.close(); ctx=null;
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await verify(ctx,'read',secrets.a);
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
  const expected=phases.map(p=>p[0]);
  if(results.length!==expected.length||results.some((p,i)=>
    !p.pass||p.phase!==expected[i]))process.exitCode=1;
})().catch(e=>{
  console.error('D18_DYNAMIC_SQL_HARNESS_FATAL', e.name);
  process.exitCode=1;
});
