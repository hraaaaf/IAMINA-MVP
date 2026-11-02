// Real Chromium + independent processes; synthetic-only.
'use strict';
const {chromium} = require('playwright');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const userData = fs.mkdtempSync(path.join(os.tmpdir(),'d18-mc-'));
const required=['stock_reject','write','wrong_key','read','isolation_b',
  'raw_bytes','rotate','old_key_reject','read_rotated',
  'raw_bytes_after_rotate'];
const steps=[];
async function phase(ctx,name){
  const p=await ctx.newPage();
  try{
    await p.goto('http://127.0.0.1:7396/?phase='+name,
      {waitUntil:'domcontentloaded',timeout:45000});
    await p.waitForFunction(()=>document.title.startsWith('D18_CIPHER_PASS:')||
      document.title.startsWith('D18_CIPHER_FAIL:'),null,{timeout:50000});
    const r=await p.evaluate(()=>({title:document.title,
      stage:document.documentElement.dataset.d18CipherStage||null,
      backend:document.documentElement.dataset.d18CipherBackend||null,
      error:document.documentElement.dataset.d18CipherError||null}));
    const pass=r.title==='D18_CIPHER_PASS:'+name;
    steps.push({phase:name,pass,backend:r.backend,
      ...(!pass?{stage:r.stage,error:r.error}:{})});
    if(!pass)throw Error('D18 POC failure '+JSON.stringify(steps.at(-1)));
  }finally{await p.close()}
}
(async()=>{
  let ctx;
  try{
    ctx=await chromium.launchPersistentContext(userData,
      {headless:true,locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    for(const p of required.slice(0,2))await phase(ctx,p);
    await ctx.close();ctx=null;
    ctx=await chromium.launchPersistentContext(userData,
      {headless:true,locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    for(const p of required.slice(2,7))await phase(ctx,p);
    await ctx.close();ctx=null;
    ctx=await chromium.launchPersistentContext(userData,
      {headless:true,locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    for(const p of required.slice(7))await phase(ctx,p);
  }catch(e){steps.push({phase:'harness',pass:false,error:String(e).slice(0,350)})}
  finally{if(ctx)await ctx.close();fs.rmSync(userData,{recursive:true,force:true})}
  fs.mkdirSync('d18-cipher-poc-proof',{recursive:true});
  fs.writeFileSync('d18-cipher-poc-proof/report.json',
    JSON.stringify({head:process.env.GITHUB_SHA||null,steps},null,2));
  console.log(JSON.stringify(steps));
  if(steps.length!==required.length||
      steps.some((s,i)=>!s.pass||s.phase!==required[i]))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
