/* Real Flutter Web + pinned Drift WASM/worker: persistent Chromium proof. */
/* Synthetic-only. Does not test encryption at rest or clinical migration. */
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const os = require('os');
const path = require('path');
const origin = 'http://127.0.0.1:7389/';
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'iamina-d18-drift-'));
const out = 'd18-real-drift-web-proof';
fs.mkdirSync(out,{recursive:true});
const steps = [];
async function verify(page,phase){
  const events=[];
  const log=(kind,value)=>{if(events.length<45)events.push({kind,value:String(value).slice(0,450)});};
  page.on('console',m=>{if(m.type()==='error'||m.type()==='warning')log('console:'+m.type(),m.text());});
  page.on('pageerror',e=>log('pageerror',e.message));
  page.on('requestfailed',r=>log('requestfailed',r.url()+':'+(r.failure()?.errorText||'unknown')));
  page.on('response',r=>{if(r.status()>=400)log('http',r.status()+' '+r.url());});
  const address = new URL(origin);
  address.searchParams.set('phase',phase);
  await page.goto(address.toString(),{waitUntil:'domcontentloaded',timeout:45000});
  try {
    await page.waitForFunction(() => document.title.startsWith('D18_DRIFT_PASS:') ||
      document.title.startsWith('D18_DRIFT_FAIL:'),null,{timeout:30000});
  }catch(e){
    const state=await page.evaluate(()=>({
      title:document.title,
      stage:document.documentElement.dataset.d18Stage||null,
      error:document.documentElement.dataset.d18Error||null,
      body:document.body?.innerText?.slice(0,1000)||'',
      href:location.href,
    })).catch(err=>({readError:String(err)}));
    const snapshot={phase,state,events,timeout:String(e).slice(0,200)};
    steps.push({phase,pass:false,diagnostic:snapshot});
    throw Error('D18 browser stalled '+JSON.stringify(snapshot).slice(0,4200));
  }
  const result = await page.evaluate(()=>({
    title: document.title,
    stage: document.documentElement.dataset.d18Stage || null,
    error: document.documentElement.dataset.d18Error || null,
  }));
  const pass = result.title === 'D18_DRIFT_PASS:' + phase;
  steps.push({phase,pass,...(!pass?{error:result.error,stage:result.stage,events}: {})});
  if(!pass)throw Error(phase + ': ' + JSON.stringify(result));
}
async function processPhase(context, phase){
  const page = await context.newPage();
  try { await verify(page,phase); } finally { await page.close(); }
}
(async()=>{
  let context;
  try {
    context=await chromium.launchPersistentContext(root,
      {headless:true,locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    await processPhase(context,'seed_legacy');
    await processPhase(context,'seed_a');
    await context.close();context=null;
    // Chromium is a NEW process but has the SAME isolated temporary user profile.
    context=await chromium.launchPersistentContext(root,
      {headless:true,locale:'fr-FR',args:['--no-sandbox','--disable-dev-shm-usage']});
    for(const phase of ['verify_a','verify_b','verify_legacy']){
      await processPhase(context,phase);
    }
  } catch(e) {
    steps.push({phase:'harness',pass:false,error:String(e).slice(0,500)});
  } finally {
    if(context)await context.close();
    fs.rmSync(root,{recursive:true,force:true});
  }
  const proof={kind:'real IAMINA driftDatabase Web, synthetic Chrome separate-process restart',
    head:process.env.D18_CANDIDATE_SHA||'unknown',
    expected:['seed_legacy','seed_a','verify_a','verify_b','verify_legacy'],
    steps,passed:steps.filter(s=>s.pass).length};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(proof,null,2));
  console.log(JSON.stringify(proof));
  if(proof.passed!==5 || steps.length!==5 || steps.some(s=>!s.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
