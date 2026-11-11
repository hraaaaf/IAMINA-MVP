// D1.8 P0: PROOF of the SAFE alternative to unrestricted concurrent tabs.
// A physical SQLite-backed Flutter runtime never starts in tab B while A owns
// the origin Web Lock. Reopening after close preserves separate A and B rows.
// Synthetic fixtures, no patient data, no clinical deployment.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const kind={chromium,webkit}[name];
if(!kind)throw Error('unsupported browser');
const origin='http://127.0.0.1:7398';
const lockName='iamina-web-patient-runtime-single-writer-v1';
const result={test:'IAMINA_D1P0E_FAIL_CLOSED_SINGLE_RUNTIME',
 browser:name,synthetic:true,phases:[],result:'NOT_RUN',
 limits:['old v5 cached PWA not fenced','no live account login',
         'not same-device real Safari','no ciphertext at rest']};
async function active(page,phase,id){
 await page.goto(origin+'/?phase='+phase,{waitUntil:'domcontentloaded'});
 const expected='IAMINA_W02_'+phase.toUpperCase()+'_PASS';
 await page.waitForFunction(({expected})=>document.title===expected||
   document.title.startsWith('IAMINA_W02_FAIL:')||
   document.documentElement.dataset.iaminaTabLease==='occupied'||
   document.documentElement.dataset.iaminaTabLease==='unavailable',
   {expected},{timeout:90000});
 const info=await page.evaluate(()=>({
   title:document.title,
   lease:document.documentElement.dataset.iaminaTabLease||null,
   backend:document.documentElement.getAttribute('data-d1-drift-storage'),
 }));
 if(info.title!==expected||info.lease!=='holding'||!info.backend)
   throw Error('runtime did not open safely: '+JSON.stringify(info));
 result.phases.push({id,phase,admission:'holding',backend:info.backend});
}
async function denied(page,phase,id){
 await page.goto(origin+'/?phase='+phase,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>['occupied','unavailable'].includes(
    document.documentElement.dataset.iaminaTabLease),
    null,{timeout:15000});
 const info=await page.evaluate(()=>({
  state:document.documentElement.dataset.iaminaTabLease,
  backend:document.documentElement.getAttribute('data-d1-drift-storage'),
  title:document.title,
  warning:document.querySelector('[role=alert]')?.textContent||null,
 }));
 if(info.state!=='occupied'||info.backend!==null||!info.warning)
   throw Error('second tab was not denied BEFORE SQLite: '+JSON.stringify(info));
 result.phases.push({id,phase,admission:'denied-before-db',backend:null});
}
async function releaseObserved(page) {
 await page.waitForFunction(async lockName=>{
   const q=await navigator.locks.query();
   return !q.held.some(entry=>entry.name===lockName);
 },lockName,{timeout:15000});
}
(async()=>{
 const browser=await kind.launch({headless:true,
  ...(name==='chromium'?{args:['--no-sandbox']}:{}),
 });
 try {
  const context=await browser.newContext({locale:'fr-FR',
   viewport:{width:390,height:844},serviceWorkers:'block'});
  try {
   const tabA=await context.newPage();
   const tabB=await context.newPage();
   await active(tabA,'seed_a','tab-A');
   result.features=await tabA.evaluate(()=>({
    crossOriginIsolated:globalThis.crossOriginIsolated,
    webLocks:typeof navigator.locks?.request==='function',
    opfs:typeof navigator.storage?.getDirectory==='function',
   }));
   await denied(tabB,'seed_b','tab-B-while-A-held');
   await active(tabA,'verify_a','tab-A-after-rejected-B');
   await tabA.close();
   await releaseObserved(tabB);
   await active(tabB,'seed_b','tab-B-after-A-closed');
   await active(tabB,'verify_b','tab-B-stable');
   const tabC=await context.newPage();
   await denied(tabC,'verify_a','tab-C-while-B-held');
   await tabB.close();
   await releaseObserved(tabC);
   await active(tabC,'verify_a','tab-C-return-A');
   await active(tabC,'verify_b','tab-C-return-B');
   await active(tabC,'verify_a','tab-C-A-B-A');
   await tabC.reload();
   await tabC.waitForFunction(()=>
    document.title==='IAMINA_W02_VERIFY_A_PASS'&&
    document.documentElement.dataset.iaminaTabLease==='holding',
    null,{timeout:90000});
   result.phases.push({id:'tab-C',phase:'reload-A',
      admission:'holding',retained:true});
   result.result='PASS_FAIL_CLOSED';
   console.log(JSON.stringify(result,null,2));
  }finally{await context.close();}
 }catch(e){
  result.result='FAIL';
  result.error=String(e).slice(0,600);
  console.error(e);
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0e-'+name+'-single-runtime-proof.json',
   JSON.stringify(result,null,2));
  await browser.close();
 }
})();
