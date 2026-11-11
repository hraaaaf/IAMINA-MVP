// D1 P0-C: isolate sqlite3mc Dart loader and real PRAGMA key from Flutter.
// Fake in-memory data ONLY. No physical-at-rest certification implied.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const browserName=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[browserName];
if(!engine)throw Error('Unsupported engine');
const report={test:'D1_BARE_DART_SQLITE3MC',browser:browserName,
  synthetic:true,result:'NOT_RUN',errors:[]};
(async()=>{
 const browser=await engine.launch({headless:true,
  ...(browserName==='chromium'?{args:['--no-sandbox']}:{})});
 try {
  const context=await browser.newContext({serviceWorkers:'block'});
  try{
   const p=await context.newPage();
   p.on('pageerror',e=>report.errors.push({
     name:'pageerror',message:e.message||'',
     stack:String(e.stack||'').slice(0,700),
   }));
   p.on('response',res=>{
    if(res.url().endsWith('sqlite3mc.wasm'))report.wasmHttpStatus=res.status();
   });
   await p.goto('http://127.0.0.1:7398/index.html',
     {waitUntil:'domcontentloaded'});
   try{
    await p.waitForFunction(()=>
      document.title==='D1_BARE_DART_PASS' ||
      document.title.startsWith('D1_BARE_DART_FAIL_'),
      null,{timeout:25000});
   }catch(err){report.errors.push({name:'timeout',message:String(err).slice(0,200)});}
   report.title=await p.title();
   report.stack=await p.evaluate(()=>document.documentElement.dataset.d1Stack||null);
   if(report.title!=='D1_BARE_DART_PASS')throw Error('Bare Dart probe did not succeed: '+report.title);
   report.result='PASS_BARE_DART_SQLITE3MC_ONLY';
   console.log(JSON.stringify(report,null,2));
   await p.close();
  }finally{await context.close();}
 }catch(err){
  report.result='FAIL';
  report.error=String(err).slice(0,450);
  console.error(JSON.stringify(report,null,2));
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0c-bare-dart-'+browserName+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
