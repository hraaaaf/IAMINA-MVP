'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');

const URL = 'https://iamina-review-la39twh0a-achraf-benmoussa-s-projects.vercel.app/';
const DIR = path.join(process.env.GITHUB_WORKSPACE || process.cwd(), 'd7-preview-browser-evidence');
const CERTIFIED_BACKEND = 'iamina-certified.vercel.app';

async function storageMarker(page, setValue) {
  return page.evaluate(async (value) => {
    if (value !== null) localStorage.setItem('__d7_synthetic_browser_probe__', value);
    const indexedValue = await new Promise((resolve, reject) => {
      const open = indexedDB.open('d7-synthetic-browser-probe-v1', 1);
      open.onupgradeneeded = () => {
        if (!open.result.objectStoreNames.contains('identity')) {
          open.result.createObjectStore('identity');
        }
      };
      open.onerror = () => reject(open.error);
      open.onsuccess = () => {
        const db = open.result;
        const tx = db.transaction('identity', value === null ? 'readonly' : 'readwrite');
        const store = tx.objectStore('identity');
        const req = value === null ? store.get('marker') : store.put(value, 'marker');
        req.onsuccess = () => resolve(req.result ?? null);
        req.onerror = () => reject(req.error);
        tx.oncomplete = () => db.close();
      };
    });
    return { local: localStorage.getItem('__d7_synthetic_browser_probe__'), indexedValue };
  }, setValue);
}

async function main() {
  fs.mkdirSync(DIR, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_BIN,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--enable-unsafe-swiftshader'],
  });
  const forbidden = [];
  const pageErrors = [];
  const contexts = [];
  const observe = (context, label) => {
    context.on('request', request => {
      try {
        if (new URL(request.url()).hostname === CERTIFIED_BACKEND) {
          forbidden.push({ context: label, method: request.method(), host: CERTIFIED_BACKEND });
          // Fail closed: never let a synthetic browser probe reach production.
          request.abort().catch(() => {});
        }
      } catch {}
    });
  };
  try {
    const contextA = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
    const contextB = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
    contexts.push(contextA, contextB);
    observe(contextA, 'A'); observe(contextB, 'B');
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();
    for (const [page, label] of [[pageA, 'A'], [pageB, 'B']]) {
      page.on('pageerror', e => pageErrors.push({ context: label, errorName: e?.name || 'Error' }));
      const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      assert.equal(response?.status(), 200, label + ' preview HTTP');
      await page.locator('flutter-view, flt-glass-pane').first().waitFor({ state: 'visible', timeout: 90000 });
    }

    assert.equal((await storageMarker(pageA, 'synthetic-A')).local, 'synthetic-A');
    assert.equal((await storageMarker(pageB, null)).local, null, 'Context B must not see A localStorage');
    assert.equal((await storageMarker(pageB, null)).indexedValue, null, 'Context B must not see A IndexedDB');
    assert.equal((await storageMarker(pageB, 'synthetic-B')).local, 'synthetic-B');
    assert.equal((await storageMarker(pageA, null)).local, 'synthetic-A', 'B must not modify A state');
    assert.equal((await storageMarker(pageA, null)).indexedValue, 'synthetic-A', 'B must not modify A IndexedDB');

    const bundle = await pageA.request.get(URL + 'main.dart.js', { timeout: 60000 });
    assert.equal(bundle.status(), 200, 'compiled Flutter bundle');
    const js = await bundle.text();
    assert.ok(js.length > 100000, 'Flutter bundle is unexpectedly small');
    assert.ok(!js.includes(CERTIFIED_BACKEND), 'Compiled preview references certified backend');

    const mobilePath = path.join(DIR, 'preview-390x844-context-A.png');
    const desktopPath = path.join(DIR, 'preview-1280x900-context-B.png');
    await pageA.screenshot({ path: mobilePath });
    await pageB.screenshot({ path: desktopPath });
    assert.ok(fs.statSync(mobilePath).size > 10000);
    assert.ok(fs.statSync(desktopPath).size > 10000);

    await contextA.setOffline(true);
    const offline = await pageA.evaluate(() => ({ navigatorOffline: !navigator.onLine, marker: localStorage.getItem('__d7_synthetic_browser_probe__') }));
    assert.equal(offline.navigatorOffline, true);
    assert.equal(offline.marker, 'synthetic-A');
    // This does not prove a cold, offline app startup or true two-device clinical sync.
    await contextA.setOffline(false);

    assert.equal(forbidden.length, 0, 'Forbidden certified backend network egress');
    const result = {
      proof_class: 'synthetic_two_browser_contexts_on_vercel_preview',
      preview_url: URL,
      branch: 'audit/d7-vercel-preview-offline-20261014',
      preview_commit: 'a8486c974a5f9f6a10da1d83fb77b6257b33d6b1',
      clinical_backend_connected: false,
      certified_backend_host_in_bundle: false,
      certified_backend_requests_observed: forbidden,
      distinct_localstorage_and_indexeddb: true,
      context_A_mobile: '390x844',
      context_B_desktop: '1280x900',
      offline_existing_page_kept_synthetic_marker: true,
      hard_offline_relaunch_tested: false,
      real_patient_a_to_b_to_a_tested: false,
      backend_CAS_409_tested_here: false,
      page_error_classes_observed: pageErrors,
      result: 'PASS_LIMITED_SCOPE',
    };
    fs.writeFileSync(path.join(DIR, 'proof.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result, null, 2));
  } finally {
    for (const context of contexts) await context.close().catch(() => {});
    await browser.close();
  }
}

main().catch(e => { console.error(e.stack || String(e)); process.exitCode = 1; });
