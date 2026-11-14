// D1-P0 real Service Worker installed offline write (SYNTHETIC).
// An already installed historical PWA cannot be patched while offline.
// This test PROVES that risk and new-vault quarantine without deleting data.
'use strict';
const {chromium}=require('playwright');
const fs=require('fs');
const folder='d1-installed-pwa-offline-proof';
const origin='http://127.0.0.1:7475';
const legacyName='amina_vault_v1_native_999';
const marker='D1_INSTALLED_OFFLINE_SYNTHETIC_999';
const swSource=String.raw`self.addEventListener('message', event => {
  if (event.data?.op !== 'legacy-offline-write') return;
  const port=event.ports?.[0];
  event.waitUntil((async () => {
    const db=await new Promise((resolve,reject) => {
      const req=indexedDB.open('amina_vault_v1_native_999',1);
      req.onupgradeneeded=() => {
        if (!req.result.objectStoreNames.contains('legacy')) {
          req.result.createObjectStore('legacy');
        }
      };
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error);
    });
    try {
      const tx=db.transaction('legacy','readwrite');
      tx.objectStore('legacy').put('D1_INSTALLED_OFFLINE_SYNTHETIC_999',
        'old-pwa-record');
      await new Promise((resolve,reject)=>{
        tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error);
        tx.onerror=()=>reject(tx.error);
      });
    } finally { db.close(); }
    port?.postMessage({saved:true});
  })().catch(e=>{port?.postMessage({saved:false,error:String(e)});}));
});`;
const proof={
  head:process.env.D1_CANDIDATE_SHA||'unknown',
  scope:'old installed Service Worker persists legacy IndexedDB while offline',
  clinicalGo:false,
  legacyWriterPreventable:false,
  result:'NOT_RUN'
};
function check(ok,msg){if(!ok)throw Error('D1 installed PWA: '+msg);}
(async()=>{
  fs.mkdirSync(folder,{recursive:true});
  // Ephemeral CI build assets ONLY, never production service worker files.
  fs.writeFileSync('frontend/build/web/d1-synthetic-installed-legacy-sw.js',swSource);
  fs.writeFileSync('frontend/build/web/d1-synthetic-installed-legacy.html',
    '<!doctype html><meta charset="utf-8"><title>Synthetic installed PWA</title>');
  const browser=await chromium.launch({headless:true});
  try {
    const ctx=await browser.newContext({
      serviceWorkers:'allow',locale:'en-US',viewport:{width:390,height:844}
    });
    const page=await ctx.newPage();
    const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,800)));
    await page.goto(origin+'/d1-synthetic-installed-legacy.html',
      {waitUntil:'load',timeout:30000});
    proof.workerInstalled=await page.evaluate(async ()=>{
      if(!navigator.serviceWorker) return false;
      const r=await navigator.serviceWorker.register(
        '/d1-synthetic-installed-legacy-sw.js',{scope:'/'});
      await navigator.serviceWorker.ready;
      return !!r.active;
    });
    check(proof.workerInstalled,'synthetic old SW did not install');
    await ctx.setOffline(true);
    const result=await page.evaluate(async()=>{
      const registration=await navigator.serviceWorker.ready;
      const active=registration.active;
      if(!active) return {saved:false,error:'worker missing'};
      return await new Promise(resolve=>{
        const channel=new MessageChannel();
        let settled=false;
        channel.port1.onmessage=e=>{
          if(!settled){settled=true;resolve(e.data);channel.port1.close();}
        };
        active.postMessage({op:'legacy-offline-write'},[channel.port2]);
        // Safety timeout within page; avoids hanging forever if an installed
        // worker cannot run while browser is disconnected.
        setTimeout(()=>{
          if(!settled){settled=true;resolve({saved:false,error:'timeout'});
            channel.port1.close();}
        },12000);
      });
    });
    proof.actualOfflineServiceWorkerWrite=result.saved===true;
    check(proof.actualOfflineServiceWorkerWrite,
      'old installed SW did not write offline: '+JSON.stringify(result));
    const getRecord=async()=>page.evaluate(async ()=>{
      const req=indexedDB.open('amina_vault_v1_native_999');
      const db=await new Promise((resolve,reject)=>{
        req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
      });
      try {
        const tx=db.transaction('legacy','readonly');
        return await new Promise((resolve,reject)=>{
          const r=tx.objectStore('legacy').get('old-pwa-record');
          r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
        });
      } finally {db.close();}
    });
    proof.legacyReadableOffline=await getRecord()===marker;
    check(proof.legacyReadableOffline,'old plaintext lost before new boot');
    await ctx.setOffline(false);
    await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>{
      const t=document.body?.textContent||'';
      return t.includes('"scope":"synthetic late legacy/offline writer quarantine"') &&
        t.includes('"result":"FAIL"');
    },null,{timeout:35000});
    const output=JSON.parse(await page.locator('body').innerText());
    proof.newVaultRefused=output.result==='FAIL' &&
      String(output.error).includes('web_vault_legacy_data_quarantined');
    check(proof.newVaultRefused,'new encrypted vault admitted old plaintext');
    proof.legacyPreservedAfterNewBoot=await getRecord()===marker;
    check(proof.legacyPreservedAfterNewBoot,'new boot changed legacy bytes');
    proof.noOwnerReassignment=await page.evaluate(()=>{
      const keys=Object.keys(localStorage);
      return !keys.some(x=>x.includes('iamina_d1_wrapped_vault_v1_amina_vault_v1_native_745'));
    });
    check(proof.noOwnerReassignment,'new owner envelope was created');
    proof.installedWorkerStillPresent=await page.evaluate(async()=>
      (await navigator.serviceWorker.getRegistrations()).some(
        r=>r.active?.scriptURL.endsWith('/d1-synthetic-installed-legacy-sw.js')));
    check(proof.installedWorkerStillPresent,
      'old service worker was silently unregistered');
    proof.jsErrors=errors;
    check(errors.length===0,'unexpected JavaScript errors');
    await ctx.close();
    proof.result='PASS_RISK_OBSERVED_AND_QUARANTINED';
  }catch(e){
    proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2500);
    throw e;
  }finally{
    fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_INSTALLED_OFFLINE_PWA='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>{process.exitCode=1;});
