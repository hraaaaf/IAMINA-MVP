// A real Drift remote connection from a browser to SQLite3MC inside a worker.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const report={test:'D1_SYNTHETIC_REAL_DRIFT_REMOTE',browser:name,
 patientRuntime:false,synthetic:true,result:'NOT_RUN',steps:[]};
async function phase(ctx,p){
 const tab=await ctx.newPage();
 try{
  await tab.goto('http://127.0.0.1:7405/d1_synthetic_remote_harness.html?phase='+p);
  await tab.waitForFunction(()=>
   document.title.startsWith('D1_REMOTE_PASS_')||
   document.title.startsWith('D1_REMOTE_FAIL_'),null,{timeout:35000});
  const title=await tab.title();
  report.steps.push({phase:p,title});
  if(title!=='D1_REMOTE_PASS_'+p.toUpperCase())throw Error(p+' got '+title);
  return tab;
 }catch(err){await tab.close();throw err;}
}
(async()=>{
 const browser=await {chromium,webkit}[name].launch({
  headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})
 });
 try{
  const ctx=await browser.newContext({serviceWorkers:'block'});
  for(const p of ['seed','reopen','wrong_key','missing_key']){
   const tab=await phase(ctx,p);
   await tab.close();
  }
  report.result='PASS_REMOTE_DRIFT_CIPHER';
  console.log(JSON.stringify(report,null,2));
  await ctx.close();
 }catch(err){report.result='FAIL';report.error=String(err).slice(0,260);
  console.error(err);process.exitCode=1;}
 finally{
  fs.writeFileSync('d1-remote-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
