// D18 PRE-CUTOVER browser-only SYNTHETIC IndexedDB CAS proof.
// NOT a clinical marker store or patient vault migration/activation.
'use strict';
const {chromium,webkit}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),http=require('node:http');
const engineName=process.env.D18_MARKER_BROWSER||'chromium';
if(!['chromium','webkit'].includes(engineName))throw Error('D18_MARKER_UNSUPPORTED_ENGINE');
const engine=engineName==='webkit'?webkit:chromium;
const root=fs.mkdtempSync(path.join(os.tmpdir(),'d18-cutover-idb-only-'));
const profile=path.join(root,'synthetic-browser-profile');
const syntheticScope='amina_vault_v1_device_aaaaaaaaaaaa4aaa8aaaaaaaaaaaaaaa';
const databaseName='iamina_d18_cutover_marker_TEST_ONLY_v1',storeName='markers';
const reports=[];
function check(value,code){if(!value)throw Error(code);}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const params=()=>({headless:true,locale:'fr-FR',viewport:{width:390,height:844},
 ...(engineName==='chromium'?{args:['--no-sandbox','--disable-dev-shm-usage']}: {})});
const server=http.createServer((_req,res)=>{
 res.writeHead(200,{'content-type':'text/html; charset=utf-8','cache-control':'no-store'});
 res.end('<!doctype html><html lang="fr"><meta charset="utf-8"><title>D18 CAS synthetic</title></html>');
});
async function withDb(page,operation,payload={}){
 return page.evaluate(async ({operation,payload,databaseName,storeName,syntheticScope})=>{
  const db=await new Promise((resolve,reject)=>{
   const opening=indexedDB.open(databaseName,1);
   opening.onupgradeneeded=()=>opening.result.createObjectStore(storeName);
   opening.onsuccess=()=>resolve(opening.result);
   opening.onerror=()=>reject(opening.error||new Error('IDB_OPEN_FAILED'));
   opening.onblocked=()=>reject(new Error('IDB_OPEN_BLOCKED'));
  });
  try{
   if(operation==='read'){
    return await new Promise((resolve,reject)=>{
     const tx=db.transaction(storeName,'readonly');
     const get=tx.objectStore(storeName).get(syntheticScope);
     let result=null;
     get.onsuccess=()=>{result=get.result??null;};
     tx.oncomplete=()=>resolve(result);
     tx.onabort=()=>reject(tx.error||new Error('IDB_READ_ABORT'));
     tx.onerror=()=>reject(tx.error||new Error('IDB_READ_ERROR'));
    });
   }
   return await new Promise((resolve,reject)=>{
    const tx=db.transaction(storeName,'readwrite',{durability:'strict'});
    const store=tx.objectStore(storeName);
    let wrote=false,intentionallyAborted=false;
    tx.oncomplete=()=>resolve({wrote,abortedAsExpected:false});
    tx.onabort=()=>{
     if(operation==='abort_after_put'&&intentionallyAborted)
      resolve({wrote:false,abortedAsExpected:true});
     else reject(tx.error||new Error('IDB_UNEXPECTED_TRANSACTION_ABORT'));
     else reject(tx.error||new Error('IDB_CAS_ABORT'));
    };
    // Deliberate tx.abort may dispatch an error event before onabort.
    // Only ignore that event if the fixture itself initiated the abort.
    // The phase still insists on abort ACK and unchanged physical marker.
    tx.onerror=()=>{
     if(operation==='abort_after_put'&&intentionallyAborted)return;
     reject(tx.error||new Error('IDB_CAS_ERROR'));
    };
    const read=store.get(syntheticScope);
    read.onsuccess=()=>{
     const actual=read.result??null,expected=payload.expected??null;
     // Synthetic fixture only; production requires canonical versioned equality.
     if(JSON.stringify(actual)!==JSON.stringify(expected))return;
     store.put(payload.next,syntheticScope);
     wrote=true;
     if(operation==='abort_after_put'){
      intentionallyAborted=true;
      tx.abort();
     }
    };
    // No await between read.onsuccess and store.put.
    // 'complete' is the commit signal, not the put's request success.
   });
  }finally{db.close();}
 },{operation,payload,databaseName,storeName,syntheticScope});
}
async function run(){
 const markerA={v:1,source:syntheticScope,target:syntheticScope+'_d18_cipher_v1',
  phase:'prepared',digest:'a'.repeat(64)};
 const markerB={...markerA,digest:'b'.repeat(64)};
 let context,secondContext;
 await new Promise((resolve,reject)=>{
  server.once('error',reject);
  server.listen(0,'127.0.0.1',resolve);
 });
 const origin='http://127.0.0.1:'+server.address().port+'/';
 try{
  context=await engine.launchPersistentContext(profile,params());
  const first=await context.newPage(),second=await context.newPage();
  await Promise.all([first.goto(origin),second.goto(origin)]);
  check(await withDb(first,'read')===null,'D18_CAS_NONEMPTY_FRESH_PROFILE');
  const [a,b]=await Promise.all([
   withDb(first,'compare_and_swap',{expected:null,next:markerA}),
   withDb(second,'compare_and_swap',{expected:null,next:markerB}),
  ]);
  check(Number(a.wrote)+Number(b.wrote)===1,'D18_CAS_TWO_FIRST_WRITERS');
  reports.push({phase:'two_tabs_one_prepared_winner',pass:true});
  const winner=a.wrote?markerA:markerB;
  check(same(await withDb(first,'read'),winner),'D18_CAS_FIRST_WINNER_NOT_PERSISTED');
  reports.push({phase:'prepared_persisted',pass:true});
  const stale=await withDb(second,'compare_and_swap',{expected:null,next:markerB});
  check(!stale.wrote&&same(await withDb(second,'read'),winner),
    'D18_CAS_STALE_WRITE_NOT_REJECTED');
  reports.push({phase:'stale_cas_denied',pass:true});
  const aborted=await withDb(second,'abort_after_put',{
   expected:winner,next:{...winner,phase:'ciphertextActive'}});
  check(aborted.abortedAsExpected&&!aborted.wrote,'D18_CAS_ABORT_NOT_RECOGNIZED');
  check(same(await withDb(first,'read'),winner),'D18_CAS_ABORT_PUBLISHED_PARTIAL_MARKER');
  reports.push({phase:'abort_rolls_back',pass:true});
  await context.close();context=null;
  context=await engine.launchPersistentContext(profile,params());
  const third=await context.newPage(),fourth=await context.newPage();
  await Promise.all([third.goto(origin),fourth.goto(origin)]);
  check(same(await withDb(third,'read'),winner),
    'D18_CAS_PREPARED_LOST_AFTER_BROWSER_RESTART');
  reports.push({phase:'prepared_survives_restart',pass:true});
  const promoted={...winner,phase:'ciphertextActive'};
  const [p1,p2]=await Promise.all([
   withDb(third,'compare_and_swap',{expected:winner,next:promoted}),
   withDb(fourth,'compare_and_swap',{expected:winner,next:promoted}),
  ]);
  check(Number(p1.wrote)+Number(p2.wrote)===1,'D18_CAS_DOUBLE_PROMOTION');
  reports.push({phase:'two_tabs_one_activation_winner',pass:true});
  check(same(await withDb(third,'read'),promoted),'D18_CAS_ACTIVE_NOT_PERSISTED');
  reports.push({phase:'active_readback',pass:true});
  const replay=await withDb(fourth,'compare_and_swap',{
   expected:winner,next:promoted});
  check(!replay.wrote,'D18_CAS_STALE_PROMOTION_REPLAY');
  reports.push({phase:'active_replay_denied',pass:true});
  await context.close();context=null;
  secondContext=await engine.launchPersistentContext(profile,params());
  const reopened=await secondContext.newPage();await reopened.goto(origin);
  check(same(await withDb(reopened,'read'),promoted),
    'D18_CAS_ACTIVE_LOST_AFTER_RESTART');
  reports.push({phase:'active_survives_restart',pass:true});
 }finally{
  await secondContext?.close().catch(()=>{});
  await context?.close().catch(()=>{});
  await new Promise(resolve=>server.close(resolve));
  fs.rmSync(root,{recursive:true,force:true});
 }
}
(async()=>{
 try{await run();}
 catch(e){
  reports.push({phase:'harness',pass:false,errorName:e.name||'Error',
   errorCode:String(e.message||'').replace(/[^A-Za-z0-9_]/g,'_').slice(0,120)});
  process.exitCode=1;
 }
 fs.mkdirSync('d18-idb-marker-proof',{recursive:true});
 fs.writeFileSync('d18-idb-marker-proof/report-'+engineName+'.json',JSON.stringify({
  kind:'D18_SYNTHETIC_INDEXEDDB_CAS_NO_CLINICAL',
  sha:process.env.GITHUB_SHA||null,engine:engineName,reports},null,2));
 console.log(JSON.stringify(reports));
 if(reports.length!==9||reports.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error('D18_IDB_CAS_FATAL',e.name);process.exitCode=1;});
