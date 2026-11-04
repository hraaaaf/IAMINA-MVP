// IAMINA D18 step 2/6 — isolated, SYNTHETIC browser lock tests.
// NOT linked to patient runtime, and not yet a CI certification.
'use strict';
const {chromium}=require('playwright');
const {randomBytes}=require('node:crypto');
const fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-unpublished-lock-'));
const origin=process.env.D18_TEST_ORIGIN || 'http://127.0.0.1:7396';
const a='amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018';
const b='amina_vault_v1_device_e2dbe28f3eea441086a7274150b00018';
const name=s=>s+'_d18_cipher_v1';
const lockName=s=>'iamina:d18:encrypted:v1:'+name(s);
const keyA=[...randomBytes(32)], keyB=[...randomBytes(32)];
const results=[];
function check(phase,pass){
  results.push({phase,pass:!!pass});
  if(!pass)throw Error('D18_STAGE2_'+phase+'_FAILED');
}
async function makePage(ctx){
  const p=await ctx.newPage();
  await p.route('**/d18_stage2_owner.html', route=>route.fulfill({
    status:200,contentType:'text/html',
    body:'<!doctype html><html><title>D18 CI</title></html>',
  }));
  await p.goto(origin+'/d18_stage2_owner.html',{waitUntil:'domcontentloaded'});
  return p;
}
async function open(page,scope,intent,key,retain=false,physical=name(scope)){
  return page.evaluate(async data=>{
    const worker=new Worker('/d18_unpublished_cipher_worker.js');
    const control=new MessageChannel(),sql=new MessageChannel();
    const bytes=Uint8Array.from(data.key);
    let kept=false;
    try{
      const response=new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(Error('ACK_TIMEOUT')),15000);
        control.port1.onmessage=e=>{clearTimeout(timer);resolve(e.data);};
      });
      worker.postMessage({type:'D18_UNPUBLISHED_KEYED_OPEN',
        scope:data.scope,name:data.physical,intent:data.intent,key:bytes.buffer},
        [control.port2,sql.port2,bytes.buffer]);
      const status=await response;
      if(data.retain&&status==='READY_FRESH'){
        window.__d18Stage2={worker,control:control.port1,sql:sql.port1};
        kept=true;
      }
      return status;
    }catch(_){return 'ACK_TIMEOUT';}
    finally{
      if(!kept){control.port1.close();sql.port1.close();worker.terminate();}
    }
  },{scope,intent,key,retain,physical});
}
async function held(page,scope){
  return page.evaluate(async lock=>{
    const q=await navigator.locks.query();
    return q.held.some(x=>x.name===lock);
  },lockName(scope));
}
async function release(page,scope){
  await page.evaluate(()=>{
    const v=window.__d18Stage2;
    if(!v)throw Error('NO_OWNER');
    v.worker.terminate();v.control.close();v.sql.close();
    delete window.__d18Stage2;
  });
  return page.waitForFunction(async lock=>{
    const q=await navigator.locks.query();
    return !q.held.some(x=>x.name===lock);
  },lockName(scope),{timeout:15000}).then(()=>true).catch(()=>false);
}
(async()=>{
  let ctx;const pages=[];
  try{
    ctx=await chromium.launchPersistentContext(profile,{headless:true,
      locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    const ownerA=await makePage(ctx);pages.push(ownerA);
    const other=await makePage(ctx);pages.push(other);
    const ownerB=await makePage(ctx);pages.push(ownerB);
    check('a_owner_open',await open(ownerA,a,'createFresh',keyA,true)==='READY_FRESH');
    check('a_lock_held',await held(ownerA,a));
    check('a_second_writer_denied',await open(other,a,'createFresh',keyA)==='LOCK_UNAVAILABLE');
    check('a_reader_denied',await open(other,a,'reopenExisting',keyA)==='LOCK_UNAVAILABLE');
    check('b_independent',await open(ownerB,b,'createFresh',keyB,true)==='READY_FRESH');
    check('b_lock_held',await held(ownerB,b));
    check('scope_spoof_denied',await open(other,a,'reopenExisting',keyA,false,name(b))==='REJECTED');
    check('a_releases',await release(ownerA,a));
    check('b_still_held',await held(ownerB,b));
    check('b_releases',await release(ownerB,b));
  }catch(e){
    results.push({phase:'harness',pass:false,error:String(e).slice(0,180)});
  }finally{
    for(const p of pages)await p.close().catch(()=>{});
    if(ctx)await ctx.close().catch(()=>{});
    fs.rmSync(profile,{recursive:true,force:true});
  }
  fs.mkdirSync('d18-unpublished-lock-proof',{recursive:true});
  fs.writeFileSync('d18-unpublished-lock-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA||null,results,
  },null,2));
  console.log(JSON.stringify(results));
  if(results.length!==10||results.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{
  console.error('D18_STAGE2_HARNESS_FATAL',e.name);
  process.exitCode=1;
});
