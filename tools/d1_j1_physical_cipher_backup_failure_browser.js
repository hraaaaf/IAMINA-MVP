// D1 J1: physical encrypted IndexedDB records of an actual SQLite3MC vault.
// Browser fixtures ONLY, never a clinical backup or migration implementation.
// Captures exact structured-clone records & sealed owner envelope; never
// includes a recovery code. SHA-256 detects accidental changes, NOT forgery.
'use strict';
const {chromium}=require('playwright');
const {createHash}=require('node:crypto');
const fs=require('fs');
const root='http://127.0.0.1:7476/';
const owner='amina_vault_v1_native_755';
const storeName='iamina_d1_encrypted_vault_v1_'+owner;
const headerName='iamina_d1_wrapped_vault_v1_'+owner;
const marker='D1_SYNTHETIC_FRESH_PROFILE_RECOVERY_755';
const folder='d1-j1-physical-cipher-crash-proof';
const sha256=s=>createHash('sha256').update(s).digest('hex');
const proof={
 head:process.env.D1_CANDIDATE_SHA||'unknown',clinicalGo:false,
 mode:'encrypted SQLite3MC IndexedDB structured records, not live WAL snapshot',
 sourceSha256:null,archiveOnlyCiphertext:false,
 result:'NOT_RUN',checks:{}
};
function check(ok,label){if(!ok)throw Error('D1_J1_PHYSICAL: '+label);}
async function report(page,expected='SOURCE_READY'){
 await page.waitForFunction(expected=>{
  const text=document.body?.textContent||'';
  return text.includes('"scope":"synthetic encrypted IndexedDB export/restore, separate browser profiles"') &&
    (text.includes('"result":"'+expected+'"')||text.includes('"result":"FAIL"'));
 },expected,{timeout:50000});
 const t=await page.locator('body').innerText();
 const obj=JSON.parse(t.slice(t.indexOf('{"scope"')));
 check(obj.result===expected,'fixture_'+obj.result+'_expected_'+expected);
 return obj;
}
const meta={storeName,headerName,owner};
async function exportArchive(page){
 return page.evaluate(async({storeName,headerName,owner})=>{
  const header=localStorage.getItem(headerName);
  if(!header)throw Error('D1_CIPHER_ENVELOPE_MISSING');
  const parsed=JSON.parse(header);
  if(parsed.owner!==owner||parsed.state!=='sealed')
    throw Error('D1_CIPHER_ENVELOPE_INVALID');
  if(typeof indexedDB.databases!=='function')
    throw Error('D1_IDB_INVENTORY_UNSUPPORTED');
  const existing=await indexedDB.databases();
  if(!existing.some(x=>x.name===storeName))
    throw Error('D1_ENCRYPTED_PHYSICAL_STORE_MISSING');
  const req=indexedDB.open(storeName);
  const db=await new Promise((res,rej)=>{
   req.onsuccess=()=>res(req.result);req.onerror=()=>rej(req.error);
  });
  async function pack(v){
   if(v===null)return {t:'null'};
   if(v===undefined)return {t:'undef'};
   if(v instanceof ArrayBuffer)return {t:'ab',v:Array.from(new Uint8Array(v))};
   if(ArrayBuffer.isView(v))return {t:'view',v:Array.from(
     new Uint8Array(v.buffer,v.byteOffset,v.byteLength))};
   if(v instanceof Blob)return {t:'blob',mime:v.type,v:Array.from(
     new Uint8Array(await v.arrayBuffer()))};
   if(v instanceof Date)return {t:'date',v:v.toISOString()};
   if(Array.isArray(v))return {t:'arr',v:await Promise.all(v.map(pack))};
   if(typeof v==='object'){
    if(Object.getPrototypeOf(v)!==Object.prototype)
      throw Error('D1_UNKNOWN_ARCHIVE_OBJECT_TYPE');
    const out=[];for(const [k,value] of Object.entries(v))
      out.push([k,await pack(value)]);
    return {t:'obj',v:out};
   }
   if(typeof v==='number'&&!Number.isFinite(v))throw Error('D1_NON_FINITE');
   if(typeof v==='bigint')return {t:'bigint',v:String(v)};
   return {t:typeof v,v};
  }
  try{
   const stores=[];
   for(const name of [...db.objectStoreNames]){
    const tx=db.transaction(name,'readonly');
    const os=tx.objectStore(name);
    const [values,keys]=await Promise.all([
     new Promise((res,rej)=>{const r=os.getAll();
      r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);}),
     new Promise((res,rej)=>{const r=os.getAllKeys();
      r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);})
    ]);
    if(values.length!==keys.length)
      throw Error('D1_PHYSICAL_KEY_VALUE_MISMATCH');
    const records=[];
    for(let i=0;i<keys.length;i++)
      records.push({key:await pack(keys[i]),value:await pack(values[i])});
    const indexes=[...os.indexNames].map(indexName=>{
     const ix=os.index(indexName);
     return {name:indexName,keyPath:ix.keyPath,unique:ix.unique,
       multiEntry:ix.multiEntry};
    });
    stores.push({name,keyPath:os.keyPath,autoIncrement:os.autoIncrement,
      indexes,records});
   }
   return {format:'D1_SYNTHETIC_CIPHER_IDB_PHYSICAL_V2',owner,
     storeName,header,db:{version:db.version,stores}};
  }finally{db.close();}
 },meta);
}
async function importArchive(page,archive,manifestSha256,{abortAfterStore=false}={}){
 return page.evaluate(async({archive,manifestSha256,abortAfterStore,
  storeName,headerName,owner})=>{
  // In the CI-only importer, SHA verification is performed INSIDE the browser
  // before ANY storage modification; it is not a signer/authenticator.
  const digest=await crypto.subtle.digest('SHA-256',
    new TextEncoder().encode(JSON.stringify(archive)));
  const hex=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(hex!==manifestSha256)throw Error('D1_ARCHIVE_SHA256_MISMATCH');
  if(archive.format!=='D1_SYNTHETIC_CIPHER_IDB_PHYSICAL_V2'||
    archive.owner!==owner||archive.storeName!==storeName||
    JSON.parse(archive.header).owner!==owner||
    JSON.parse(archive.header).state!=='sealed'||
    !Array.isArray(archive.db?.stores)||!archive.db.stores.length)
    throw Error('D1_ARCHIVE_OWNER_OR_FORMAT_INVALID');
  if(typeof indexedDB.databases!=='function')
    throw Error('D1_IDB_INVENTORY_UNSUPPORTED');
  if(localStorage.getItem(headerName)||
    (await indexedDB.databases()).some(x=>x.name===storeName))
    throw Error('D1_RESTORE_TARGET_NOT_EMPTY');

  const unpack=v=>{
   switch(v.t){
    case 'null':return null;
    case 'undef':return undefined;
    case 'ab':return Uint8Array.from(v.v).buffer;
    case 'view':return Uint8Array.from(v.v);
    case 'blob':return new Blob([Uint8Array.from(v.v)],{type:v.mime});
    case 'date':return new Date(v.v);
    case 'arr':return v.v.map(unpack);
    case 'obj':return Object.fromEntries(v.v.map(([k,value])=>[k,unpack(value)]));
    case 'bigint':return BigInt(v.v);
    case 'string':case 'number':case 'boolean':return v.v;
    default:throw Error('D1_UNSUPPORTED_ARCHIVE_TYPE');
   }
  };
  const req=indexedDB.open(storeName,archive.db.version);
  req.onupgradeneeded=()=>{
   for(const s of archive.db.stores){
    const options={autoIncrement:s.autoIncrement};
    if(s.keyPath!==null)options.keyPath=s.keyPath;
    const os=req.result.createObjectStore(s.name,options);
    for(const idx of s.indexes)
      os.createIndex(idx.name,idx.keyPath,
        {unique:idx.unique,multiEntry:idx.multiEntry});
   }
  };
  const db=await new Promise((res,rej)=>{
   req.onsuccess=()=>res(req.result);req.onerror=()=>rej(req.error);
  });
  try{
   for(const s of archive.db.stores){
    const tx=db.transaction(s.name,'readwrite');
    const os=tx.objectStore(s.name);
    for(const r of s.records){
     if(s.keyPath!==null)os.put(unpack(r.value));
     else os.put(unpack(r.value),unpack(r.key));
    }
    await new Promise((res,rej)=>{
     tx.oncomplete=res;tx.onerror=()=>rej(tx.error);
     tx.onabort=()=>rej(tx.error);
    });
    if(abortAfterStore){
      // Simulate hard crash BEFORE committing localStorage sealed envelope.
      // Partial encrypted IDB stays present, clearly quarantined.
      throw Error('D1_SYNTHETIC_INTERRUPTED_BEFORE_ENVELOPE_COMMIT');
    }
   }
  }finally{db.close();}
  localStorage.setItem(headerName,archive.header);
  return {committed:true};
 },{archive,manifestSha256,abortAfterStore,...meta});
}
(async()=>{
 fs.mkdirSync(folder,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const contexts=[];
 async function context(phase){
  const ctx=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  contexts.push(ctx);
  const page=await ctx.newPage();
  await page.goto(root+'?phase='+phase,{waitUntil:'domcontentloaded'});
  if(phase==='target'){
   await page.waitForSelector('#d1-fresh-profile-restore-trigger',
     {state:'attached',timeout:40000});
  }
  return page;
 }
 try{
  const src=await context('source');
  await report(src);
  const bundle=await exportArchive(src);
  const serialized=JSON.stringify(bundle);
  const manifest=sha256(serialized);
  proof.sourceSha256=manifest;
  proof.archiveOnlyCiphertext=serialized.length>10000&&
    !serialized.includes(marker)&&!serialized.includes('SQLite format 3')&&
    !serialized.includes('log_entries');
  check(proof.archiveOnlyCiphertext,'backup_contains_plain_marker_or_schema');
  const recovery=await src.evaluate(()=>sessionStorage.getItem('d1_fixture_recovery'));
  check(typeof recovery==='string'&&recovery.length>40,
    'fixture_recovery_missing');
  check(!serialized.includes(recovery),'recovery_secret_leaked_to_backup');
  proof.checks.recoveryExcludedFromPhysicalArchive=true;

  const corrupt=await context('target');
  const modified=JSON.parse(serialized);
  modified.header+=' ';
  let denied=false;
  try{await importArchive(corrupt,modified,manifest);}
  catch(e){denied=String(e).includes('D1_ARCHIVE_SHA256_MISMATCH');}
  check(denied,'tampered_archive_accepted');
  proof.checks.tamperRejectedBeforeStorage=true;
  const noStore=await corrupt.evaluate(async({storeName,headerName})=>
    !localStorage.getItem(headerName)&&
    !(await indexedDB.databases()).some(x=>x.name===storeName),meta);
  check(noStore,'tamper_created_or_modified_target_storage');
  proof.checks.corruptTargetPreservedEmpty=true;

  const staging=await context('target');
  let crashed=false;
  try{await importArchive(staging,bundle,manifest,{abortAfterStore:true});}
  catch(e){crashed=String(e).includes(
    'D1_SYNTHETIC_INTERRUPTED_BEFORE_ENVELOPE_COMMIT');}
  check(crashed,'interruption_injection_not_observed');
  proof.checks.crashInjectedAfterEncryptedStore=true;
  const state=await staging.evaluate(async({storeName,headerName})=>({
    ciphertextPresent:(await indexedDB.databases()).some(x=>x.name===storeName),
    sealedHeaderPresent:!!localStorage.getItem(headerName)
  }),meta);
  check(state.ciphertextPresent&&!state.sealedHeaderPresent,
    'partial_stage_not_quarantined');
  proof.checks.partialCiphertextQuarantinedWithoutEnvelope=true;
  denied=false;
  try{await importArchive(staging,bundle,manifest);}
  catch(e){denied=String(e).includes('D1_RESTORE_TARGET_NOT_EMPTY');}
  check(denied,'partial_stage_was_overwritten');
  proof.checks.partialStagingOverwriteDenied=true;
  const preserved=await exportArchive(src);
  proof.checks.sourcePhysicalShaUnchangedAfterCrash=
    sha256(JSON.stringify(preserved))===manifest;
  check(proof.checks.sourcePhysicalShaUnchangedAfterCrash,
    'crash_modified_cipher_source');

  const target=await context('target');
  await importArchive(target,bundle,manifest);
  const after=await exportArchive(target);
  proof.checks.byteEquivalentPhysicalRecordsRestored=
    sha256(JSON.stringify(after))===manifest;
  check(proof.checks.byteEquivalentPhysicalRecordsRestored,
    'cipher_object_store_physical_manifest_mismatch');
  denied=false;
  try{await importArchive(target,bundle,manifest);}
  catch(e){denied=String(e).includes('D1_RESTORE_TARGET_NOT_EMPTY');}
  check(denied,'repeat_import_overwrote_target');
  proof.checks.repeatRestoreRejected=true;

  // The recovery code travels OUTSIDE the archive in this test-only path.
  await target.evaluate(recovery=>
    sessionStorage.setItem('d1_fixture_recovery',recovery),recovery);
  await target.locator('#d1-fresh-profile-restore-trigger').evaluate(el=>el.click());
  const result=await report(target,'PASS');
  check(result.wrongRecoveryRejected===true&&
    result.restoredOriginalRecord===true,'actual_sqlite3mc_record_not_recovered');
  proof.checks.actualEncryptedDatabaseRecovered=true;
  proof.checks.wrongRecoveryRejected=true;
  proof.checks.freshCleanProfileRestoresAfterAbortedStaging=true;
  proof.result='PASS_ENCRYPTED_IDB_BYTES_AND_CRASH_QUARANTINE';
 }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2700);throw e;}
 finally{
  fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_J1_PHYSICAL_CIPHER_BACKUP='+JSON.stringify(proof));
  for(const ctx of contexts)await ctx.close().catch(()=>{});
  await browser.close();
 }
})().catch(()=>{process.exitCode=1;});