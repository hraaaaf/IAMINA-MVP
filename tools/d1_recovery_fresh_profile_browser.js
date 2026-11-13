// D1 synthetic encrypted-profile portability feasibility only.
// Does not install a clinical backup flow or authorize any patient data.
// The fixture explicitly keeps the recovery material OUT of the backup object.
const {chromium} = require('playwright');
const fs = require('fs');

const root = 'http://127.0.0.1:7476/';
const owner = 'amina_vault_v1_native_755';
const storeName = 'iamina_d1_encrypted_vault_v1_' + owner;
const headerName = 'iamina_d1_wrapped_vault_v1_' + owner;
const marker = 'D1_SYNTHETIC_FRESH_PROFILE_RECOVERY_755';
const out = 'd1-fresh-profile-recovery-proof';

async function expectFixture(page, expected, timeout = 60000) {
  await page.waitForFunction(value => {
    const s = document.body?.textContent || '';
    return s.includes('"scope":"synthetic encrypted IndexedDB export/restore, separate browser profiles"') &&
      (s.includes('"result":"' + value + '"') || s.includes('"result":"FAIL"'));
  }, expected, {timeout});
  const text = await page.locator('body').innerText();
  const obj = JSON.parse(text.slice(text.indexOf('{"scope"')));
  if (obj.result !== expected) throw Error('D1 fixture rejected: ' + JSON.stringify(obj));
  return obj;
}

