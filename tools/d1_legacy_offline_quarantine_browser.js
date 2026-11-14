// D1 P0: an old, previously-installed offline writer CANNOT be retroactively
// patched by a new bundle. Verify new vault fails closed on its next open
// without deleting the writer's legacy IndexedDB records. Synthetic only.
const {chromium} = require('playwright');
const fs = require('fs');

const folder = 'd1-legacy-offline-quarantine-proof';
const marker = 'D1_SYNTHETIC_OLD_PWA_PLAINTEXT_745';
const legacyStore = 'amina_vault_v1_native_999'; // OTHER patient namespace
const uri = 'http://127.0.0.1:7475/';

(async () => {
  fs.mkdirSync(folder, {recursive: true});
  const proof = {
    scope: 'synthetic legacy writer after encrypted enrollment, offline',
    head: process.env.D1_CANDIDATE_SHA || 'unknown',
    clinicalGo: false,
    result: 'NOT_RUN',
    oldPwaWriterActuallyBlocked: false, // NOT a claim we can make offline
  };
  const browser = await chromium.launch({headless: true});
  try {
    const ctx = await browser.newContext({
      viewport: {width: 390, height: 844},
      locale: 'en-US',
      serviceWorkers: 'block',
    });
    const page = await ctx.newPage();
    const errors = [];
    const consoleMessages = [];
    page.on('pageerror', e => errors.push(String(e.stack || e).slice(0, 1600)));
    page.on('console', m => consoleMessages.push(m.type() + ': ' + m.text().slice(0, 250)));
    await page.goto(uri, {waitUntil: 'domcontentloaded', timeout: 60000});
    // The synthetic Dart entrypoint may publish an early error as JSON.
    // Observe that explicitly instead of waiting 60 seconds for a hidden UI.
    await page.waitForFunction(() => {
      const text = document.body?.textContent || '';
      return document.querySelector('#d1-late-legacy-probe-trigger') ||
        (text.includes('"scope":"synthetic late legacy/offline writer quarantine"') &&
         text.includes('"result":"FAIL"'));
    }, null, {timeout: 30000});
    if (!(await page.locator('#d1-late-legacy-probe-trigger').count())) {
      const body = (await page.locator('body').innerText()).slice(0, 2000);
      throw Error('D1 probe setup failed before legacy injection: ' + body);
    }

    // The new encrypted vault is already enrolled and closed. Simulate a
    // stale PWA that remains capable of writing an old unencrypted store.
    await ctx.setOffline(true);
    proof.legacyPlaintextWriteWhileOffline = await page.evaluate(async ({marker,legacyStore}) => {
      const request = indexedDB.open(legacyStore, 1);
      const db = await new Promise((resolve, reject) => {
        request.onupgradeneeded = () => {
          if (!request.result.objectStoreNames.contains('legacy')) {
            request.result.createObjectStore('legacy');
          }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      try {
        const tx = db.transaction('legacy', 'readwrite');
        tx.objectStore('legacy').put(marker, 'old-pwa-record');
        await new Promise((resolve, reject) => {
          tx.oncomplete = resolve;
          tx.onerror = () => reject(tx.error);
          tx.onabort = () => reject(tx.error);
        });
        return true;
      } finally {
        db.close();
      }
    }, {marker,legacyStore});
    proof.onlyForeignLegacyPresent = await page.evaluate(async legacyStore => {
      const names=(await indexedDB.databases()).map(d=>d.name);
      return names.includes(legacyStore) && !names.includes('amina');
    },legacyStore);

    // Dispatch directly: the Flutter engine may visually cover this fixture
    // button. This is a synthetic coordination signal, not an end-user UI.
    await page.locator('#d1-late-legacy-probe-trigger').evaluate(el => el.click());
    await page.waitForFunction(() => {
      const text = document.body?.textContent || '';
      return text.includes('"scope":"synthetic late legacy/offline writer quarantine"') &&
        text.includes('"result":"');
    }, null, {timeout: 30000});
    const result = JSON.parse(await page.locator('body').innerText());
    proof.candidate = result;
    proof.legacyRecordStillReadable = await page.evaluate(async legacyStore => {
      const request = indexedDB.open(legacyStore);
      const db = await new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      try {
        const tx = db.transaction('legacy', 'readonly');
        return await new Promise((resolve, reject) => {
          const get = tx.objectStore('legacy').get('old-pwa-record');
          get.onsuccess = () => resolve(get.result);
          get.onerror = () => reject(get.error);
        });
      } finally {
        db.close();
      }
    },legacyStore);
    proof.jsErrors = errors;
    if (proof.onlyForeignLegacyPresent !== true ||
        proof.legacyPlaintextWriteWhileOffline !== true ||
        proof.legacyRecordStillReadable !== marker ||
        result.result !== 'PASS' || errors.length) {
      throw Error('Late legacy quarantine regression: ' +
        JSON.stringify(proof).slice(0, 2200));
    }
    proof.result = 'PASS';
    await ctx.close();
  } catch (e) {
    proof.result = 'FAIL';
    proof.error = String(e.stack || e).slice(0, 2400);
    throw e;
  } finally {
    fs.writeFileSync(folder + '/proof.json', JSON.stringify(proof, null, 2));
    console.log('D1_LATE_OFFLINE_LEGACY_QUARANTINE=' + JSON.stringify(proof));
    await browser.close();
  }
})().catch(() => { process.exitCode = 1; });
