// D18 stage 3/6: synthetic full-schema copy to the real unpublished cipher worker.
// No clinical data, no runtime import, no cutover or source deletion.
'use strict';
const {chromium}=require('playwright');
const crypto=require('node:crypto');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-candidate-migration-'));
const key=[...crypto.randomBytes(32)];
const results=[];
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

async function phase(ctx,name){
  const page=await ctx.newPage();
  try{
    await page.addInitScript(installSourceWriteGate);
    await page.addInitScript(bytes=>{
      Object.defineProperty(window,'__D18_FULL_KEY',
        {value:new Uint8Array(bytes),configurable:false,writable:false});
    },key);
    await page.goto('http://127.0.0.1:7396/?phase='+name,
      {waitUntil:'domcontentloaded',timeout:45000});
    await page.waitForFunction(()=>
      document.title.startsWith('D18_CANDIDATE_MIGRATION_PASS:')||
      document.title.startsWith('D18_CANDIDATE_MIGRATION_FAIL:'),
      null,{timeout:80000});
    const out=await page.evaluate(()=>({title:document.title,
      stage:document.documentElement.dataset.d18FullStage||null,
      error:document.documentElement.dataset.d18FullError||null}));
    const pass=out.title==='D18_CANDIDATE_MIGRATION_PASS:'+name;
    results.push({phase:name,pass,...(pass?{}:{stage:out.stage,error:out.error})});
    if(!pass)throw Error('D18_STAGE3_'+name+'_FAILED');
  }finally{await page.close();}
}
(async()=>{
  let ctx;
  try{
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'seed');
    await phase(ctx,'migrate');
    await ctx.close();ctx=null;
    // Reopening ciphertext and source in an independent Chromium process.
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    await phase(ctx,'verify');
    await phase(ctx,'physical_bytes');
  }catch(e){results.push({phase:'harness',pass:false,errorName:e.name||'Error'});}
  finally{
    if(ctx)await ctx.close().catch(()=>{});
    key.fill(0);
    fs.rmSync(profile,{recursive:true,force:true});
  }
  fs.mkdirSync('d18-candidate-migration-proof',{recursive:true});
  fs.writeFileSync('d18-candidate-migration-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA||null,
    kind:'synthetic_full_schema_into_unpublished_cipher_worker',results},null,2));
  console.log(JSON.stringify(results));
  const expected=['seed','migrate','verify','physical_bytes'];
  if(results.length!==expected.length||results.some((v,i)=>!v.pass||v.phase!==expected[i]))
    process.exitCode=1;
})().catch(e=>{console.error('D18_STAGE3_FATAL',e.name);process.exitCode=1;});
