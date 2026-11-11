// D1 P0-E. Real synthetic IndexedDB upgrade proof across two Flutter builds:
// exact old Drift 2.31 baseline -> exact new Drift 2.35.4, same ORIGIN + context.
// Separate fresh-context old->old diagnostic prevents false migration blame.
// No patient data, no backend authentication, no encrypted vault claim.
'use strict';
const fs = require('node:fs');
const {chromium, webkit} = require('playwright');
const name = process.env.D1_BROWSER || 'chromium';
const engine = {chromium, webkit}[name];
if (!engine) throw Error('unsupported browser');
const origin = 'http://127.0.0.1:7398';
const report = {
  kind: 'D1_P0E_OLD_231_TO_NEW_2354_SHARED_ORIGIN',
  browser: name,
  synthetic: true,
  old: 'Drift 2.31.0, current committed worker and sqlite3.wasm',
  next: 'Drift 2.35.4 and SHA256-verified official worker and sqlite3.wasm',
  coexistence: 'historical v5 cached tab NOT covered',
  controls: [],
  result: 'NOT_RUN',
};

async function phase(page, bundle, phaseName, label) {
  const expected = 'IAMINA_W02_' + phaseName.toUpperCase() + '_PASS';
  await page.goto(origin + '/' + bundle + '/?phase=' + phaseName, {
    waitUntil: 'domcontentloaded', timeout: 60000,
  });
  await page.waitForFunction(({expected}) => {
    const title = document.title;
    const lease = document.documentElement.dataset.iaminaTabLease;
    return title === expected || title.startsWith('IAMINA_W02_FAIL:') ||
      lease === 'occupied' || lease === 'unavailable';
  }, {expected}, {timeout: 90000});
  const observed = await page.evaluate(() => ({
    title: document.title,
    lease: document.documentElement.dataset.iaminaTabLease ?? null,
    vfs: document.documentElement.getAttribute('data-d1-drift-storage'),
    crossOriginIsolated: globalThis.crossOriginIsolated === true,
    // Names only, no data and no patient content. Optional WebKit API.
    storageDatabases: typeof indexedDB.databases === 'function'
      ? indexedDB.databases().then(x => x.map(y => y.name)) : [],
  }));
  const success = observed.title === expected &&
    observed.lease === 'holding' && !!observed.vfs &&
    observed.crossOriginIsolated === false;
  const entry = {label, bundle, phase:phaseName, success, observed};
  report.controls.push(entry);
  if (!success) throw Error('phase failed: ' + JSON.stringify(entry).slice(0,650));
}

async function trial(browser, label, readBundle) {
  const context = await browser.newContext({
    locale: 'fr-FR', serviceWorkers: 'block', viewport: {width: 390,height:844},
  });
  const trialResult = {kind:label, readBundle, result:'NOT_RUN'};
  try {
    const oldTab = await context.newPage();
    try { await phase(oldTab, 'old', 'seed_a', label+'-write-old'); }
    finally { await oldTab.close(); }
    const reader = await context.newPage();
    try {
      await phase(reader, readBundle, 'verify_a', label+'-read');
      trialResult.result = 'PASS';
    } finally { await reader.close(); }
  } catch (e) {
    trialResult.result = 'FAIL';
    trialResult.error = String(e).slice(0,750);
  } finally {
    await context.close();
  }
  return trialResult;
}

(async () => {
  const browser = await engine.launch({
    headless: true, ...(name==='chromium' ? {args:['--no-sandbox']} : {}),
  });
  try {
    report.oldToOld = await trial(browser, 'OLD_TO_OLD_COLD_CONTROL','old');
    report.oldToNew = await trial(browser, 'OLD_TO_NEW_COLD_COMPAT','new');
    // A passed old->new is necessary but not sufficient: B must stay isolated.
    if (report.oldToNew.result !== 'PASS') {
      report.result = 'FAIL_OLD_TO_NEW';
      throw Error('Cross-version read failed; old cold baseline='+
        report.oldToOld.result+'; no legacy cutover authorized');
    }
    const ctx = await browser.newContext({locale:'fr-FR',
      serviceWorkers:'block'});
    try {
      // Independent new-engine namespace test; does NOT mutate the earlier trial.
      const tab = await ctx.newPage();
      await phase(tab,'new','seed_a','new-scope-A');
      await phase(tab,'new','seed_b','new-scope-B');
      await phase(tab,'new','verify_a','new-return-A');
      await phase(tab,'new','verify_b','new-return-B');
      await tab.close();
    } finally {await ctx.close();}
    report.result='PASS_OLD_TO_NEW';
    console.log(JSON.stringify(report,null,2));
  } catch (e) {
    if (report.result === 'NOT_RUN') report.result='FAIL';
    report.error=String(e).slice(0,750);
    console.error(e);
    process.exitCode=1;
  } finally {
    fs.writeFileSync('d1-p0e-'+name+'-old-to-new-proof.json',
      JSON.stringify(report,null,2));
    await browser.close();
  }
})();