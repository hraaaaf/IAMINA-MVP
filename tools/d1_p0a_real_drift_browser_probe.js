// D1 P0-A real Drift / SQLite WASM browser-only probe.
// Data and browser profile are synthetic/ephemeral, NOT real legacy bundles.
// A passing result is not a migration, backup, encryption, or patient release.
'use strict';
const { chromium } = require('playwright');

const origin = 'http://127.0.0.1:7388';
const phases = [
  'seed_legacy', 'seed_a', 'late_legacy_write', 'seed_b',
  'verify_a', 'verify_b', 'verify_legacy', 'verify_a',
];
const result = {
  kind: 'IAMINA_D1_P0A_REAL_DRIFT_V12_SYNTHETIC',
  browser: 'Playwright Chromium',
  realStorage: 'drift_flutter / sqlite3.wasm; selected VFS backend not asserted',
  phases: [],
  hardReload: false,
  limitations: [
    'current v12 compiled bundle only',
    'not a historical cached bundle or v1-v12 upgrade',
    'not a stale-tab physical fence, crash recovery or cryptographic restore',
    'not a patient or clinical migration certification',
  ],
};

async function run() {
  let browser;
  let page;
  const errors = [];
  try {
    browser = await chromium.launch({
      headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'],
    });
    const context = await browser.newContext({locale: 'en-US'});
    page = await context.newPage();
    page.on('pageerror', (error) => errors.push(String(error).slice(0, 400)));
    page.on('console', (entry) => {
      if (entry.type() === 'error') errors.push(entry.text().slice(0, 400));
    });

    async function visit(phase, hardReload = false) {
      if (hardReload) {
        await page.reload({waitUntil: 'domcontentloaded', timeout: 45000});
      } else {
        await page.goto(origin + '/?phase=' + phase, {
          waitUntil: 'domcontentloaded', timeout: 45000,
        });
      }
      const expected = 'IAMINA_D1P0A_' + phase.toUpperCase() + '_PASS';
      await page.waitForFunction(
        (passTitle) => document.title === passTitle ||
          document.title.startsWith('IAMINA_D1P0A_FAIL:'),
        expected,
        {timeout: 90000},
      );
      const actual = await page.title();
      if (actual !== expected) {
        throw new Error('DRIFT_PHASE_FAILED ' + phase + ': ' + actual);
      }
      if (hardReload) result.hardReload = true;
      result.phases.push({phase, hardReload, pass: true});
    }

    for (const phase of phases) await visit(phase);
    await visit('verify_a', true);
    if (!result.hardReload || result.phases.length !== phases.length + 1)
      throw new Error('INCOMPLETE_REAL_DRIFT_COVERAGE');
    result.result = 'PASS';
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    if (page) await page.screenshot({path:'d1-p0a-real-drift-fail.png', fullPage:true}).catch(()=>{});
    console.error('D1_P0A_REAL_DRIFT_FAIL:', String(error).slice(0, 900));
    if (errors.length) console.error('BROWSER_ERRORS:', errors.slice(-5).join(' | '));
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close().catch(()=>{});
  }
}

run();
