/* D18-A isolated actual WebCrypto recovery, no patient fixtures. */
'use strict';
const {chromium} = require('playwright');
const fs=require('fs');
const path=require('path');
const out='d18-a-webcrypto-key-proof';
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const events=[];
 try {
   // Flutter Web's locale-sensitive bootstrap requires a valid locale.
   // Match the proven D18 real-Drift Chromium harness.
   const context=await browser.newContext({locale:'fr-FR'});
   const page=await context.newPage();
   page.on('pageerror',e=>{if(events.length<25)events.push('pageerror: '+e.message.slice(0,300));});
   page.on('requestfailed',r=>{if(events.length<25)events.push('request: '+r.url().slice(0,250));});
   page.on('console',m=>{if(m.type()==='error'&&events.length<25)events.push('console: '+m.text().slice(0,300));});
   await page.goto('http://127.0.0.1:7390/',{waitUntil:'domcontentloaded',timeout:40000});
   try {
     await page.waitForFunction(()=>document.title==='D18_KEY_PASS'||
       document.title==='D18_KEY_FAIL',null,{timeout:150000});
   }catch(e){events.push('timed out: '+String(e).slice(0,180));}
   const result=await page.evaluate(()=>({
     title:document.title,
     stage:document.documentElement.dataset.d18Stage||null,
     error:document.documentElement.dataset.d18Error||null,
   }));
   const report={head:process.env.D18_CANDIDATE_SHA||'unknown',
     proof:'actual Flutter Web + WebCrypto key wrapping/recovery, synthetic-only',
     passed:result.title==='D18_KEY_PASS',
     stage:result.stage,error:result.error,events};
   fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
   console.log(JSON.stringify(report));
   if(!report.passed)process.exitCode=1;
   await context.close();
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
