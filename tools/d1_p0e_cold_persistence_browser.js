// D1 P0-E: distinguish WebKit failure caused by a second tab from a
// single-tab release/reopen durability regression. Real Flutter/Drift SQLite
// on localhost; synthetic records only; no real user or old vault changes.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[name];
if(!engine)throw Error('unsupported browser');
const base='http://127.0.0.1:7398';
const result={kind:'D1_P0E_FIRST_TAB_COLD_REOPEN',engine:name,
 synthetic:true,phases:[],result:'NOT_RUN'};
async function phase(page,name) {
 await page.goto(base+'/?phase='+name,{waitUntil:'domcontentloaded'});
 const expected='IAMINA_W02_'+name.toUpperCase()+'_PASS';
 await page.waitForFunction(({expected})=>document.title===expected||
   document.title.startsWith('IAMINA_W02_FAIL:')||
   document.documentElement.dataset.iaminaTabLease==='occupied'||
   document.documentElement.dataset.iaminaTabLease==='unavailable',
   {expected},{timeout:90000});
 const observed=await page.evaluate(()=>({
  title:document.title,
  lease:document.documentElement.dataset.iaminaTabLease||null,
  backend:document.documentElement.getAttribute('data-d1-drift-storage'),
 }));
 result.phases.push({phase:name,observed});
 if(observed.title!==expected||observed.lease!=='holding'||!observed.backend)
   throw Error('cold phase failed: '+JSON.stringify(observed));
}
(async()=>{
 const browser=await engine.launch({headless:true,
    ...(name==='chromium'?{args:['--no-sandbox']}:{}),
 });
 try {
  const ctx=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  try {
    const first=await ctx.newPage();
    await phase(first,'seed_a');
    await first.close();
    // No B tab ever created or permitted to touch SQLite.
    const next=await ctx.newPage();
    await phase(next,'verify_a');
    await next.close();
    result.result='PASS_COLD_PERSISTENCE';
    console.log(JSON.stringify(result,null,2));
  } finally {await ctx.close();}
 }catch(e){
  result.result='FAIL_COLD_PERSISTENCE';
  result.error=String(e).slice(0,650);
  console.error(e);
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0e-'+name+'-cold-persistence-proof.json',
    JSON.stringify(result,null,2));
  await browser.close();
 }
})();
