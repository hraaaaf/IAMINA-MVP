// Browser proof of a REAL dedicated Web Worker with SQLite3MC IDB encryption.
// No patient data, auth, clinical code paths or application bootstrap.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const browserName=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[browserName];
const prefix='http://127.0.0.1:7399/';
const canary='D1_WORKER_SYNTHETIC_CANARY_20261112';
const driftMarker='D1_WORKER_DRIFT_MARKER_731';
const plain='d1_synthetic_real_worker_plain_20261112';
const cipher='d1_synthetic_real_worker_cipher_20261112';
const report={lot:'D1_REAL_DEDICATED_WORKER_SYNTHETIC',browser:browserName,
 synthetic:true,patientRuntime:false,result:'NOT_RUN',phases:[]};
async function phase(page,step){
 const result=await page.evaluate(async ({step})=>{
  return new Promise((resolve,reject)=>{
   const worker=new Worker('d1_synthetic_real_worker.js');
   const timeout=setTimeout(()=>{worker.terminate();reject(Error('WORKER_TIMEOUT'));},30000);
   worker.onerror=()=>{clearTimeout(timeout);worker.terminate();reject(Error('WORKER_ERROR'));};
   worker.onmessage=event=>{clearTimeout(timeout);worker.terminate();resolve(event.data);};
   worker.postMessage(JSON.stringify({phase:step}));
  });
 },{step});
 report.phases.push({phase:step,status:result});
 if(result!=='PASS_'+step.toUpperCase())throw Error(step+': '+result);
}
async function audit(page,dbname){
 return page.evaluate(async ({dbname,canary,driftMarker})=>{
  const names=await indexedDB.databases();
  if(!names.some(x=>x.name===dbname))throw Error('IDB_MISSING');
  const db=await new Promise((resolve,reject)=>{
   const open=indexedDB.open(dbname);
   open.onsuccess=()=>resolve(open.result);
   open.onerror=()=>reject(open.error);
  });
  const chunks=[], encoder=new TextEncoder();
  async function visit(value,depth=0){
   if(depth>12)throw Error('RECURSION');
   if(value==null)return;
   if(typeof value==='string'){chunks.push(encoder.encode(value));return;}
   if(typeof value==='number'||typeof value==='boolean')return;
   if(value instanceof ArrayBuffer){chunks.push(new Uint8Array(value));return;}
   if(ArrayBuffer.isView(value)){chunks.push(new Uint8Array(value.buffer,value.byteOffset,value.byteLength));return;}
   if(value instanceof Blob){chunks.push(new Uint8Array(await value.arrayBuffer()));return;}
   if(typeof value==='object')for(const v of Object.values(value))await visit(v,depth+1);
  }
  try{
   for(const store of [...db.objectStoreNames]){
    const tx=db.transaction(store,'readonly');
    const values=await new Promise((resolve,reject)=>{
     const q=tx.objectStore(store).getAll();q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);
    });
    for(const v of values)await visit(v);
   }
  }finally{db.close()}
  if(!chunks.length)throw Error('EMPTY_PHYSICAL_STORAGE');
  function containsMarker(text){
   const needle=encoder.encode(text);
   return chunks.some(chunk=>{
    outer:for(let i=0;i<=chunk.length-needle.length;i++){
     for(let j=0;j<needle.length;j++)if(chunk[i+j]!==needle[j])continue outer;
     return true;
    }
    return false;
   });
  }
  return {dbname,blocks:chunks.length,bytes:chunks.reduce((n,x)=>n+x.length,0),
   containsCanary:containsMarker(canary),containsDriftRow:containsMarker(driftMarker)};
 },{dbname,canary,driftMarker});
}
(async()=>{
 if(!engine)throw Error('UNSUPPORTED_BROWSER');
 const browser=await engine.launch({headless:true,...(browserName==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const page=await browser.newPage({serviceWorkers:'block'});
  await page.goto(prefix+'d1_synthetic_worker_harness.html');
  await phase(page,'seed_plain');
  const control=await audit(page,plain);
  report.control=control;
  if(!control.containsCanary||!control.containsDriftRow)throw Error('CONTROL_CLEAR_MARKER_ABSENT');
  await phase(page,'seed_cipher');
  const encrypted=await audit(page,cipher);
  report.encrypted=encrypted;
  if(encrypted.containsCanary||encrypted.containsDriftRow||encrypted.bytes<256)throw Error('CIPHERTEXT_NOT_PROVEN');
  await phase(page,'verify_cipher');
  await phase(page,'wrong_key');
  await phase(page,'no_key');
  report.result='PASS_REAL_WORKER_CIPHERTEXT_ONLY';
  console.log(JSON.stringify(report,null,2));
 }catch(error){report.result='FAIL';report.error=String(error).slice(0,240);console.error(error);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-real-worker-'+browserName+'-proof.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
