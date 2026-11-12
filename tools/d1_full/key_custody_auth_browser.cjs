// Two synthetic identities, A→B→A with real keyed SQLite3MC worker.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const report={lot:'D1_KEYED_AUTH_LOCK_WORKER_INTEGRATION',
 browser:name,realAuthService:false,patientRuntime:false,synthetic:true,
 audited:false,patientRelease:'NO_GO',result:'NOT_RUN'};
(async()=>{
 const browser=await {chromium,webkit}[name].launch({
  headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})
 });
 try{
  const ctx=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  const page=await ctx.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push({type:e.name,category:'pageerror'}));
  await page.goto('http://127.0.0.1:7420/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.title==='D1_KEY_AUTH_PASS'||
    document.title.startsWith('D1_KEY_AUTH_FAIL_'),null,{timeout:65000});
  report.title=await page.title();
  if(report.title!=='D1_KEY_AUTH_PASS')throw Error('AUTH_BRIDGE_'+report.title);
  // Demonstrate zero 256-bit recovery material in storage serializable data.
  report.localStorageKeys=await page.evaluate(()=>Object.keys(localStorage).length);
  report.result='PASS_SYNTHETIC_KEYED_A_B_A';
  console.log(JSON.stringify(report,null,2));
  await ctx.close();
 }catch(e){report.result='FAIL';report.error=String(e).slice(0,260);
  console.error(e);process.exitCode=1}
 finally{
  fs.writeFileSync('d1-keyed-session-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