(async () => {
  fs.mkdirSync(out, {recursive:true});
  const proof = {scope:'two independent Chromium profiles, encrypted-only synthetic bundle',
    head:process.env.D1_CANDIDATE_SHA||'unknown',
    result:'NOT_RUN',clinicalGo:false,backupMadeOfEncryptedStoreOnly:false,
    codeExcludedFromBundle:false,plainMarkerAbsentFromBundle:false,
    freshTargetInitialStorageEmpty:false,wrongRecoveryRejected:false,
    originalDataRecovered:false,ownerScoped:false,sourceAndTargetIndependent:false};
  const browser = await chromium.launch({headless:true});
  try {
    const source = await browser.newContext({locale:'en-US',serviceWorkers:'block'});
    const src = await source.newPage();
    const jsErrors = [];
    src.on('pageerror', err => jsErrors.push('source:'+String(err.stack || err).slice(0,1300)));
    await src.goto(root+'?phase=source',{waitUntil:'domcontentloaded'});
    try { await expectFixture(src,'SOURCE_READY',35000); }
    catch (err) {
      const diagnostic = await src.evaluate(async () => ({
        body:(document.body?.innerText||'').slice(0,1600),
        html:document.documentElement.outerHTML.slice(0,2200),
        scripts:[...document.scripts].map(s=>s.src.slice(-120)),
        encryptedDbNames:typeof indexedDB.databases==='function' ?
          (await indexedDB.databases()).map(d=>d.name) : [],
        cryptoLoaded:!!globalThis.IaminaD1CryptoCandidate,
      })).catch(e=>({diagnosticFailure:String(e)}));
      throw Error('Synthetic source initialization failed: '+
        JSON.stringify({diagnostic,jsErrors}).slice(0,2500)+'; '+String(err));
    }

    // Browser IndexedDB records are already encrypted by sqlite3mc.
    // Export the EXACT object-store data and structure, not arbitrary stores,
    // not old 'amina', and never an application-level plaintext SQL export.
    const bundle = await src.evaluate(async ({storeName,headerName}) => {
      const header = localStorage.getItem(headerName);
      if (!header) throw Error('sealed owner-bound key envelope not found');
      const obj = JSON.parse(header);
      if (obj.state !== 'sealed') throw Error('ciphertext not fully sealed');
      if (obj.owner !== 'amina_vault_v1_native_755') throw Error('wrong owner');
      if (typeof indexedDB.databases !== 'function') throw Error('DB inventory unsupported');
      const listed = await indexedDB.databases();
      if (!listed.some(d=>d.name===storeName)) throw Error('encrypted store not found');
      const req=indexedDB.open(storeName);
      const db=await new Promise((res,rej)=>{
        req.onsuccess=()=>res(req.result); req.onerror=()=>rej(req.error);
      });
      async function pack(value) {
        if(value instanceof ArrayBuffer)
          return {kind:'ab',data:Array.from(new Uint8Array(value))};
        if(ArrayBuffer.isView(value))
          return {kind:'view',data:Array.from(
            new Uint8Array(value.buffer,value.byteOffset,value.byteLength))};
        if(value instanceof Blob)
          return {kind:'blob',mime:value.type,
            data:Array.from(new Uint8Array(await value.arrayBuffer()))};
        if(value instanceof Date) return {kind:'date',data:value.toISOString()};
        if(Array.isArray(value)) return {kind:'arr',data:await Promise.all(value.map(pack))};
        if(value&&typeof value==='object') {
          const entries=[];for(const [k,v] of Object.entries(value))
            entries.push([k,await pack(v)]);
          return {kind:'obj',data:entries};
        }
        return {kind:'raw',data:value};
      }
      try {
        const stores=[];
        for(const store of Array.from(db.objectStoreNames)) {
          const tx=db.transaction(store,'readonly');
          const os=tx.objectStore(store);
          const values=await new Promise((res,rej)=>{
            const q=os.getAll();q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);
          });
          const keys=await new Promise((res,rej)=>{
            const q=os.getAllKeys();q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);
          });
          const records=[];for(let i=0;i<keys.length;i++)
            records.push({key:await pack(keys[i]),value:await pack(values[i])});
          stores.push({name:store,keyPath:os.keyPath,autoIncrement:os.autoIncrement,records});
        }
        return {format:'D1_CI_SYNTHETIC_ENCRYPTED_IDB_V1',
          owner:'amina_vault_v1_native_755',storeName,header,
          db:{version:db.version,stores}};
      } finally {db.close();}
    },{storeName,headerName});
    proof.ownerScoped = bundle.owner===owner && JSON.parse(bundle.header).owner===owner;
    const recovery = await src.evaluate(()=>sessionStorage.getItem('d1_fixture_recovery'));
    if(!recovery || recovery.length<40)throw Error('source recovery fixture not available');
    const backupBytes=JSON.stringify(bundle);
    proof.bundleByteLength=Buffer.byteLength(backupBytes);
    proof.codeExcludedFromBundle=!backupBytes.includes(recovery);
    proof.plainMarkerAbsentFromBundle=!backupBytes.includes(marker) &&
      !backupBytes.includes('SQLite format 3') && !backupBytes.includes('log_entries');
    proof.backupMadeOfEncryptedStoreOnly=
      bundle.storeName===storeName && bundle.db.stores.length>0 &&
      bundle.header.length>100 && bundle.owner===owner;
    if(!proof.codeExcludedFromBundle || !proof.plainMarkerAbsentFromBundle ||
      !proof.backupMadeOfEncryptedStoreOnly) throw Error('unsafe synthetic backup payload');

    const target = await browser.newContext({locale:'en-US',serviceWorkers:'block'});
    proof.sourceAndTargetIndependent = source!==target;
    const dst = await target.newPage();
    dst.on('pageerror', err=>jsErrors.push('target:'+String(err).slice(0,600)));
    await dst.goto(root+'?phase=target',{waitUntil:'domcontentloaded'});
    await dst.waitForSelector('#d1-fresh-profile-restore-trigger',{state:'attached',timeout:45000});
    proof.freshTargetInitialStorageEmpty=await dst.evaluate(async ({storeName,headerName}) => {
      const names=await indexedDB.databases();
      return !localStorage.getItem(headerName) && !names.some(d=>d.name===storeName);
    },{storeName,headerName});
    if(!proof.freshTargetInitialStorageEmpty)throw Error('target browser not fresh');

    await dst.evaluate(async ({bundle,recovery,storeName,headerName})=>{
      if(bundle.storeName!==storeName || bundle.owner!=='amina_vault_v1_native_755' ||
        JSON.parse(bundle.header).owner!=='amina_vault_v1_native_755')
        throw Error('owner mismatch before restore');
      const existing=await indexedDB.databases();
      if(existing.some(d=>d.name===storeName)||localStorage.getItem(headerName))
        throw Error('restore collision (no overwrites allowed)');
      function unpack(value) {
        switch(value.kind) {
          case 'ab': return Uint8Array.from(value.data).buffer;
          case 'view': return Uint8Array.from(value.data);
          case 'blob': return new Blob([Uint8Array.from(value.data)],{type:value.mime});
          case 'date':return new Date(value.data);
          case 'arr':return value.data.map(unpack);
          case 'obj':return Object.fromEntries(value.data.map(([k,v])=>[k,unpack(v)]));
          default:return value.data;
        }
      }
      const request=indexedDB.open(storeName,bundle.db.version);
      request.onupgradeneeded=()=>{
        const db=request.result;
        for(const s of bundle.db.stores) {
          const options={autoIncrement:s.autoIncrement};
          if(s.keyPath!=null)options.keyPath=s.keyPath;
          db.createObjectStore(s.name,options);
        }
      };
      const db=await new Promise((res,rej)=>{
        request.onsuccess=()=>res(request.result);
        request.onerror=()=>rej(request.error);
      });
      try {
        for(const s of bundle.db.stores){
          if(!s.records.length)continue;
          const tx=db.transaction(s.name,'readwrite');
          const os=tx.objectStore(s.name);
          for(const rec of s.records){
            const v=unpack(rec.value);
            if(s.keyPath!=null) os.put(v);
            else os.put(v,unpack(rec.key));
          }
          await new Promise((res,rej)=>{
            tx.oncomplete=res;tx.onerror=()=>rej(tx.error);tx.onabort=()=>rej(tx.error);
          });
        }
      } finally {db.close();}
      localStorage.setItem(headerName,bundle.header);
      // Synthetic fixture handoff ONLY; no real key in IDB backup/metadata.
      sessionStorage.setItem('d1_fixture_recovery',recovery);
    },{bundle,recovery,storeName,headerName});
    await dst.locator('#d1-fresh-profile-restore-trigger').evaluate(e=>e.click());
    const recovered=await expectFixture(dst,'PASS',45000);
    proof.wrongRecoveryRejected=recovered.wrongRecoveryRejected===true;
    proof.originalDataRecovered=recovered.restoredOriginalRecord===true;
    proof.jsErrors=jsErrors;
    if(!proof.wrongRecoveryRejected||!proof.originalDataRecovered||jsErrors.length)
      throw Error('synthetic fresh profile restore invariant failure');
    proof.result='PASS';
    await source.close();await target.close();
  } catch(err){
    proof.result='FAIL';proof.error=String(err.stack||err).slice(0,2300);
    throw err;
  } finally {
    fs.writeFileSync(out+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_FRESH_PROFILE_RECOVERY='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>{process.exitCode=1;});
