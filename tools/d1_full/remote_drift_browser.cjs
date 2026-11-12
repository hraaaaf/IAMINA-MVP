// A real Drift remote connection from a browser to SQLite3MC inside a worker.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const report={test:'D1_SYNTHETIC_REAL_APPDATABASE_REMOTE',browser:name,
 patientRuntime:false,synthetic:true,result:'NOT_RUN',steps:[]};
// Inspect the raw physical IndexedDB blocks after a complete worker flush.
// No source-level assertions are accepted as a substitute for byte inspection.
async function rawIdbProof(tab){
 return tab.evaluate(async ()=>{
  const dbName='d1_synthetic_remote_drift_731';
  const marker='D1_REAL_REMOTE_APPDATABASE_ROW_731';
  const dbs=await indexedDB.databases();
  if(!dbs.some(d=>d.name===dbName))throw Error('IDB_MISSING');
  const db=await new Promise((resolve,reject)=>{
   const req=indexedDB.open(dbName);
   req.onsuccess=()=>resolve(req.result);
   req.onerror=()=>reject(req.error);
  });
  const blocks=[];
  const encoder=new TextEncoder();
  async function add(value,depth=0){
   if(depth>10)throw Error('IDB_RECURSION');
   if(value==null)return;
   if(typeof value==='string'){blocks.push(encoder.encode(value));return;}
   if(typeof value==='boolean'||typeof value==='number')return;
   if(value instanceof ArrayBuffer){blocks.push(new Uint8Array(value));return;}
   if(ArrayBuffer.isView(value)){blocks.push(new Uint8Array(value.buffer,value.byteOffset,value.byteLength));return;}
   if(value instanceof Blob){blocks.push(new Uint8Array(await value.arrayBuffer()));return;}
   if(typeof value==='object')for(const child of Object.values(value))await add(child,depth+1);
  }
  try{
   for(const store of [...db.objectStoreNames]){
    const req=db.transaction(store,'readonly').objectStore(store).getAll();
    const values=await new Promise((resolve,reject)=>{
     req.onsuccess=()=>resolve(req.result);
     req.onerror=()=>reject(req.error);
    });
    for(const v of values)await add(v);
   }
  }finally{db.close();}
  const needle=encoder.encode(marker);
  const contains=blocks.some(block=>{
   start:for(let i=0;i<=block.length-needle.length;i++){
    for(let j=0;j<needle.length;j++)if(block[i+j]!==needle[j])continue start;
    return true;
   }
   return false;
  });
  return {storage:'IndexedDB',blockCount:blocks.length,
    rawBytes:blocks.reduce((sum,v)=>sum+v.byteLength,0),
    sensitiveSyntheticMarkerInRawStorage:contains};
 });
}

async function phase(ctx,p){
 const tab=await ctx.newPage();
 const failures=[];
 tab.on('pageerror',err=>{
  // The page hosts only hard-coded synthetic fixtures. Do not log arbitrary
  // SQL or credentials: only a small, scrubbed startup error category.
  const message=String(err.message||'')
    .replace(/D1_[A-Z0-9_]+/g,'[SYNTHETIC_REDACTED]')
    .replace(/[a-f0-9]{64,}/gi,'[HEX_REDACTED]')
    .slice(0,400);
  failures.push({kind:'pageerror',type:err.name||'unknown',message});
 });
 tab.on('requestfailed',req=>failures.push({
   kind:'requestfailed',asset:new URL(req.url()).pathname.split('/').pop(),
 }));
 try{
  await tab.goto('http://127.0.0.1:7405/?phase='+p);
  await tab.waitForFunction(()=>
   document.title.startsWith('D1_REMOTE_PASS_')||
   document.title.startsWith('D1_REMOTE_FAIL_'),null,{timeout:55000});
  const title=await tab.title();
  report.steps.push({phase:p,title});
  if(title!=='D1_REMOTE_PASS_'+p.toUpperCase())throw Error(p+' got '+title);
  return tab;
 }catch(err){
  const diag=await tab.evaluate(()=>({
   title:document.title,ready:document.readyState,
   scripts:[...document.scripts].map(x=>(x.src||'inline').split('/').pop()),
   resources:performance.getEntriesByType('resource')
     .filter(x=>/main.dart.js|flutter_bootstrap.js|sqlite3mc.wasm|d1_synthetic_remote_drift_worker.js/.test(x.name))
     .map(x=>({asset:x.name.split('/').pop(),loaded:x.responseEnd>0})),
  })).catch(()=>({unavailable:true}));
  report.steps.push({phase:p,diagnostic:diag,failures});
  await tab.close();
  throw Error(p+' failed: '+String(err.name||'Error')+' '+JSON.stringify({diag,failures}).slice(0,950));
 }
}
(async()=>{
 const browser=await {chromium,webkit}[name].launch({
  headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})
 });
 try{
  const ctx=await browser.newContext({serviceWorkers:'block'});
  const seeded=await phase(ctx,'seed');
  try{
   report.physicalIndexedDb=await rawIdbProof(seeded);
   if(report.physicalIndexedDb.blockCount<1||
     report.physicalIndexedDb.rawBytes<256||
     report.physicalIndexedDb.sensitiveSyntheticMarkerInRawStorage){
     throw Error('REAL_REMOTE_DRIFT_CIPHERTEXT_NOT_PROVEN');
   }
  }finally{await seeded.close();}
  for(const p of ['reopen','wrong_key','missing_key']){
   const tab=await phase(ctx,p);
   await tab.close();
  }
  report.result='PASS_REMOTE_DRIFT_CIPHER_PHYSICAL_IDB';
  console.log(JSON.stringify(report,null,2));
  await ctx.close();
 }catch(err){report.result='FAIL';report.error=String(err).slice(0,260);
  console.error(err);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-remote-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
