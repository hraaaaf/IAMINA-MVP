// D1 P0-A: genuine Git-history Flutter v5 tab stays OPEN while a separate
// v12 tab creates patient vault A. Old v5 then attempts a late SQLite write.
// This is an intentionally NEGATIVE safety proof: SUCCESS means the old writer
// remains dangerous, NOT that migration/cutover is safe. Synthetic rows only.
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const root = 'http://127.0.0.1:7390';
const proof = {
  kind: 'IAMINA_D1P0A_TRUE_GIT_V5_LIVE_TAB_NEGATIVE',
  oldCommit: 'a1d46f9be5f2190a1e8380f28fe4679954f9863f',
  currentCommit: 'PR HEAD (Actions checkout)',
  synthetic: true,
  origin: 'localhost-only',
  assertions: [],
  expectedClinicalGate: 'NO_GO',
  limitations: [
    'old Web bundle remains live, but is not served from a cached Service Worker',
    'only Chromium + one old v5 bundle and SQLite sharedIndexedDb/Drift auto VFS',
    'does not prove older v1 app, OPFS, WebKit/Safari, crash or backup',
    'cannot authorize any clinical or automated legacy migration',
  ],
};
const expected = (name, actual, title) => {
  if (actual !== title) throw new Error(name + ' returned ' + actual);
  proof.assertions.push({name,pass:true});
};
async function phase(page, path, title, name) {
  await page.goto(root+path,{waitUntil:'domcontentloaded',timeout:60000});
  await page.waitForFunction(t => document.title === t ||
    document.title.startsWith('IAMINA_V5_FAIL:') ||
    document.title.startsWith('IAMINA_D1P0A_FAIL:'),
  title,{timeout:90000});
  expected(name,await page.title(),title);
}
(async()=>{
  let browser;
  let context;
  let oldTab;
  let current;
  try {
    browser = await chromium.launch({headless:true,args:['--no-sandbox']});
    context = await browser.newContext({
      locale:'en-US',
      serviceWorkers:'block', // Avoid falsely claiming cached SW coverage.
    });
    const seed = await context.newPage();
    await phase(seed,'/historical/?phase=seed','IAMINA_V5_SEED_PASS','v5_git_seed');
    await seed.close();

    oldTab = await context.newPage();
    await phase(oldTab,'/historical/?phase=hold_old_tab',
      'IAMINA_V5_LIVE_OLD_TAB_READY','old_v5_tab_still_alive');
    current = await context.newPage();
    await phase(current,'/current/?phase=seed_a',
      'IAMINA_D1P0A_SEED_A_PASS','v12_opens_isolated_patient_vault_A');

    await oldTab.evaluate(() => {
      window.postMessage('IAMINA_D1_V5_LATE_WRITE', window.location.origin);
    });
    await oldTab.waitForFunction(() =>
      document.title === 'IAMINA_V5_LATE_WRITE_AFTER_V12_A_PASS' ||
      document.title.startsWith('IAMINA_V5_LATE_WRITE_FAIL:'),
    {timeout:90000});
    expected('REAL_OLD_V5_LATE_WRITE_STILL_POSSIBLE',
      await oldTab.title(),'IAMINA_V5_LATE_WRITE_AFTER_V12_A_PASS');

    // Keep the REAL historic v5 code alive while the isolated v12 account B
    // opens and A/B are both read back. This proves containment, NOT a
    // capability to stop an old offline writer.
    await phase(current,'/current/?phase=seed_b',
      'IAMINA_D1P0A_SEED_B_PASS','v12_opens_isolated_patient_vault_B');
    await phase(current,'/current/?phase=verify_a',
      'IAMINA_D1P0A_VERIFY_A_PASS','A_unchanged_while_v5_tab_writes');
    await phase(current,'/current/?phase=verify_b',
      'IAMINA_D1P0A_VERIFY_B_PASS','B_unchanged_while_v5_tab_writes');

    // Close stale writer before upgrading legacy SQLite v5 to v12. This is
    // only a diagnostic verification, NOT a credential/possession cutover.
    await oldTab.close();
    oldTab=null;
    await phase(current,'/current/?phase=verify_historical_v5_late_write',
      'IAMINA_D1P0A_VERIFY_HISTORICAL_V5_LATE_WRITE_PASS',
      'v12_drift_readback_preserves_both_old_rows');
    await phase(current,'/current/?phase=verify_a',
      'IAMINA_D1P0A_VERIFY_A_PASS','A_vault_remains_isolated_and_integral');
    await phase(current,'/current/?phase=verify_b',
      'IAMINA_D1P0A_VERIFY_B_PASS','B_preserved_after_legacy_readback');
    proof.result='PASS_NEGATIVE_PROOF';
    proof.conclusion='UNFENCED_REAL_V5_WRITER_CONFIRMED';
    proof.patientCutover='FORBIDDEN';
    fs.writeFileSync('d1-p0a-real-v5-old-tab-negative-proof.json',
      JSON.stringify(proof,null,2));
    console.log(JSON.stringify(proof,null,2));
  } catch(e) {
    proof.result='HARNESS_FAILURE';
    proof.error=String(e).slice(0,700);
    fs.writeFileSync('d1-p0a-real-v5-old-tab-negative-proof.json',
      JSON.stringify(proof,null,2));
    if(oldTab) await oldTab.screenshot({path:'d1-p0a-real-v5-old-tab-failure.png'})
      .catch(()=>{});
    console.error('D1P0A_TRUE_OLD_V5_TAB_FAIL:',proof.error);
    process.exitCode=1;
  } finally {
    if(browser) await browser.close().catch(()=>{});
  }
})();
