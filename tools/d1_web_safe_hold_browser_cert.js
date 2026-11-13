// D1-P0: real production main.dart in isolated localhost Chrome.
// No patient fixture, clinical API or deployment. Existing patient vaults
// must remain absent. This checks a safe hold, NOT clinical functionality.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');

const url = process.env.D1_SAFE_HOLD_URL || 'http://127.0.0.1:7373/';
const out = process.env.D1_SAFE_HOLD_OUT || 'd1-safe-hold-proof';
const sizes = [[390, 844], [768, 1024], [1280, 900]];
const localeCta = /Continue without an account|Continuer sans compte|المتابعة بدون حساب/i;
const hold = /Patient vault unavailable|Coffre patient indisponible|ملف المريض غير متاح/i;

async function semantics(page) {
  const element = page.locator('flt-semantics-placeholder');
  if (await element.count()) {
    await element.first().focus();
    await page.keyboard.press('Enter');
  }
}

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const report = {
    scope: 'real production Flutter main.dart localhost Web, synthetic empty browser',
    head: process.env.D1_CANDIDATE_SHA || process.env.GITHUB_SHA || 'unknown',
    result: 'NOT_RUN',
    clinicalFUE: 'NOT_RUN',
    noRealPatients: true,
    viewports: [],
  };
  try {
    for (const [width, height] of sizes) {
      const context = await browser.newContext({
        viewport: {width, height},
        locale: 'en-US',
        serviceWorkers: 'block',
        acceptDownloads: false,
      });
      const page = await context.newPage();
      const pageErrors = [];
      page.on('pageerror', e => pageErrors.push(String(e.message).slice(0,200)));
      const id = width + 'x' + height;
      await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 45000});
      await page.waitForTimeout(2200);
      await semantics(page);
      let start = page.getByRole('button', {name: localeCta}).first();
      if (!(await start.count())) start = page.getByText(localeCta).first();
      await start.waitFor({state: 'visible', timeout: 20000});
      await start.scrollIntoViewIfNeeded();
      await page.screenshot({
        path: path.join(out, id + '-before.png'),
        animations: 'disabled',
      });
      await start.click();
      await semantics(page);
      const title = page.getByText(hold).first();
      await title.waitFor({state: 'visible', timeout: 25000});
      const prose = await page.locator('flt-semantics').allTextContents();
      const screenshot = path.join(out, id + '-safe-hold.png');
      await page.screenshot({path: screenshot, animations: 'disabled'});
      const vaults = await page.evaluate(async () =>
        (await indexedDB.databases()).map(d => d.name || '')
      );
      if (vaults.includes('amina') ||
          vaults.some(name => /^amina_vault_v1_(native_|device_)/.test(name))) {
        throw Error('Historical or clinical patient IndexedDB opened: ' +
          vaults.join(','));
      }
      if (pageErrors.length) {
        throw Error('Uncaught browser errors: ' + pageErrors.join(';'));
      }
      let signOut = page.getByRole('button',
        {name: /Sign out|Se déconnecter|تسجيل الخروج/i}).first();
      if (!(await signOut.count())) {
        signOut = page.getByText(/Sign out|Se déconnecter|تسجيل الخروج/i).first();
      }
      await signOut.waitFor({state: 'visible', timeout: 10000});
      await signOut.click();
      let returnedToGuest = page.getByRole('button', {name: localeCta}).first();
      if (!(await returnedToGuest.count())) {
        returnedToGuest = page.getByText(localeCta).first();
      }
      await returnedToGuest.waitFor({state: 'visible', timeout: 12000});
      report.viewports.push({viewport: id, holdVisible: true,
        signedOutToGuest: true, existingPatientDatabaseUntouched: true,
        before: id + '-before.png', after: id + '-safe-hold.png',
        semanticsCount: prose.length});
      await context.close();
    }
    report.result = 'PASS';
  } catch (error) {
    report.result = 'FAIL';
    report.error = String(error.stack || error).slice(0,2500);
    throw error;
  } finally {
    fs.writeFileSync(path.join(out, 'proof.json'),
      JSON.stringify(report, null, 2));
    await browser.close();
    console.log('D1_PRODUCTION_SAFE_HOLD=' + JSON.stringify(report));
  }
})().catch(() => process.exitCode = 1);
