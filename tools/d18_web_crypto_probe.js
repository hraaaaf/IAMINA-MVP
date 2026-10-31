/* D18 true WebCrypto + physical IndexedDB backup export/recovery, synthetic-only. */
'use strict';
const {chromium}=require('playwright'), fs=require('fs'), path=require('path');
const out='d18-web-fue-proof';
fs.mkdirSync(out,{recursive:true});
const origin='http://127.0.0.1:7387/',steps=[];
const head=process.env.D18_CANDIDATE_SHA||'unknown';
async function phase(page,name,payload){
 const url=new URL(origin);url.searchParams.set('phase',name);
 if(payload)url.searchParams.set('payload',payload);
 await page.goto(url.toString(),{waitUntil:'domcontentloaded',timeout:40000});
 await page.waitForFunction(()=>
   document.title.startsWith('D18_CRYPTO_PASS:') ||
   document.title.startsWith('D18_CRYPTO_FAIL:'),null,{timeout:90000});
 const result=await page.evaluate(()=>({
  title:document.title,
  error:document.documentElement.dataset.d18Error||null,
 }));
 const step={phase:name,title:result.title,pass:result.title==='D18_CRYPTO_PASS:'+name};
 if(!step.pass){step.error=result.error;steps.push(step);throw Error(name+': '+JSON.stringify(result));}
 steps.push(step);return result;
}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 let context,other;
 try{
  context=await browser.newContext({viewport:{width:390,height:844}});
  const page=await context.newPage();
  await phase(page,'seed_a');
  const ciphertext=await page.locator('#d18-crypto-synthetic-export').textContent();
  if(!ciphertext || ciphertext.length<100)throw Error('Missing real WebCrypto backup');
  await phase(page,'verify_b');
  await phase(page,'verify_a');
  // Brand-new browser profile: no source IndexedDB state, only encrypted file.
  await context.close();context=null;
  other=await browser.newContext({viewport:{width:390,height:844}});
  const fresh=await other.newPage();
  await phase(fresh,'wrong_pass',ciphertext);
  await phase(fresh,'tampered',ciphertext);
  await phase(fresh,'restore_c',ciphertext);
  await phase(fresh,'verify_c');
  await phase(fresh,'reject_second_restore',ciphertext);
 }catch(err){
  steps.push({phase:'harness',pass:false,error:String(err.message||err).slice(0,500)});
 }finally{
  if(context)await context.close();
  if(other)await other.close();
  await browser.close();
 }
 const proof={head,kind:'Real Chromium WebCrypto, synthetic local-only IndexedDB, fresh browser-profile transfer',steps,
  passed:steps.filter(s=>s.pass).length,total:8};
 fs.writeFileSync(path.join(out,'encrypted-recovery-report.json'),JSON.stringify(proof,null,2));
 console.log(JSON.stringify(proof,null,2));
 if(proof.passed!==8 || steps.some(s=>!s.pass))process.exitCode=1;
})().catch(err=>{console.error(err);process.exitCode=1;});
