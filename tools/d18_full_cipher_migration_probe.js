// D18 synthetic ONLY: browser-process restart proof of all-schema logical copy.
// Generated app tables, FK, view, index, trigger, BLOB, NULL and sequence tested.
'use strict';
const {chromium}=require('playwright');
const crypto=require('node:crypto');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-full-copy-'));
const key=[...crypto.randomBytes(32)];
const results=[];
async function phase(context,step){
  const page=await context.newPage();
  try{
    await page.addInitScript(bytes=>{
      Object.defineProperty(window,'__D18_FULL_KEY',
        {value:new Uint8Array(bytes),configurable:false,writable:false});
    },key);
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
    }));
    const pass=output.title==='D18_FULL_PASS:'+step;
    results.push({phase:step,pass,...(!pass?{
      stage:output.stage,error:output.error,errors}: {})});
    if(!pass)throw Error('D18_FULL_'+step+'_FAILED');
  }finally{await page.close();}
}
(async()=>{
  let ctx;
  try{
    ctx=await chromium.launchPersistentContext(profile,{
      headless:true,locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'seed');
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
  }
  fs.mkdirSync('d18-full-vault-proof',{recursive:true});
  fs.writeFileSync('d18-full-vault-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA||null,kind:'synthetic_all_schema_sqlite3mc',
    results,
  },null,2));
  console.log(JSON.stringify(results));
  const expected=['seed','migrate','verify','physical_bytes'];
  if(results.length!==4||results.some((v,i)=>!v.pass||v.phase!==expected[i]))
    process.exitCode=1;
})().catch(e=>{
  console.error('D18_FULL_VAULT_HARNESS_FATAL',e.name);
  process.exitCode=1;
});
