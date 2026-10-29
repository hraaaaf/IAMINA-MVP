/*
 * D19 synthetic Flutter Web first-use diagnostic.
 * Standalone Playwright/Chromium, localhost only, no credentials or patient data.
 * A non-advancing click is recorded with its console/DOM evidence, NOT inferred
 * to be a product bug without the corresponding trace.
 */
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const origin = process.env.D19_LOCAL_WEB_ORIGIN || 'http://127.0.0.1:7358';
const out = path.resolve(process.env.D19_BROWSER_EVIDENCE || 'd19-browser-evidence');
fs.mkdirSync(out, { recursive: true });
const cases = [
  { id: '390x844-en', width: 390, height: 844, locale: 'en-US' },
  { id: '768x1024-fr', width: 768, height: 1024, locale: 'fr-FR' },
  { id: '1280x900-ar', width: 1280, height: 900, locale: 'ar-MA' },
];
const allowed = /^(Continue without an account|Continuer sans compte|المتابعة بدون حساب)$/i;

async function capture(page, id, phase) {
  const filename = `${id}-${phase}.png`;
  await page.screenshot({ path: path.join(out, filename), fullPage: false });
  return filename;
}

async function runCase(browser, c) {
  const context = await browser.newContext({
    viewport: { width: c.width, height: c.height },
    locale: c.locale,
    serviceWorkers: 'block',
    deviceScaleFactor: 1,
  });
  const observed = {
    viewport: [c.width, c.height],
    locale: c.locale,
    navigation: 'NOT_TESTED',
    consoleErrors: [],
    pageErrors: [],
    externalRequestsBlocked: 0,
    accessibilityPlaceholderFound: false,
  };
  const page = await context.newPage();
  page.on('pageerror', e => observed.pageErrors.push(String(e.message).slice(0,500)));
  page.on('console', msg => {
    if (msg.type() === 'error') observed.consoleErrors.push(msg.text().slice(0,500));
  });
  await page.route('**/*', route => {
    const u = route.request().url();
    if (u.startsWith(origin) || u.startsWith('data:') || u.startsWith('blob:')) {
      return route.continue();
    }
    observed.externalRequestsBlocked++;
    return route.abort();
  });
  try {
    const response = await page.goto(origin + '/', { waitUntil: 'load', timeout: 60000 });
    observed.httpStatus = response?.status() || null;
    await page.waitForSelector('flt-glass-pane', { state: 'attached', timeout: 45000 });
    await page.waitForTimeout(2800);
    observed.beforeHash = await page.evaluate(() => location.hash);
    observed.beforeScreenshot = await capture(page, c.id, 'before');
    const placeholder = page.locator('flt-semantics-placeholder');
    observed.accessibilityPlaceholderFound = (await placeholder.count()) > 0;
    if (observed.accessibilityPlaceholderFound) {
      try {
        await placeholder.first().click({ timeout: 3500 });
        observed.accessibilityEnabledByPointer = true;
      } catch (e) {
        observed.accessibilityEnableError = String(e.message).slice(0,350);
      }
    }
    // Flutter Web CanvasKit exposes controls to the accessibility tree only
    // after semantics are enabled. Real mouse click; no JS event injection.
    const button = page.getByRole('button', { name: allowed }).first();
    try {
      await button.waitFor({ state: 'visible', timeout: 10000 });
    } catch (e) {
      observed.navigation = 'INACCESSIBLE_BUTTON';
      observed.accessibleButtons = await page.getByRole('button').allTextContents().catch(() => []);
      observed.diagnostic = String(e.message).slice(0,320);
      return observed;
    }
    observed.buttonLabel = (await button.innerText()).slice(0,120);
    try {
      await button.click({ timeout: 12000 });
      observed.clickDispatched = true;
    } catch (e) {
      observed.navigation = 'CLICK_NOT_DISPATCHED';
      observed.diagnostic = String(e.message).slice(0,500);
      return observed;
    }
    await page.waitForTimeout(5500);
    observed.afterHash = await page.evaluate(() => location.hash);
    observed.navigation = observed.afterHash !== observed.beforeHash
      ? 'ROUTE_CHANGED'
      : 'ROUTE_UNCHANGED';
    observed.errorTextVisible = await page.getByText(/échec|failed|error|فشل/i).allTextContents().catch(() => []);
    return observed;
  } catch (e) {
    observed.navigation = 'RUNTIME_ERROR';
    observed.diagnostic = String(e.stack || e.message).slice(0,1100);
    return observed;
  } finally {
    observed.afterHash = observed.afterHash || await page.evaluate(() => location.hash).catch(() => null);
    observed.afterScreenshot = await capture(page, c.id, 'after').catch(() => null);
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  let report;
  try {
    report = await Promise.all(cases.map(c => runCase(browser, c)));
  } finally {
    await browser.close();
  }
  const file = path.join(out, 'diagnostic.json');
  fs.writeFileSync(file, JSON.stringify({ origin, source: 'local isolated build, NO patient', cases: report }, null, 2));
  console.log(JSON.stringify(report.map(c => ({
    locale: c.locale, viewport: c.viewport, navigation: c.navigation,
    beforeHash: c.beforeHash, afterHash: c.afterHash,
    pageErrors: c.pageErrors.slice(0, 3), diagnostic: c.diagnostic,
  })), null, 2));
  const notAdvanced = report.filter(c => c.navigation !== 'ROUTE_CHANGED');
  if (notAdvanced.length) {
    console.error(`D19 local-first Chrome diagnostic: ${notAdvanced.length}/${report.length} viewports did not advance; details in diagnostic.json`);
    process.exitCode = 1;
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
