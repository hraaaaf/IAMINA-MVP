// D1 P0-A: true Git-history v5 -> current v12 Drift WASM migration probe.
// Both bundles built in CI and served under one localhost origin.
// Synthetic data, ephemeral Playwright context, NO patient data or deployment.
'use strict';
const {chromium} = require('playwright');
const root = 'http://127.0.0.1:7390';
const phases = [
  {name: 'historical_v5_seed', url: root + '/historical/?phase=seed',
   expected: 'IAMINA_V5_SEED_PASS'},
  {name: 'v12_upgrade_v5', url: root + '/current/?phase=verify_historical_v5_upgrade',
   expected: 'IAMINA_D1P0A_VERIFY_HISTORICAL_V5_UPGRADE_PASS'},
  {name: 'v12_reopen_after_upgrade',
   url: root + '/current/?phase=verify_historical_v5_upgrade',
   expected: 'IAMINA_D1P0A_VERIFY_HISTORICAL_V5_UPGRADE_PASS'},
];
const proof = {
  kind: 'IAMINA_D1P0A_ACTUAL_GIT_V5_TO_V12_SYNTHETIC',
  oldSourceSha: 'a1d46f9be5f2190a1e8380f28fe4679954f9863f',
  currentSource: 'PR HEAD (Actions checkout)',
  origin: 'localhost-only',
  phases: [],
  limitations: [
    'does not exercise original deployed PWA service worker cache',
    'does not prove closed or fenced concurrent stale v5 tabs',
    'does not prove older-than-v5 schemas',
    'no byte-for-byte backup, crash recovery, cipher, identity or clinical cutover',
  ],
};
async function main() {
  let browser;
  let page;
  const errors = [];
  try {
    browser = await chromium.launch({
      headless:true, args:['--no-sandbox', '--disable-dev-shm-usage'],
    });
    const context = await browser.newContext({locale: 'en-US'});
    page = await context.newPage();
    page.on('pageerror', e => errors.push(String(e).slice(0, 350)));
    for (const phase of phases) {
      await page.goto(phase.url, {waitUntil:'domcontentloaded', timeout:60000});
      await page.waitForFunction(expect => document.title === expect ||
        document.title.startsWith('IAMINA_V5_FAIL:') ||
        document.title.startsWith('IAMINA_D1P0A_FAIL:'),
      phase.expected, {timeout:90000});
      const actual = await page.title();
      if (actual !== phase.expected) {
        throw new Error(phase.name + ': ' + actual);
      }
      proof.phases.push({name:phase.name, pass:true});
    }
    await page.reload({waitUntil:'domcontentloaded', timeout:60000});
    await page.waitForFunction(
      title => document.title === title ||
        document.title.startsWith('IAMINA_D1P0A_FAIL:'),
      phases[2].expected, {timeout:90000},
    );
    if (await page.title() !== phases[2].expected) {
      throw new Error('POST_UPGRADE_HARD_RELOAD_FAILED');
    }
    proof.hardReload = true;
    proof.result = 'PASS';
    console.log(JSON.stringify(proof,null,2));
  } catch (err) {
    if(page) await page.screenshot({path:'d1-p0a-historical-v5-failure.png',
      fullPage:true}).catch(()=>{});
    console.error('D1P0A_HISTORICAL_V5_FAIL:', String(err).slice(0,900));
    if(errors.length) console.error('D1P0A_PAGE_ERRORS:',errors.slice(-5).join(' | '));
    process.exitCode=1;
  } finally {
    if (browser) await browser.close().catch(()=>{});
  }
}
main();
