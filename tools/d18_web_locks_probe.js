// D18 CI-only cross-tab and DedicatedWorker Web Locks proof.
// No patient data, no clinical runtime imports, no recovery secrets.
'use strict';
const {chromium} = require('playwright');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const profile = fs.mkdtempSync(path.join(os.tmpdir(),'d18-locks-'));
const base = 'http://127.0.0.1:7396/d18_web_locks_test.html';
const a = 'amina_vault_v1_device_e2dbe28f3eea441086a7274150a00018_d18_ci_dynamic';
const b = 'amina_vault_v1_device_e2dbe28f3eea441086a7274150b00018_d18_ci_dynamic';
const steps = [];
function expect(phase, actual, target) {
  const pass = actual === target;
  steps.push({phase,pass});
  if (!pass) throw Error('D18_WEB_LOCKS_'+phase+'_FAILED_EXPECTED_'+target);
}
async function open(ctx) {
  const page = await ctx.newPage();
  await page.addInitScript({path:'tools/fixtures/d18_web_locks_gate.js'});
  await page.goto(base,{waitUntil:'domcontentloaded',timeout:30000});
  return page;
}
async function acquire(page, name, slot = 'owned') {
  return page.evaluate(async ({name,slot}) => {
    const result = await D18SyntheticVaultLockGate.acquire(name);
    if (result.ok) {
      (window.__d18LeaseSlots ||= {})[slot] = result;
      return 'ACQUIRED';
    }
    return result.reason;
  },{name,slot});
}
async function release(page,slot='owned') {
  return page.evaluate(async slot => {
    const lease = (window.__d18LeaseSlots||{})[slot];
    if(!lease) return false;
    await lease.release();
    delete window.__d18LeaseSlots[slot];
    return true;
  },slot);
}
async function workerAttempt(page,name) {
  return page.evaluate(name => new Promise((resolve,reject) => {
    const w = new Worker('/d18_web_locks_worker.js');
    const timeout = setTimeout(()=>{
      w.terminate();
      reject(new Error('D18_WORKER_LOCK_TIMEOUT'));
    }, 8000);
    w.onmessage = ev => {
      clearTimeout(timeout);
      w.terminate();
      resolve(ev.data);
    };
    w.onerror = () => {
      clearTimeout(timeout);
      w.terminate();
      resolve('WORKER_ERROR');
    };
    w.postMessage({name});
  }),name);
}
async function waitReleased(page,name) {
  const key = 'iamina:d18:ci:v1:'+name;
  await page.waitForFunction(async key => {
    const status = await navigator.locks.query();
    return !status.held.some(lock=>lock.name===key);
  },key,{timeout:15000});
}
(async()=>{
  let ctx;
  try {
    ctx = await chromium.launchPersistentContext(profile,{
      headless:true,locale:'fr-FR',
      args:['--no-sandbox','--disable-dev-shm-usage'],
    });
    const ownerA = await open(ctx);
    const contender = await open(ctx);
    const ownerB = await open(ctx);
    expect('invalid_scope_denied',await acquire(contender,'bad_name'),'INVALID_SCOPE');
    expect('first_vault_a_acquired',await acquire(ownerA,a),'ACQUIRED');
    expect('same_vault_second_tab_denied',await acquire(contender,a),'LOCK_UNAVAILABLE');
    expect('different_vault_b_allowed',await acquire(ownerB,b),'ACQUIRED');
    expect('same_vault_b_second_tab_denied',await acquire(contender,b),'LOCK_UNAVAILABLE');
    expect('worker_same_vault_a_denied',await workerAttempt(contender,a),'LOCK_UNAVAILABLE');
    expect('worker_same_vault_b_denied',await workerAttempt(contender,b),'LOCK_UNAVAILABLE');
    expect('unsupported_web_locks_fail_closed',await (async()=>{
      const unsupported = await open(ctx);
      try {
        return await unsupported.evaluate(async n => {
          Object.defineProperty(navigator,'locks',{value:undefined,configurable:true});
          const value=await D18SyntheticVaultLockGate.acquire(n);
          return value.reason;
        },a);
      }finally{await unsupported.close()}
    })(),'UNSUPPORTED');
    expect('release_b',await release(ownerB),true);
    expect('worker_b_after_release_allowed',await workerAttempt(contender,b),'ACQUIRED');
    await ownerA.close();
    await waitReleased(contender,a);
    expect('a_after_owner_tab_closed_allowed',await acquire(contender,a),'ACQUIRED');
    expect('release_a',await release(contender),true);
    expect('a_after_explicit_release_allowed',await acquire(ownerB,a,'takeover'),'ACQUIRED');
    expect('release_a_takeover',await release(ownerB,'takeover'),true);

    const first = await open(ctx), second = await open(ctx);
    const [one,two] = await Promise.all([
      acquire(first,a),acquire(second,a),
    ]);
    expect('racing_same_vault_exactly_one_owner',
      [one,two].sort().join(','),'ACQUIRED,LOCK_UNAVAILABLE');
    if(one==='ACQUIRED') await release(first);
    if(two==='ACQUIRED') await release(second);
    await first.close();await second.close();
    await contender.close();await ownerB.close();
  }catch(e) {
    steps.push({phase:'harness',pass:false,errorName:e.name||'Error'});
  }finally{
    if(ctx) await ctx.close();
    fs.rmSync(profile,{recursive:true,force:true});
  }
  fs.mkdirSync('d18-web-locks-proof',{recursive:true});
  fs.writeFileSync('d18-web-locks-proof/report.json',
    JSON.stringify({head:process.env.GITHUB_SHA||null,steps},null,2));
  console.log(JSON.stringify(steps));
  if(steps.length!==15 || steps.some(x=>!x.pass)) process.exitCode=1;
})().catch(e=>{console.error('D18_LOCKS_FATAL',e.name);process.exitCode=1});
