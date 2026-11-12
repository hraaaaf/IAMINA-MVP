// No patient credentials. Real Drift+SQLite3MC and browser WebCrypto on fixtures.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const report={name:'D1_HIGH_BROWSER_BACKUP_E2E',browser:name,
 synthetic:true,realPatientRuntime:false,antiRollback:'NOT_PROVEN',
 patientRelease:'NO_GO',result:'NOT_RUN'};
(async()=>{
 const engine={chromium,webkit}[name];if(!engine)throw Error('BROWSER');
 const browser=await engine.launch({
  headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})
 });
 try{
  const context=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push({type:e.name,message:String(e.message).slice(0,200)}));
  await page.goto('http://127.0.0.1:7412/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>
    document.title==='D1_BACKUP_PASS'||document.title.startsWith('D1_BACKUP_FAIL_'),
    null,{timeout:50000});
  const title=await page.title();
  report.title=title;
  if(title!=='D1_BACKUP_PASS')throw Error('BROWSER_BACKUP_'+title);
  // The backup container must never include the fictitious plaintext marker.
  // This is supplementary: encryption/authentication checked inside Flutter.
  report.result='PASS_WEBCRYPTO_AUTHENTICATED_ROUNDTRIP_SYNTHETIC';
  console.log(JSON.stringify(report,null,2));
  await context.close();
 }catch(e){report.result='FAIL';report.error=String(e).slice(0,320);console.error(e);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-high-backup-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
