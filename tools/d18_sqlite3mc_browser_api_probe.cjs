/* D18 isolated browser API discovery: synthetic-only; NOT an at-rest encryption proof. */
'use strict';
const {chromium}=require('playwright');
const path=require('node:path');
const fs=require('node:fs');
const os=require('node:os');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage();
  await page.goto('http://127.0.0.1:7398/d18-probe.html');
  const result=await page.evaluate(async()=>{
   if(typeof sqlite3InitModule!=='function')throw Error('sqlite3InitModule missing');
   const sqlite3=await sqlite3InitModule({locateFile:name=>'/jswasm/'+name});
   globalThis.__d18Sqlite3=sqlite3;
   const db=new sqlite3.oo1.DB(':memory:');
   try{
    db.exec('CREATE TABLE synthetic (v TEXT); INSERT INTO synthetic VALUES (\'D18_SYNTHETIC_ONLY\')');
    const rows=db.selectObjects('SELECT v FROM synthetic');
    if(rows[0]?.v!=='D18_SYNTHETIC_ONLY')throw Error('SQLite roundtrip failed');
    return {sqliteRoundtrip:true,keyApi:typeof sqlite3.capi.sqlite3_key,opfsApi:typeof sqlite3.oo1.OpfsDb,opfsStorageApi:typeof navigator.storage?.getDirectory,crossOriginIsolated:globalThis.crossOriginIsolated,sharedArrayBuffer:typeof SharedArrayBuffer,workerApi:typeof Worker,encryptedPersistenceVerified:false};
   }finally{db.close()}
  });
  console.log(JSON.stringify(result));
  if(!result.crossOriginIsolated||result.sharedArrayBuffer!=='function')throw Error('BLOCKED: Chromium probe lacks COOP/COEP isolation');
  const worker=await page.evaluate(async()=>{
   const url='/jswasm/sqlite3-worker1-promiser.js';
   const script=document.createElement('script');script.src=url;
   await new Promise((resolve,reject)=>{script.onload=resolve;script.onerror=()=>reject(Error('worker promiser script missing'));document.head.appendChild(script)});
   if(typeof sqlite3Worker1Promiser!=='function')throw Error('sqlite3Worker1Promiser missing');
   const promiser=await new Promise((resolve,reject)=>{
    try{const p=sqlite3Worker1Promiser({onready:()=>resolve(p),onerror:reject});}catch(e){reject(e)}
   });
   globalThis.d18Worker=promiser;
   const config=await promiser('config-get',{});
   const vfsList=config.result?.vfsList||[];
   const opfsRegistered=vfsList.some(v=>/opfs/i.test(v));
   const kvvfsRegistered=vfsList.includes('kvvfs');
   return {workerReady:true,configType:config.type,configKeys:Object.keys(config.result||{}),vfsList,opfsRegistered,kvvfsRegistered,opfsStorageApi:typeof navigator.storage?.getDirectory,crossOriginIsolated:globalThis.crossOriginIsolated,sharedArrayBuffer:typeof SharedArrayBuffer};
  });
  console.log(JSON.stringify(worker));
  const kvvfs=await page.evaluate(async()=>{
   const sqlite3=globalThis.__d18Sqlite3;
   if(!sqlite3)throw Error('Missing cached sqlite3 instance');
   const details={attempted:true,opened:false,reopened:false,wrongKeyRejected:false,rawStorageInspected:false,encryptedPersistenceVerified:false};
   const filename='local';
   let db;
   try{
    db=new sqlite3.oo1.DB({filename,vfs:'kvvfs'});
    details.opened=true;
    db.exec("PRAGMA key='D18_SYNTHETIC_KEY_NOT_FOR_PRODUCTION'");
    db.exec("CREATE TABLE IF NOT EXISTS d18_probe(v TEXT); DELETE FROM d18_probe; INSERT INTO d18_probe VALUES('D18_SYNTHETIC_ONLY')");
    db.close();db=null;
    details.rawStorageInspected=true;
    details.localStorageKeys=Object.keys(localStorage).filter(k=>k.startsWith('kvvfs-')).length;
    details.plaintextVisible=Object.values(localStorage).some(v=>v.includes('D18_SYNTHETIC_ONLY'));
    db=new sqlite3.oo1.DB({filename,vfs:'kvvfs'});
    db.exec("PRAGMA key='D18_SYNTHETIC_KEY_NOT_FOR_PRODUCTION'");
    details.reopened=db.selectObjects('SELECT v FROM d18_probe')[0]?.v==='D18_SYNTHETIC_ONLY';
   }catch(e){details.error=String(e)}
   finally{if(db)db.close()}
   return details;
  });
  console.log(JSON.stringify({kvvfsExploration:kvvfs}));
  const opfs=await page.evaluate(async()=>{
   const p=globalThis.d18Worker;
   const out={candidateVfs:'multipleciphers-opfs',opened:false,keyAccepted:false,wrote:false,encryptedPersistenceVerified:false};
   let id;
   try{
    const o=await p('open',{filename:'/d18-test-encrypted.sqlite3',vfs:'multipleciphers-opfs'});
    if(o.type==='error')throw Error(JSON.stringify({type:o.type,result:o.result,message:o.result?.message,operation:'open'}));
    id=o.dbId;out.opened=true;
    const k=await p('exec',{dbId:id,sql:"PRAGMA key='D18_TEST_ONLY'"});
    if(k.type==='error')throw Error(JSON.stringify({type:k.type,result:k.result,message:k.result?.message,operation:'key'}));
    out.keyAccepted=true;
    const w=await p('exec',{dbId:id,sql:"CREATE TABLE IF NOT EXISTS synthetic(v TEXT); INSERT INTO synthetic VALUES('D18_TEST_ONLY')"});
    if(w.type==='error')throw Error(JSON.stringify({type:w.type,result:w.result,message:w.result?.message,operation:'write'}));
    out.wrote=true;
   }catch(e){out.error=String(e);out.errorMessage=e?.message||null;out.errorDetails=JSON.stringify(e, Object.getOwnPropertyNames(e||{}));out.errorKeys=Object.keys(e||{});out.errorType=typeof e;out.workerResultProps=Object.getOwnPropertyNames(e?.result||{});out.workerResultDetails=JSON.stringify(e?.result,Object.getOwnPropertyNames(e?.result||{}));out.workerResultString=String(e?.result)}
   finally{if(id)await p('close',{dbId:id})}
   return out;
  });
  console.log(JSON.stringify({multipleciphersOpfsExploration:opfs}));
  const persistence=await page.evaluate(async()=>{
   const p=globalThis.d18Worker, file='/d18-test-encrypted.sqlite3',vfs='multipleciphers-opfs';
   const out={wrongKeyRejected:false,correctKeyRecovered:false,rawBytesInspected:false,plaintextFound:null,encryptedPersistenceVerified:false};
   async function run(key){
    let id;
    try{
     const o=await p('open',{filename:file,vfs});id=o.dbId;
     if(o.type==='error')throw o;
     const k=await p('exec',{dbId:id,sql:"PRAGMA key='"+key+"'"});
     if(k.type==='error')throw k;
     const q=await p('exec',{dbId:id,sql:'SELECT v FROM synthetic',rowMode:'array',resultRows:[]});
     if(q.type==='error')throw q;
     return {ok:true,rows:q.result?.resultRows||[]};
    }catch(e){return {ok:false,error:e?.result?.message||e?.message||String(e)}}
    finally{if(id)await p('close',{dbId:id})}
   }
   out.wrong=await run('D18_INCORRECT_KEY');
   out.wrongKeyRejected=!out.wrong.ok;
   out.correct=await run('D18_TEST_ONLY');
   out.correctKeyRecovered=out.correct.ok&&out.correct.rows.some(r=>r[0]==='D18_TEST_ONLY');
   try{
    const root=await navigator.storage.getDirectory();
    const names=[];
    for await(const [name,handle] of root.entries()){
     names.push(name);
     if(handle.kind==='file'){
      const bytes=new Uint8Array(await (await handle.getFile()).arrayBuffer());
      const text=new TextDecoder('latin1').decode(bytes);
      if(name.includes('d18-test-encrypted')){
       out.rawBytesInspected=true;
       out.plaintextFound=text.includes('D18_TEST_ONLY')||text.includes('CREATE TABLE');
       out.sqliteHeaderVisible=text.startsWith('SQLite format 3');
      }
     }
    }
    out.opfsRootEntries=names;
   }catch(e){out.rawError=String(e)}
   out.encryptedPersistenceVerified=out.wrongKeyRejected&&out.correctKeyRecovered&&out.rawBytesInspected&&out.plaintextFound===false&&out.sqliteHeaderVisible===false;
   return out;
  });
  console.log(JSON.stringify({opfsPersistenceExploration:persistence}));
  if(opfs.wrote&&!persistence.correctKeyRecovered)throw Error('D18 keyed OPFS failed correct-key reopen');
  if(opfs.wrote&&!persistence.wrongKeyRejected)throw Error('D18 keyed OPFS failed wrong-key rejection');

  if(worker.opfsRegistered)console.log('OPFS_VFS_AVAILABLE_REQUIRES_KEYED_PERSISTENCE_TEST');
  console.log(JSON.stringify({persistenceGate:worker.opfsRegistered?'OPFS_AVAILABLE_NOT_YET_ENCRYPTION_PROOF':'BLOCKED_NO_OPFS_VFS',encryptedPersistenceVerified:false}));
  if(result.keyApi!=='function')throw Error('BLOCKED: sqlite3_key is not exposed by sqlite3mc browser C API');


  // Independent Chromium processes, same persistent profile; synthetic data only.
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'d18-opfs-restart-'));
  async function restartPhase(phase){
   const context=await chromium.launchPersistentContext(profile,{headless:true,args:['--no-sandbox']});
   try{
    const tab=context.pages()[0]||await context.newPage();
    await tab.goto('http://127.0.0.1:7398/d18-probe.html');
    return await tab.evaluate(async(phase)=>{
     const script=document.createElement('script');script.src='/jswasm/sqlite3-worker1-promiser.js';
     await new Promise((resolve,reject)=>{script.onload=resolve;script.onerror=reject;document.head.appendChild(script)});
     const p=await new Promise((resolve,reject)=>{try{const x=sqlite3Worker1Promiser({onready:()=>resolve(x),onerror:reject})}catch(e){reject(e)}});
     const file='/d18-restart-encrypted.sqlite3',vfs='multipleciphers-opfs';
     const details={phase,isolated:crossOriginIsolated,ok:false};
     async function attempt(key,write){
      let id;
      try{
       const o=await p('open',{filename:file,vfs});if(o.type==='error')throw o;id=o.dbId;
       const k=await p('exec',{dbId:id,sql:"PRAGMA key='"+key+"'"});if(k.type==='error')throw k;
       const sql=write?"CREATE TABLE synthetic(v TEXT); INSERT INTO synthetic VALUES('D18_RESTART_SENTINEL')":'SELECT v FROM synthetic';
       const q=await p('exec',{dbId:id,sql,rowMode:'array',resultRows:[]});if(q.type==='error')throw q;
       return {ok:true,rows:q.result?.resultRows||[]};
      }catch(e){return {ok:false,error:e?.result?.message||String(e)}}
      finally{if(id)await p('close',{dbId:id})}
     }
     if(phase==='write'){details.write=await attempt('D18_RESTART_KEY',true);details.ok=details.write.ok}
     else{
      details.wrong=await attempt('D18_WRONG_KEY',false);
      details.correct=await attempt('D18_RESTART_KEY',false);
      details.ok=!details.wrong.ok&&details.correct.ok&&details.correct.rows.some(r=>r[0]==='D18_RESTART_SENTINEL');
     }
     return details;
    },phase);
   }finally{await context.close()}
  }
  try{
   const first=await restartPhase('write');
   console.log(JSON.stringify({persistentProcessWrite:first}));
   if(!first.ok)throw Error('D18 persistent Chromium initial keyed write failed');
   const second=await restartPhase('reopen');
   console.log(JSON.stringify({persistentProcessRestart:second}));
   if(!second.ok)throw Error('D18 persistent Chromium restart wrong-key/correct-key gate failed');
  }finally{fs.rmSync(profile,{recursive:true,force:true})}
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
