// D18: real Flutter Dart -> browser source Web Locks; synthetic, NO CUTOVER.
'use strict';
const {chromium, webkit} = require('playwright');
const engineName = process.env.D18_DART_SOURCE_BROWSER || 'chromium';
if (!['chromium', 'webkit'].includes(engineName)) throw Error('D18_BAD_ENGINE');
const root = 'iamina:d18:precutover:source:v1:';
const a = 'amina_vault_v1_native_734', b = 'amina_vault_v1_native_812';
const origin = 'http://127.0.0.1:7409/';
const report = [];
function check(name, value, expected) {
  const pass = value === expected;
  report.push({phase:name, pass});
  if (!pass) throw Error('D18_DART_SOURCE_' + name);
}
async function run() {
  const browser = await (engineName === 'chromium' ? chromium : webkit).launch({
    headless: true, ...(engineName === 'chromium' ? {args: ['--no-sandbox']} : {}),
  });
  try {
    const ctx = await browser.newContext({viewport:{width:390,height:844}});
    async function tab(phase, disableLocks=false) {
      const page = await ctx.newPage();
      if (disableLocks) {
        await page.addInitScript(() =>
          Object.defineProperty(navigator, 'locks',
            {value:undefined, configurable:true}));
      }
      await page.goto(origin + '?phase=' + phase,
        {waitUntil:'domcontentloaded',timeout:45000});
      await page.waitForFunction(() =>
        document.title.startsWith('D18_SOURCE_DART_HELD:') ||
        document.title.startsWith('D18_SOURCE_DART_FAIL:'),
        null, {timeout:60000});
      return page;
    }
    async function status(page) {
      return page.evaluate(() => document.title);
    }
    async function release(page, phase) {
      await page.evaluate(() =>
        window.postMessage('D18_SOURCE_RELEASE', window.location.origin));
      await page.waitForFunction(phase =>
        document.title === 'D18_SOURCE_DART_RELEASED:' + phase ||
        document.title === 'D18_SOURCE_DART_FAIL:' + phase,
        phase, {timeout:20000});
      return await status(page);
    }
    async function migrate(page, scope) {
      return page.evaluate(async ({scope,root}) =>
        navigator.locks.request(root+'legacy',{mode:'exclusive',ifAvailable:true},
          async lock => lock
            ? navigator.locks.request(root+'patient:'+scope,
              {mode:'exclusive',ifAvailable:true}, patient => !!patient)
            : false),{scope,root});
    }
    const legacy = await tab('legacy');
    check('flutter_dart_legacy_held', await status(legacy),
      'D18_SOURCE_DART_HELD:legacy');
    const pa = await tab('a');
    check('flutter_dart_patient_a_held', await status(pa), 'D18_SOURCE_DART_HELD:a');
    const pb = await tab('b');
    check('flutter_dart_patient_b_held', await status(pb), 'D18_SOURCE_DART_HELD:b');
    const observer = await tab('audit_denied');
    check('flutter_dart_audit_rejected', await status(observer),
      'D18_SOURCE_DART_FAIL:audit_denied');
    const missing = await tab('legacy', true);
    check('flutter_dart_missing_api_rejected', await status(missing),
      'D18_SOURCE_DART_FAIL:legacy');
    check('legacy_prevents_migration_a', await migrate(observer,a), false);
    check('flutter_dart_release_legacy', await release(legacy,'legacy'),
      'D18_SOURCE_DART_RELEASED:legacy');
    check('patient_a_prevents_migration_a', await migrate(observer,a), false);
    check('patient_b_prevents_migration_b', await migrate(observer,b), false);
    check('flutter_dart_release_patient_a', await release(pa,'a'),
      'D18_SOURCE_DART_RELEASED:a');
    check('migration_a_after_closing_lease', await migrate(observer,a), true);
    check('flutter_dart_release_patient_b', await release(pb,'b'),
      'D18_SOURCE_DART_RELEASED:b');
    check('migration_b_after_closing_lease', await migrate(observer,b), true);
    const crashed = await tab('a');
    check('flutter_dart_reacquire_a', await status(crashed),
      'D18_SOURCE_DART_HELD:a');
    await crashed.close();
    await observer.waitForFunction(async ({root,a}) => {
      const state = await navigator.locks.query();
      return !state.held.some(lock => lock.name === root+'patient:'+a);
    }, {root,a}, {timeout:15000});
    check('closed_tab_releases_physical_lock', await migrate(observer,a), true);
  } finally {
    await browser.close().catch(()=>{});
  }
}
(async () => {
  try { await run(); }
  catch (e) {
    report.push({phase:'harness',pass:false,
      code:String(e.message||'UNKNOWN').replace(/[^A-Za-z0-9_]/g,'_').slice(0,120)});
    process.exitCode=1;
  }
  console.log(JSON.stringify({kind:'CI_ONLY_D18_ACTUAL_DART_TO_WEBLOCK_CANARY',
    browser:engineName, sha:process.env.GITHUB_SHA||null, report}));
  if(report.length!==15 || report.some(x=>!x.pass)) process.exitCode=1;
})().catch(e=>{console.error('D18_DART_SOURCE_FATAL',e.name);process.exitCode=1;});
