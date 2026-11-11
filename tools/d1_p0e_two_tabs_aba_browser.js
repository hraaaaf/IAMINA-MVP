// D1 P0-E: SAME browser context, TWO simultaneously active Flutter Web tabs.
// Physical Drift/IndexedDB owner-scope A/B proof with synthetic records only.
// Does NOT simulate real login or Safari product QA, backup/recovery or crypto.
'use strict';
const fs = require('node:fs');
const {chromium, webkit} = require('playwright');

const name = process.env.D1_BROWSER || 'chromium';
if (!['chromium','webkit'].includes(name)) throw Error('unsupported browser');
const type = {chromium,webkit}[name];
const origin = 'http://127.0.0.1:7398';
const outcome={test:'IAMINA_D1_P0E_TWO_LIVE_TABS_ABA',
  browserEngine:name,synthetic:true,origin:'localhost only',
  phases:[],result:'NOT_RUN',scope:'physical Drift/IndexedDB; not real auth'};
async function phase(page, phaseName, id) {
  const url=origin+'/?phase='+phaseName;
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
  const expected='IAMINA_W02_'+phaseName.toUpperCase()+'_PASS';
  await page.waitForFunction(({expected})=>
    document.title===expected || document.title.startsWith('IAMINA_W02_FAIL:'),
    {expected}, {timeout:90000});
  const title=await page.title();
  if(title!==expected)throw Error(id+' '+phaseName+' failed with '+title);
  outcome.phases.push({id,phase:phaseName,pass:true});
}
(async()=>{
  const browser=await type.launch({
    headless:true, ...(name==='chromium'?{args:['--no-sandbox']}:{}),
  });
  try {
    const context=await browser.newContext({
      viewport:{width:390,height:844},
      serviceWorkers:'block',
      locale:'fr-FR',
    });
    try {
      const tabA=await context.newPage();
      const tabB=await context.newPage();
      await phase(tabA,'seed_a','tab-A');
      await phase(tabB,'seed_b','tab-B');
      // Both pages stay open while the physical opposite namespace is read.
      await Promise.all([
        phase(tabA,'verify_a','tab-A'),
        phase(tabB,'verify_b','tab-B'),
      ]);
      await phase(tabB,'verify_a','tab-B-switch-to-A');
      await phase(tabA,'verify_b','tab-A-switch-to-B');
      await Promise.all([
        phase(tabA,'verify_a','tab-A-return'),
        phase(tabB,'verify_b','tab-B-return'),
      ]);
      await Promise.all([tabA.reload(),tabB.reload()]);
      const titles=await Promise.all([tabA.title(),tabB.title()]);
      if(titles.some((v,i)=>v!=='IAMINA_W02_'+(i?'VERIFY_B':'VERIFY_A')+'_PASS')){
        // Reload can finish before Flutter loads: await exact durable probe.
        await Promise.all([
          tabA.waitForFunction(()=>document.title==='IAMINA_W02_VERIFY_A_PASS',
            null,{timeout:90000}),
          tabB.waitForFunction(()=>document.title==='IAMINA_W02_VERIFY_B_PASS',
            null,{timeout:90000}),
        ]);
      }
      outcome.phases.push({id:'both-tabs',phase:'hard-reload',pass:true});
      outcome.result='PASS';
      fs.writeFileSync('d1-p0e-'+name+'-browser-proof.json',
        JSON.stringify(outcome,null,2));
      console.log(JSON.stringify(outcome,null,2));
    }finally{await context.close();}
  }catch(error){
    outcome.result='FAIL';
    outcome.error=String(error).slice(0,500);
    fs.writeFileSync('d1-p0e-'+name+'-browser-proof.json',
      JSON.stringify(outcome,null,2));
    console.error(error);
    process.exitCode=1;
  }finally{await browser.close();}
})();
