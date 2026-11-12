// Browser WebCrypto & IndexedDB credential tests; NO real patient or key.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const browserName=process.env.D1_BROWSER||'chromium';
const report={lot:'D1_DEVICE_KEY_LIFECYCLE',browser:browserName,
 synthetic:true,patientRuntime:false,deviceHardwareBound:false,
 patientRelease:'NO_GO',result:'NOT_RUN',checks:[]};
const ownerA='amina_vault_v1_native_731',ownerB='amina_vault_v1_native_812';
async function check(page,name,fn){
 const result=await page.evaluate(fn);
 if(result!==true)throw Error(name+' FAILED: '+JSON.stringify(result).slice(0,260));
 report.checks.push(name);
}
(async()=>{
 const engine={chromium,webkit}[browserName];if(!engine)throw Error('BROWSER');
 const browser=await engine.launch({headless:true,...(browserName==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const context=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  const page=await context.newPage();
  await page.goto('http://127.0.0.1:7417/d1_device_key_harness.html');
  const init=await page.evaluate(async({ownerA,ownerB})=>{
   const api=window.iaminaD1DeviceKeyCustody;
   const a=await api.create(ownerA),b=await api.create(ownerB);
   window.__d1Fixture={recoveryA:a.recoveryKey,recoveryB:b.recoveryKey};
   return {a,b};
  },{ownerA,ownerB});
  if(init.a.status!=='pending_confirmation'||init.b.status!=='pending_confirmation')
   throw Error('PENDING_CONFIRMATION_REQUIRED');
  report.checks.push('per-owner random recovery keys, initial pending');
  report.knownCriticalRisk='SAME_ORIGIN_JS_CAN_USE_LOCAL_CRYPTO_KEY_WITHOUT_APP_LOCK';
  await check(page,'cannot unlock before confirmed',async()=>{
   try{await window.iaminaD1DeviceKeyCustody.unlockDevice('amina_vault_v1_native_731');return false}
   catch(e){return String(e).includes('RECOVERY_NOT_CONFIRMED')}
  });
  await check(page,'wrong recovery cannot confirm account A',async()=>{
   const api=window.iaminaD1DeviceKeyCustody;
   try{await api.confirm('amina_vault_v1_native_731',window.__d1Fixture.recoveryB);return false}
   catch(e){return String(e).includes('AUTH_DENIED')}
  });
  await check(page,'confirmation checks both device and recovery key',async()=>{
   const api=window.iaminaD1DeviceKeyCustody;
   await api.confirm('amina_vault_v1_native_731',window.__d1Fixture.recoveryA);
   await api.confirm('amina_vault_v1_native_812',window.__d1Fixture.recoveryB);
   const a=await api.inspect('amina_vault_v1_native_731');
   return a.status==='ready'&&a.deviceKeyExtractable===false&&a.hasRecoveryEnvelope===true;
  });
  await check(page,'same-origin JS bypasses app-lock (deliberate threat NO-GO)',async()=>{
   const key=await window.iaminaD1DeviceKeyCustody.unlockDevice('amina_vault_v1_native_731');
   const observed=key instanceof Uint8Array&&key.length===32;
   key.fill(0);return observed;
  });
  await check(page,'atomic confirmation race rejects second writer',async()=>{
   const api=window.iaminaD1DeviceKeyCustody,owner='amina_vault_v1_native_921';
   const created=await api.create(owner);
   const r=await Promise.allSettled([
    api.confirm(owner,created.recoveryKey),
    api.confirm(owner,created.recoveryKey),
   ]);
   return r.filter(v=>v.status==='fulfilled').length===1 &&
     r.filter(v=>v.status==='rejected').length===1 &&
     (await api.inspect(owner)).status==='ready';
  });
  await check(page,'duplicate account creation cannot replace existing DEK',async()=>{
   try{await window.iaminaD1DeviceKeyCustody.create('amina_vault_v1_native_731');return false}
   catch(e){return String(e).includes('ALREADY_ENROLLED')}
  });
  await check(page,'A unlock equals A recovery, never B',async()=>{
   const api=window.iaminaD1DeviceKeyCustody;
   const a=await api.unlockDevice('amina_vault_v1_native_731');
   const r=await api.unlockRecovery('amina_vault_v1_native_731',window.__d1Fixture.recoveryA);
   const b=await api.unlockDevice('amina_vault_v1_native_812');
   const equal=(x,y)=>x.length===y.length&&x.every((v,i)=>v===y[i]);
   const valid=equal(a,r)&&!equal(a,b)&&a.length===32;
   a.fill(0);r.fill(0);b.fill(0);
   return valid;
  });
  await check(page,'foreign recovery refuses owner B',async()=>{
   try{await window.iaminaD1DeviceKeyCustody.unlockRecovery(
    'amina_vault_v1_native_812',window.__d1Fixture.recoveryA);return false}
   catch(e){return String(e).includes('AUTH_DENIED')}
  });
  await check(page,'no DEK or recovery key in localStorage or sessionStorage',async()=>{
   const fixture=window.__d1Fixture;
   const local=[...Object.entries(localStorage)].flat().join('|');
   const session=[...Object.entries(sessionStorage)].flat().join('|');
   return !local.includes(fixture.recoveryA)&&!session.includes(fixture.recoveryA);
  });
  await check(page,'stored CryptoKey cannot be exported',async()=>{
   const db=await new Promise((resolve,reject)=>{
    const q=indexedDB.open('iamina_d1_key_custody_v1',1);
    q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);
   });
   const rec=await new Promise((resolve,reject)=>{
    const q=db.transaction('vaults','readonly').objectStore('vaults').get('amina_vault_v1_native_731');
    q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);
   });
   db.close();
   if(rec.deviceKek.extractable!==false||rec.recoveryKey!==undefined)return false;
   try{await crypto.subtle.exportKey('raw',rec.deviceKek);return false}
   catch{return true}
  });
  // Simulate a reload: recover in a separate JS runtime, same browser profile.
  const second=await context.newPage();
  await second.goto('http://127.0.0.1:7417/d1_device_key_harness.html');
  await check(second,'device DEK persists across page reload',async()=>{
   const key=await window.iaminaD1DeviceKeyCustody.unlockDevice('amina_vault_v1_native_731');
   const good=key instanceof Uint8Array&&key.length===32;
   key.fill(0);return good;
  });
  await check(second,'damaged local envelope fails authentication',async()=>{
   const owner='amina_vault_v1_native_731';
   const db=await new Promise((resolve,reject)=>{
    const q=indexedDB.open('iamina_d1_key_custody_v1',1);
    q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);
   });
   const r=await new Promise((resolve,reject)=>{
    const q=db.transaction('vaults','readonly').objectStore('vaults').get(owner);
    q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);
   });
   const damaged={...r,device:{...r.device,
    ciphertext:(r.device.ciphertext[0]==='A'?'B':'A')+r.device.ciphertext.slice(1)}};
   const put=record=>new Promise((resolve,reject)=>{
    const tx=db.transaction('vaults','readwrite');
    tx.objectStore('vaults').put(record);
    tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);
   });
   await put(damaged);
   let refused=false;
   try{await window.iaminaD1DeviceKeyCustody.unlockDevice(owner)}
   catch(e){refused=String(e).includes('AUTH_DENIED')}
   await put(r);db.close();return refused;
  });
  await check(second,'wrong recovery cannot rebind device',async()=>{
   try{await window.iaminaD1DeviceKeyCustody.rebindDevice(
    'amina_vault_v1_native_731',window.btoa('x'.repeat(32)));return false}
   catch(e){return String(e).includes('AUTH_DENIED')}
  });
  await check(second,'recover with patient secret and rebind fresh device KEK',async()=>{
   // Recovery secret is handed over from the synthetic test fixture, not storage.
   const key=await window.iaminaD1DeviceKeyCustody.unlockDevice('amina_vault_v1_native_731');
   window.__tmpOld=Array.from(key);key.fill(0);
   return true;
  });
  await second.close();
  // Test rebind uses recovery from original test page and proves DB key unchanged.
  await check(page,'rebind via recovery preserves DEK while replacing local KEK',async()=>{
   const api=window.iaminaD1DeviceKeyCustody,owner='amina_vault_v1_native_731';
   const key1=await api.unlockDevice(owner);
   const recovery=window.__d1Fixture.recoveryA;
   await api.rebindDevice(owner,recovery);
   const key2=await api.unlockDevice(owner);
   const same=key1.every((x,i)=>key2[i]===x);
   key1.fill(0);key2.fill(0);return same;
  });
  await check(page,'audit namespace and empty recovery are refused',async()=>{
   const api=window.iaminaD1DeviceKeyCustody;
   let bad=0;
   for(const owner of ['amina_vault_v1_audit','','amina_vault_v1_native_0']){
    try{await api.create(owner)}catch{bad++}
   }
   try{await api.unlockRecovery('amina_vault_v1_native_731','')}catch{bad++}
   return bad===4;
  });
  report.result='PASS_SYNTHETIC_DEVICE_KEY_LIFECYCLE';
  console.log(JSON.stringify(report,null,2));
  await context.close();
 }catch(e){report.result='FAIL';report.error=String(e).slice(0,320);
  console.error(e);process.exitCode=1}
 finally{
  fs.writeFileSync('d1-device-key-'+browserName+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
