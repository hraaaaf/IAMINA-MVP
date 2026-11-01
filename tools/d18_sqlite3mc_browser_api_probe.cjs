/* D18 isolated browser API discovery: synthetic-only; NOT an at-rest encryption proof. */
'use strict';
const {chromium}=require('playwright');
const path=require('node:path');
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
   const out={opened:false,keyAccepted:false,wrote:false,encryptedPersistenceVerified:false};
   let id;
   try{
    const o=await p('open',{filename:'/d18-test.sqlite3',vfs:'opfs'});
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
  console.log(JSON.stringify({opfsKeyedExploration:opfs}));
  if(worker.opfsRegistered)console.log('OPFS_VFS_AVAILABLE_REQUIRES_KEYED_PERSISTENCE_TEST');
  console.log(JSON.stringify({persistenceGate:worker.opfsRegistered?'OPFS_AVAILABLE_NOT_YET_ENCRYPTION_PROOF':'BLOCKED_NO_OPFS_VFS',encryptedPersistenceVerified:false}));
  if(result.keyApi!=='function')throw Error('BLOCKED: sqlite3_key is not exposed by sqlite3mc browser C API');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
