// Real VFS/worker/Drift schema test on synthetic data, never clinical release.
'use strict';
const fs = require('node:fs');
const {chromium,webkit} = require('playwright');
const name = process.env.D1_BROWSER||'chromium';
const report = {name:'D1_HIGH_RUNTIME_ADMISSION_CANDIDATE',browser:name,
 patientRuntimeEnabled:false,synthetic:true,patientRelease:'NO_GO',
 result:'NOT_RUN',steps:[]};
async function phase(ctx,step){
 const page=await ctx.newPage();
 try{
  await page.goto('http://127.0.0.1:7409/?phase='+step,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.title.startsWith('D1_HIGH_PASS_')||
      document.title.startsWith('D1_HIGH_FAIL_'),null,{timeout:50000});
  const title=await page.title();
  report.steps.push({step,title});
  if(title!=='D1_HIGH_PASS_'+step.toUpperCase())throw Error(step+' got '+title);
  return page;
 }catch(err){await page.close();throw err}
}
async function inspectIdb(page){
 return page.evaluate(async ()=>{
  const dbName='d1_encrypted_v1_amina_vault_v1_native_731';
  const marker='D1_HIGH_FAKE_PATIENT_ROW_731';
  const names=await indexedDB.databases();
  if(!names.some(o=>o.name===dbName))throw Error('ENCRYPTED_IDB_ABSENT');
  const db=await new Promise((resolve,reject)=>{
    const q=indexedDB.open(dbName);
    q.onsuccess=()=>resolve(q.result);
    q.onerror=()=>reject(q.error);
  });
  const parts=[],encoder=new TextEncoder();
  async function walk(v,depth=0){
   if(depth>12)throw Error('IDB_NESTING');
   if(v==null||typeof v==='number'||typeof v==='boolean')return;
   if(typeof v==='string'){parts.push(encoder.encode(v));return;}
   if(v instanceof ArrayBuffer){parts.push(new Uint8Array(v));return;}
   if(ArrayBuffer.isView(v)){parts.push(new Uint8Array(v.buffer,v.byteOffset,v.byteLength));return;}
   if(v instanceof Blob){parts.push(new Uint8Array(await v.arrayBuffer()));return;}
   if(typeof v==='object')for(const x of Object.values(v))await walk(x,depth+1);
  }
  try{
   for(const store of [...db.objectStoreNames]){
    const req=db.transaction(store,'readonly').objectStore(store).getAll();
    const data=await new Promise((resolve,reject)=>{
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
    });
    for(const v of data)await walk(v);
   }
  }finally{db.close()}
  const needle=encoder.encode(marker);
  const seen=parts.some(part=>{
   outer:for(let i=0;i<=part.length-needle.length;i++){
    for(let j=0;j<needle.length;j++)if(part[i+j]!==needle[j])continue outer;
    return true;
   }
   return false;
  });
  return {rawBlocks:parts.length,rawBytes:parts.reduce((n,v)=>n+v.length,0),
   plaintextMarkerFound:seen};
 });
}
(async()=>{
 const engine={chromium,webkit}[name];if(!engine)throw Error('BROWSER');
 const browser=await engine.launch({headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})});
 try {
  const ctx=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  for(const p of ['unkeyed','locked','foreign','missing_key']){
   const page=await phase(ctx,p);await page.close();
  }
  let page=await phase(ctx,'seed');
  report.physical=await inspectIdb(page);await page.close();
  if(report.physical.rawBlocks<1||report.physical.rawBytes<256||
      report.physical.plaintextMarkerFound)throw Error('PHYSICAL_CIPHERTEXT_NOT_PROVEN');
  for(const p of ['reopen','wrong_key','retire']){
   page=await phase(ctx,p);await page.close();
  }
  report.result='PASS_D1_RUNTIME_CANDIDATE_SYNTHETIC';
  console.log(JSON.stringify(report,null,2));
  await ctx.close();
 }catch(e){report.result='FAIL';report.error=String(e).slice(0,320);console.error(e);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-high-runtime-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
