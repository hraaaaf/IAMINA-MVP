// D18 stage 3/6: synthetic full-schema copy to the real unpublished cipher worker.
// No clinical data, no runtime import, no cutover or source deletion.
'use strict';
const {chromium}=require('playwright');
const crypto=require('node:crypto');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-candidate-migration-'));
const key=[...crypto.randomBytes(32)];
const results=[];
const mode=process.env.D18_NEGATIVE_MODE||'baseline';
if(!['baseline','missing_source','missing_trigger'].includes(mode))
  throw Error('D18_UNSUPPORTED_NEGATIVE_MODE');
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

async function phase(ctx,name,{expectedFailure=null}={}){
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
    const pass=expectedFailure===null
      ? out.title==='D18_CANDIDATE_MIGRATION_PASS:'+name
      : out.title==='D18_CANDIDATE_MIGRATION_FAIL:'+name &&
        out.error===expectedFailure;
    results.push({phase:name,pass,
      ...(expectedFailure===null?{}:{expectedFailure}),
      ...(pass?{}:{stage:out.stage,error:out.error})});
    if(!pass)throw Error('D18_STAGE3_'+name+'_FAILED');
  }finally{await page.close();}
}
(async()=>{
  let ctx;
  try{
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    if(mode==='missing_source'){
      await phase(ctx,'migrate',{
        expectedFailure:'D18_SOURCE_MISSING_BEFORE_REOPEN'});
      await phase(ctx,'assert_missing_source_untouched');
    }else if(mode==='missing_trigger'){
      await phase(ctx,'seed_missing_trigger');
      await phase(ctx,'migrate',{
        expectedFailure:'D18_SOURCE_SYNTHETIC_TRIGGER_MISSING'});
      await ctx.close();ctx=null;
      // Independent Chromium process verifies source preservation after fail.
      ctx=await chromium.launchPersistentContext(profile,{headless:true,
        locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
      await phase(ctx,'assert_missing_trigger_untouched');
    }else{
      await phase(ctx,'seed');
      await phase(ctx,'migrate');
      await ctx.close();ctx=null;
      // Reopening ciphertext and source in an independent Chromium process.
      ctx=await chromium.launchPersistentContext(profile,{headless:true,
        locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
      await phase(ctx,'verify');
      await phase(ctx,'physical_bytes');
    }
  }catch(e){results.push({phase:'harness',pass:false,errorName:e.name||'Error'});}
  finally{
    if(ctx)await ctx.close().catch(()=>{});
    key.fill(0);
    fs.rmSync(profile,{recursive:true,force:true});
  }
  fs.mkdirSync('d18-candidate-migration-proof',{recursive:true});
  fs.writeFileSync('d18-candidate-migration-proof/'+
    (mode==='baseline'?'report.json':'report-'+mode+'.json'),JSON.stringify({
    head:process.env.GITHUB_SHA||null,
    kind:'synthetic_full_schema_into_unpublished_cipher_worker',
    mode,results},null,2));
  console.log(JSON.stringify(results));
  const expected=mode==='missing_source'
    ? ['migrate','assert_missing_source_untouched']
    : mode==='missing_trigger'
      ? ['seed_missing_trigger','migrate','assert_missing_trigger_untouched']
      : ['seed','migrate','verify','physical_bytes'];
  if(results.length!==expected.length||results.some((v,i)=>!v.pass||v.phase!==expected[i]))
    process.exitCode=1;
})().catch(e=>{console.error('D18_STAGE3_FATAL',e.name);process.exitCode=1;});
