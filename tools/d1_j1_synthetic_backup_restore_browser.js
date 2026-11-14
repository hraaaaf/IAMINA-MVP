// D1/J1 SYNTHETIC ONLY: byte-faithful logical IndexedDB snapshot with
// metadata/indexes, SHA-256, fresh-profile restore, tamper and overwrite denial.
// Not a physical SQLite/WAL backup, not a production export or clinical GO.
'use strict';
const {chromium}=require('playwright');
const fs=require('fs');
const dir='d1-j1-synthetic-backup-proof';
const origin='http://127.0.0.1:7481';
const names=['amina','amina_vault_v1_native_734','amina_vault_v1_native_812'];
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',clinicalGo:false,
  mode:'synthetic logical IndexedDB archive, NOT physical SQLite bytes',
  result:'NOT_RUN'};
function check(value,label){if(!value)throw Error('J1 ASSERT: '+label);}

async function invoke(page,fun,arg){
  return page.evaluate(fun,arg);
}
async function inventoryAndBackup(page,selectedNames=names){
  return invoke(page,async names=>{
    function request(req){return new Promise((resolve,reject)=>{
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
    });}
    async function encode(value){
      if(value===null)return {t:'null'};
      if(value===undefined)return {t:'undefined'};
      const type=typeof value;
      if(type==='string'||type==='boolean')return {t:type,v:value};
      if(type==='number'){
        if(!Number.isFinite(value))throw Error('J1_UNSUPPORTED_NON_FINITE');
        return {t:'number',v:value};
      }
      if(type==='bigint')return {t:'bigint',v:String(value)};
      if(value instanceof Date){
        if(!Number.isFinite(value.getTime()))throw Error('J1_INVALID_DATE');
        return {t:'date',v:value.toISOString()};
      }
      if(value instanceof ArrayBuffer||ArrayBuffer.isView(value)){
        const a=value instanceof ArrayBuffer?new Uint8Array(value):
          new Uint8Array(value.buffer,value.byteOffset,value.byteLength);
        let raw='';for(const x of a)raw+=String.fromCharCode(x);
        return {t:'bytes',ctor:value.constructor.name,v:btoa(raw)};
      }
      if(value instanceof Blob){
        const raw=new Uint8Array(await value.arrayBuffer());
        let binary='';for(const x of raw)binary+=String.fromCharCode(x);
        return {t:'blob',mime:value.type,v:btoa(binary)};
      }
      if(Array.isArray(value))return {t:'array',v:await Promise.all(
        value.map(encode))};
      if(Object.getPrototypeOf(value)===Object.prototype){
        const v={};for(const k of Object.keys(value).sort())v[k]=await encode(value[k]);
        return {t:'object',v};
      }
      throw Error('J1_UNSUPPORTED_STRUCTURED_CLONE_TYPE');
    }
    if(typeof indexedDB.databases!=='function')
      throw Error('J1_INDEXEDDB_INVENTORY_UNSUPPORTED');
    const discovered=(await indexedDB.databases()).map(x=>x.name);
    const expected=names.slice().sort();
    const actual=discovered.filter(x=>x==='amina'||
      /^amina_vault_v1_(native_|device_)/.test(x)).sort();
    if(JSON.stringify(actual)!==JSON.stringify(expected))
      throw Error('J1_LEGACY_INVENTORY_MISMATCH');
    const databases=[];
    for(const name of expected){
      const db=await request(indexedDB.open(name));
      try{
        const stores=[];
        for(const storeName of [...db.objectStoreNames].sort()){
          const tx=db.transaction(storeName,'readonly');
          const store=tx.objectStore(storeName);
          const indexes=[...store.indexNames].sort().map(indexName=>{
            const i=store.index(indexName);
            return {name:indexName,keyPath:i.keyPath,unique:i.unique,
              multiEntry:i.multiEntry};
          });
          // Fetch keys/values in the same IndexedDB key order while the
          // transaction is active. Perform async Blob serialization AFTER
          // both requests finish (never await in a cursor callback).
          const [keys,values]=await Promise.all([
            request(store.getAllKeys()),request(store.getAll())
          ]);
          if(keys.length!==values.length)throw Error('J1_KEY_VALUE_COUNT_MISMATCH');
          const records=[];
          for(let k=0;k<keys.length;k++)records.push({
            key:await encode(keys[k]),value:await encode(values[k])
          });
          stores.push({name:storeName,keyPath:store.keyPath,
            autoIncrement:store.autoIncrement,indexes,records});
        }
        databases.push({name,version:db.version,stores});
      }finally{db.close();}
    }
    const payload={version:1,kind:'iamina-d1-j1-logical-synthetic',databases};
    const serial=JSON.stringify(payload);
    const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(serial));
    const sha256=Array.from(new Uint8Array(hash)).map(x=>x.toString(16).padStart(2,'0')).join('');
    return {payload,sha256};
  },selectedNames);
}
async function restore(page,archive,options={}){
  return invoke(page,async ({archive,options})=>{
    const sha=async x=>{
      const buf=await crypto.subtle.digest('SHA-256',
        new TextEncoder().encode(JSON.stringify(x)));
      return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,'0')).join('');
    };
    const request=req=>new Promise((resolve,reject)=>{
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
    });
    const decode=o=>{
      switch(o.t){
        case 'null':return null;
        case 'undefined':return undefined;
        case 'string':case 'boolean':case 'number':return o.v;
        case 'bigint':return BigInt(o.v);
        case 'date':return new Date(o.v);
        case 'array':return o.v.map(decode);
        case 'object':return Object.fromEntries(
          Object.entries(o.v).map(([k,v])=>[k,decode(v)]));
        case 'bytes':{
          const raw=atob(o.v);
          const arr=Uint8Array.from(raw,c=>c.charCodeAt(0));
          if(o.ctor==='ArrayBuffer')return arr.buffer;
          const ctor=globalThis[o.ctor];
          if(typeof ctor!=='function'||!ArrayBuffer.isView(
            new ctor(arr.buffer)))throw Error('J1_UNKNOWN_TYPED_ARRAY');
          return new ctor(arr.buffer);
        }
        case 'blob':{
          const raw=atob(o.v);
          return new Blob([Uint8Array.from(raw,c=>c.charCodeAt(0))],
            {type:o.mime});
        }
        default:throw Error('J1_UNKNOWN_TYPE');
      }
    };
    if(archive.sha256!==await sha(archive.payload))
      throw Error('J1_ARCHIVE_SHA256_MISMATCH');
    const databases=archive.payload.databases;
    if(archive.payload.kind!=='iamina-d1-j1-logical-synthetic'||
       archive.payload.version!==1||!Array.isArray(databases))
      throw Error('J1_ARCHIVE_FORMAT_UNTRUSTED');
    if(typeof indexedDB.databases!=='function')
      throw Error('J1_INDEXEDDB_INVENTORY_UNSUPPORTED');
    const present=(await indexedDB.databases()).map(x=>x.name);
    if(databases.some(x=>present.includes(x.name)))
      throw Error('J1_RESTORE_TARGET_NOT_EMPTY');
    for(const saved of databases){
      const req=indexedDB.open(saved.name,saved.version);
      req.onupgradeneeded=()=>{
        for(const s of saved.stores){
          const opts={autoIncrement:s.autoIncrement};
          if(s.keyPath!==null)opts.keyPath=s.keyPath;
          const store=req.result.createObjectStore(s.name,opts);
          for(const i of s.indexes)
            store.createIndex(i.name,i.keyPath,
              {unique:i.unique,multiEntry:i.multiEntry});
        }
      };
      const db=await request(req);
      try{
        for(const savedStore of saved.stores){
          // Each object store is restored atomically in a single transaction.
          // Multi-database rollback requires a separate verified protocol.
          const tx=db.transaction(savedStore.name,'readwrite');
          const store=tx.objectStore(savedStore.name);
          for(const rec of savedStore.records){
            const v=decode(rec.value),key=decode(rec.key);
            if(savedStore.keyPath===null)store.put(v,key);
            else store.put(v);
          }
          await new Promise((resolve,reject)=>{
            tx.oncomplete=resolve;
            tx.onerror=()=>reject(tx.error);
            tx.onabort=()=>reject(tx.error||Error('J1_TX_ABORT'));
          });
        }
      }finally{db.close();}
      if(options.simulateAbortAfterDatabase===databases.indexOf(saved)+1){
        throw Error('J1_SIMULATED_POWER_LOSS_STAGED_PARTIAL');
      }
    }
    return true;
  },{archive,options});
}
async function fixture(page){
  return invoke(page,async names=>{
    const request=req=>new Promise((resolve,reject)=>{
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
    });
    for(const [i,name] of names.entries()){
      const req=indexedDB.open(name,2);
      req.onupgradeneeded=()=>{
        if(i===0)req.result.createObjectStore('legacy');
        else if(i===1){
          const store=req.result.createObjectStore('profiles',{keyPath:'id'});
          store.createIndex('by_kind','kind',{unique:false});
        }else req.result.createObjectStore('clinical');
      };
      const db=await request(req);
      try{
        const storeName=i===0?'legacy':i===1?'profiles':'clinical';
        const tx=db.transaction(storeName,'readwrite'),s=tx.objectStore(storeName);
        if(i===0)s.put({note:'SYNTHETIC_UNOWNED_DO_NOT_ASSIGN',
          when:new Date('2026-11-14T00:00:00Z')},'legacy');
        if(i===1)s.put({id:734,kind:'type2',
          payload:new Uint8Array([0,1,2,128,255]).buffer,
          record:'D1_J1_SYNTHETIC_NATIVE_734'});
        if(i===2)s.put(new Uint8Array([10,20,128,250]),
          'D1_J1_SYNTHETIC_NATIVE_812');
        await new Promise((resolve,reject)=>{
          tx.oncomplete=resolve;
          tx.onabort=()=>reject(tx.error);tx.onerror=()=>reject(tx.error);
        });
      }finally{db.close();}
    }
    return true;
  },names);
}
if(require.main===module){
(async()=>{
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const source=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  const a=await source.newPage();await a.goto(origin);
  await fixture(a);
  const archive=await inventoryAndBackup(a);
  proof.manifestSha256=archive.sha256;
  proof.sourceStores=archive.payload.databases.flatMap(db=>
    db.stores.map(s=>({name:db.name,store:s.name,records:s.records.length})));
  check(proof.sourceStores.length===3,'fixture must include three database schemas');
  const untouched=await inventoryAndBackup(a);
  proof.sourceUnchangedAfterBackup=untouched.sha256===archive.sha256;
  check(proof.sourceUnchangedAfterBackup,'backup changed source');

  const fresh=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  const b=await fresh.newPage();await b.goto(origin);
  await restore(b,archive);
  const recovered=await inventoryAndBackup(b);
  proof.independentRestoreSha256Matches=recovered.sha256===archive.sha256;
  check(proof.independentRestoreSha256Matches,
    'fresh browser profile logical bytes/schema mismatch');
  let refused=false;
  try{await restore(b,archive);}
  catch(e){refused=String(e).includes('J1_RESTORE_TARGET_NOT_EMPTY');}
  proof.overwriteDenied=refused;
  check(refused,'restore overwrote existing target');
  const corrupted=JSON.parse(JSON.stringify(archive));
  corrupted.payload.databases[0].stores[0].records[0].value.v.note.v='TAMPERED';
  const untouchedCtx=await browser.newContext({locale:'en-US'});
  const c=await untouchedCtx.newPage();await c.goto(origin);
  refused=false;
  try{await restore(c,corrupted);}
  catch(e){refused=String(e).includes('J1_ARCHIVE_SHA256_MISMATCH');}
  proof.tamperRejectedBeforeWrite=refused;
  check(refused,'tampered manifest accepted');
  proof.tamperTargetEmpty=(await c.evaluate(async()=>
    (await indexedDB.databases()).length))===0;
  check(proof.tamperTargetEmpty,'tampered manifest created database');
  proof.sourcePreservedAfterRestore=(await inventoryAndBackup(a)).sha256===
    archive.sha256;
  check(proof.sourcePreservedAfterRestore,'restore mutated original archive source');
  await Promise.all([source.close(),fresh.close(),untouchedCtx.close()]);
  proof.result='PASS_SYNTHETIC_LOGICAL_RESTORE_ONLY';
 }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,1800);throw e;}
 finally{
  fs.writeFileSync(dir+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J1_BACKUP_RESTORE='+JSON.stringify(proof));
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});
}
module.exports={inventoryAndBackup,restore,fixture,names};