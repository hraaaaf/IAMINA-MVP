// D1.6 synthetic SQLite3MC: physical IndexedDB bytes vs plain control.
// This does NOT touch the IAMINA production patient runtime.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[name];
if(!engine)throw Error('Unsupported Playwright engine');
const origin='http://127.0.0.1:7398/';
const fixture='D1_SQLITE3MC_FAKE_PATIENT_CANARY_8f4d7e23';
const driftMarker='d1-fake-drift-owner-731';
const cipher='iamina_d1p0c_sqlite3mc_synthetic_v1';
const plain='iamina_d1p0c_sqlite3mc_plain_control_v1';
const report={test:'D1_6_SQLITE3MC_REAL_INDEXEDDB_CIPHER',
 browser:name,synthetic:true,result:'NOT_RUN',phases:[],
 scope:'isolated SQLite3MC engine only; NOT patient runtime'};
async function phase(ctx,name) {
 const p=await ctx.newPage();
 const errors=[];
 p.on('pageerror',e=>errors.push('pageerror:'+String(e).slice(0,280)));
 p.on('requestfailed',req=>{
  if(req.url().includes('sqlite3mc.wasm'))
   errors.push('wasm-request-failed:'+String(req.failure()).slice(0,240));
 });
 p.on('response',resp=>{
  if(resp.url().includes('sqlite3mc.wasm'))
   errors.push('wasm-http-status:'+resp.status());
 });
 try{
  await p.goto(origin+'?phase='+name,{waitUntil:'domcontentloaded'});
  const wanted='IAMINA_D1P0C_PASS_'+name.toUpperCase();
  try{
   await p.waitForFunction(({wanted})=>
    document.title===wanted||document.title.startsWith('IAMINA_D1P0C_FAIL_'),
    {wanted},{timeout:25000});
  }catch(e){
   const diag=await p.evaluate(()=>({
    title:document.title,
    state:document.readyState,
    lease:document.documentElement.dataset.iaminaTabLease||null,
    wasmError:document.documentElement.dataset.d1WasmError||null,
    jsFiles:performance.getEntriesByType('resource')
     .filter(r=>r.name.includes('sqlite3mc')||r.name.includes('main.dart.js'))
     .map(r=>({name:r.name.split('/').pop(),responseEnd:r.responseEnd})),
   }));
   throw Error('timed out in '+name+': '+JSON.stringify({diag,errors}).slice(0,1300));
  }
  const got=await p.title();
  report.phases.push({phase:name,title:got});
  if(got!==wanted){
   const preKeyTransport=await p.evaluate(()=>
    document.documentElement.dataset.d1WasmError||'');
   throw Error('SQLite probe stage '+name+' failed with '+got+
    (preKeyTransport ? ' (pre-key wasm transport: '+preKeyTransport+')' : ''));
  }
  return p;
 }catch(e){await p.close();throw e;}
}
async function auditIdb(page,dbname) {
 return page.evaluate(async ({dbname,fixture,driftMarker})=>{
  const exists=await indexedDB.databases();
  if(!exists.some(x=>x.name===dbname))throw Error('IDB missing: '+dbname);
  const database=await new Promise((resolve,reject)=>{
   const request=indexedDB.open(dbname);
   request.onsuccess=()=>resolve(request.result);
   request.onerror=()=>reject(request.error);
  });
  const packets=[];
  const encode=new TextEncoder();
  let count=0;
  async function push(val,depth=0){
   if(depth>10)throw Error('unexpected IDB recursion');
   if(val==null)return;
   if(typeof val==='string'){packets.push(encode.encode(val));return;}
   if(typeof val==='number'||typeof val==='boolean')return;
   if(val instanceof ArrayBuffer){packets.push(new Uint8Array(val));return;}
   if(ArrayBuffer.isView(val)){
    packets.push(new Uint8Array(val.buffer,val.byteOffset,val.byteLength));return;
   }
   if(val instanceof Blob){
    packets.push(new Uint8Array(await val.arrayBuffer()));return;
   }
   if(typeof val==='object')for(const v of Object.values(val))await push(v,depth+1);
  }
  try{
   for(const storeName of Array.from(database.objectStoreNames)){
    const transaction=database.transaction(storeName,'readonly');
    const request=transaction.objectStore(storeName).getAll();
    const values=await new Promise((resolve,reject)=>{
     request.onsuccess=()=>resolve(request.result);
     request.onerror=()=>reject(request.error);
    });
    count+=values.length;
    for(const value of values)await push(value);
   }
  }finally{database.close();}
  if(!packets.length)throw Error('no actual IDB blocks inspected');
  function contains(needleText){
   const needle=encode.encode(needleText);
   return packets.some(block=>{
    position:for(let i=0;i<=block.byteLength-needle.byteLength;i++){
     for(let k=0;k<needle.byteLength;k++)
      if(block[i+k]!==needle[k])continue position;
     return true;
    }
    return false;
   });
  }
  return {idbName:dbname,rawBytes:packets.reduce((s,v)=>s+v.byteLength,0),
   blockCount:packets.length,objectCount:count,
   canaryInPhysicalBytes:contains(fixture),
   driftRowInPhysicalBytes:contains(driftMarker)};
 },{dbname,fixture,driftMarker});
}
(async()=>{
 const browser=await engine.launch({headless:true,
  ...(name==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const ctx=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  try{
   let page=await phase(ctx,'seed_plain');
   const ctrl=await auditIdb(page,plain);
   await page.close();
   report.phases.push({phase:'raw_control',proof:ctrl});
   if(!ctrl.canaryInPhysicalBytes||!ctrl.driftRowInPhysicalBytes)throw Error('plain control/Drift row NOT readable: experiment inconclusive');
   page=await phase(ctx,'seed_cipher');
   const encrypted=await auditIdb(page,cipher);
   await page.close();
   report.phases.push({phase:'raw_cipher',proof:encrypted});
   if(encrypted.canaryInPhysicalBytes||encrypted.driftRowInPhysicalBytes)throw Error('CRITICAL cleartext fixture/Drift row in encrypted storage');
   if(encrypted.rawBytes<100)throw Error('Insufficient physical ciphertext');
   page=await phase(ctx,'verify_cipher');await page.close();
   page=await phase(ctx,'wrong_key');await page.close();
   report.result='PASS_ENGINE_CIPHERTEXT_ONLY';
   console.log(JSON.stringify(report,null,2));
  }finally{await ctx.close();}
 }catch(err){
  report.result='FAIL';
  report.error=String(err).slice(0,650);
  console.error(err);
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0c-'+name+'-at-rest-proof.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
