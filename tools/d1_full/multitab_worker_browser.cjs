// Test two independent browser tabs, each with a real SQLite3MC worker.
// Concurrent same-origin access is an experimental safety gate, not a
// certification of real login A/B or physical Safari.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[name];
const report={test:'D1_REAL_WORKER_TWO_TABS',browser:name,synthetic:true,
 physicalSafari:'NOT_TESTED',patientRelease:'NO_GO',result:'NOT_RUN',steps:[]};
async function execute(page,phase){
 const value=await page.evaluate(async (phase)=>new Promise((resolve,reject)=>{
  const worker=new Worker('d1_synthetic_real_worker.js');
  const timer=setTimeout(()=>{worker.terminate();reject(Error('TIMEOUT'))},30000);
  worker.onmessage=e=>{clearTimeout(timer);worker.terminate();resolve(e.data)};
  worker.onerror=()=>{clearTimeout(timer);worker.terminate();reject(Error('WORKER_ERROR'))};
  worker.postMessage(JSON.stringify({phase}));
 }),phase);
 report.steps.push({tab:page===globalThis._a?'A':'B',phase,status:value});
 if(value!=='PASS_'+phase.toUpperCase())throw Error('phase '+phase+' got '+value);
}
(async()=>{
 const browser=await engine.launch({headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const context=await browser.newContext({serviceWorkers:'block'});
  const tabA=await context.newPage(),tabB=await context.newPage();
  globalThis._a=tabA;
  await Promise.all([tabA.goto('http://127.0.0.1:7402/d1_synthetic_worker_harness.html'),
                    tabB.goto('http://127.0.0.1:7402/d1_synthetic_worker_harness.html')]);
  await execute(tabA,'seed_cipher');
  // Both tabs must read only ciphertext through independent dedicated
  // workers. A failure is a real unsupported concurrency limitation.
  await Promise.all([execute(tabA,'verify_cipher'),execute(tabB,'verify_cipher')]);
  await execute(tabB,'wrong_key');
  await execute(tabA,'verify_cipher');
  await execute(tabB,'no_key');
  const keys=await Promise.all([tabA,tabB].map(p=>p.evaluate(()=>({
    localStorageKeys:Object.keys(localStorage),sessionStorageKeys:Object.keys(sessionStorage),
  }))));
  report.storageKeys=keys;
  if(JSON.stringify(keys).includes('D1_FAKE_ONLY_NOT_PATIENT_KEY_20261112'))
   throw Error('KEY_LEAK_TO_STORAGE');
  report.result='PASS_SYNTHETIC_TWO_TABS';
  console.log(JSON.stringify(report,null,2));
  await context.close();
 }catch(err){report.result='FAIL';report.error=String(err).slice(0,260);console.error(err);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-two-tabs-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
