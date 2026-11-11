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
  const storage=await page.evaluate(
    ()=>document.documentElement.getAttribute('data-d1-drift-storage'));
  if (title!==expected) {
    outcome.phases.push({id,phase:phaseName,pass:false,storage,
      message:title.slice(0,220)});
    throw Error(id+' '+phaseName+' failed with '+title+
      ' [Drift VFS='+storage+']');
  }
  if (!storage) {
    throw Error(id+' '+phaseName+' missing actual Drift storage VFS proof');
  }
  outcome.phases.push({id,phase:phaseName,pass:true,storage});
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
      outcome.browserFeatures=await tabA.evaluate(()=>({
        crossOriginIsolated:globalThis.crossOriginIsolated===true,
        sharedArrayBuffer:typeof SharedArrayBuffer==='function',
        navigatorLocks:typeof navigator.locks?.request==='function',
        opfs:typeof navigator.storage?.getDirectory==='function',
        indexedDbAvailable:typeof indexedDB==='object',
      }));
      if (!outcome.browserFeatures.crossOriginIsolated) {
        throw Error('Synthetic COOP/COEP test origin not cross-origin isolated');
      }
      await phase(tabA,'seed_a','tab-A');
      await phase(tabB,'seed_b','tab-B');
      // Control arm: both tabs remain live, but verification requests are
      // serialized to distinguish same-origin persistence from DB contention.
      await phase(tabA,'verify_a','tab-A-sequential-control');
      await phase(tabB,'verify_b','tab-B-sequential-control');
      // Stress arm: prove reads at the same time, never silently serialize.
      const concurrent = await Promise.allSettled([
        phase(tabA,'verify_a','tab-A'),
        phase(tabB,'verify_b','tab-B'),
      ]);
      if (concurrent.some(p=>p.status==='rejected')) {
        outcome.concurrentErrors=concurrent.map((p,i)=>({
          tab:i?'B':'A',status:p.status,
          error:p.status==='rejected'?String(p.reason).slice(0,260):null,
        }));
        // Negative diagnostic: distinguish a transient two-writer conflict
        // from persistent loss. Still FAIL the gate even if recovery succeeds.
        outcome.afterConflict={};
        for (const [tab,phaseName] of [
          [tabA,'verify_a'],[tabB,'verify_b']]) {
          try {
            await phase(tab,phaseName,'recovery-check');
            outcome.afterConflict[phaseName]='PRESENT';
          } catch(e) {
            outcome.afterConflict[phaseName]=String(e).slice(0,220);
          }
        }
        throw Error('simultaneous Web vault reads failed; see afterConflict');
      }
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
