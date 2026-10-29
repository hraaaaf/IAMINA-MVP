/*
 * D19 synthetic Flutter Web first-use diagnostic.
 * Standalone Playwright/Chromium, localhost only, no credentials or patient data.
 * A non-advancing click is recorded with its console/DOM evidence, NOT inferred
 * to be a product bug without the corresponding trace.
 */
'use strict';
const { chromium } = require('playwright');
const { PNG } = require('pngjs');
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

/* Calibrated on the same test's actual rendered screenshot, not hardcoded
 * coordinates, CSS selectors, fake events or a remote user session.
 * Flutter Web CanvasKit may render a visible button while the accessibility
 * placeholder itself is non-visible to Playwright.
 */
async function findVisibleGreenCta(page, minRunOverride) {
  const shot = PNG.sync.read(await page.screenshot({ fullPage: false }));
  const width = shot.width;
  const height = shot.height;
  const minimumRun = minRunOverride || Math.min(250, Math.round(width * 0.40));
  const rows = [];
  for (let y = 140; y < height - 40; y++) {
    let start = -1;
    let best = null;
    for (let x = 0; x <= width; x++) {
      let green = false;
      if (x < width) {
        const offset = (y * width + x) * 4;
        const [r, g, b] = shot.data.subarray(offset, offset + 3);
        green = r >= 8 && r <= 15 && g >= 105 && g <= 115 &&
          b >= 80 && b <= 94;
      }
      if (green && start === -1) start = x;
      if (!green && start !== -1) {
        const run = x - start;
        if (!best || run > best.length) best = { x: start + run / 2, length: run };
        start = -1;
      }
    }
    if (best && best.length >= minimumRun) rows.push({ x: best.x, y, width: best.length });
  }
  if (rows.length < 6) {
    throw new Error('No visible broad dark-green CTA in screenshot; pointer click refused');
  }
  const selected = rows[Math.floor(rows.length / 2)];
  return { x: Math.round(selected.x), y: selected.y, width: selected.width, sampledRows: rows.length };
}


// On the app-lock screen, the *outlined* lower button is drawn as two broad
// horizontal teal strokes. Only click when both edges are observed with
// consistent coordinates in the same real screenshot (not a guessed position).
async function findAppLockSkipOutline(page) {
  const shot = PNG.sync.read(await page.screenshot({ fullPage: false }));
  const { width, height } = shot;
  const rows = [];
  for (let y = Math.floor(height * 0.25); y < height - 20; y++) {
    let best = { len: 0, center: 0 };
    let start = -1;
    for (let x = 0; x <= width; x++) {
      let match = false;
      if (x < width) {
        const offset = (y * width + x) * 4;
        const [r, g, b] = shot.data.subarray(offset, offset + 3);
        match = r < 60 && g >= 80 && g <= 170 &&
          b >= 70 && b <= 160 && g > r * 1.3;
      }
      if (match && start < 0) start = x;
      if (!match && start >= 0) {
        const len = x - start;
        if (len > best.len) best = { len, center: start + len / 2 };
        start = -1;
      }
    }
    if (best.len >= Math.min(160, Math.round(width * 0.25))) {
      rows.push({ x: best.center, y, len: best.len });
    }
  }
  for (let i = rows.length - 1; i > 0; i--) {
    const lower = rows[i];
    for (let j = i - 1; j >= 0; j--) {
      const upper = rows[j];
      const distance = lower.y - upper.y;
      if (distance > 100) break;
      if (distance >= 30 && distance <= 65 &&
          Math.abs(lower.x - upper.x) <= 3 &&
          Math.abs(lower.len - upper.len) <= 6) {
        return { x: Math.round(lower.x), y: Math.round((upper.y + lower.y) / 2),
          top: upper.y, bottom: lower.y, width: lower.len };
      }
    }
  }
  throw new Error('App-lock outlined skip CTA was not observed; refusing ungrounded click');
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
    // Prefer accessible click. If CanvasKit has a non-visible semantics
    // placeholder, use a grounded native pointer click on the rendered CTA.
    // This distinguishes Flutter semantics limitations from a real app bug.
    const button = page.getByRole('button', { name: allowed }).first();
    if (await button.isVisible().catch(() => false)) {
      observed.clickMode = 'accessible-role';
      observed.buttonLabel = (await button.innerText()).slice(0,120);
      await button.click({ timeout: 12000 });
    } else {
      observed.clickMode = 'screenshot-grounded-pointer';
      observed.accessibilityRoleUnavailable = true;
      observed.accessibleButtons = await page.getByRole('button').allTextContents().catch(() => []);
      const cta = await findVisibleGreenCta(page);
      observed.pointerTarget = cta;
      await page.mouse.click(cta.x, cta.y);
    }
    observed.clickDispatched = true;
    await page.waitForTimeout(5500);
    observed.afterHash = await page.evaluate(() => location.hash);
    observed.navigation = observed.afterHash !== observed.beforeHash
      ? 'ROUTE_CHANGED'
      : 'ROUTE_UNCHANGED';
    observed.errorTextVisible = await page.getByText(/échec|failed|error|فشل/i).allTextContents().catch(() => []);
    if (observed.afterHash === '#/app-lock/setup') {
      const skip = await findAppLockSkipOutline(page);
      observed.appLockSkipPointer = skip;
      await page.mouse.click(skip.x, skip.y);
      await page.waitForTimeout(950);
      observed.appLockDialogScreenshot = await capture(page, c.id, 'app-lock-dialog');
      // A confirmation dialog is a privacy gate. Only a visible, sufficiently
      // wide teal primary action is acceptable. Do not bypass via script.
      try {
        const confirm = await findVisibleGreenCta(page, 90);
        observed.appLockConfirmPointer = confirm;
        await page.mouse.click(confirm.x, confirm.y);
        await page.waitForTimeout(3500);
        observed.afterConfirmHash = await page.evaluate(() => location.hash);
        observed.appLockConsent = observed.afterConfirmHash === '#/onboarding'
          ? 'ONBOARDING_REACHED'
          : 'NO_ONBOARDING_TRANSITION';
      } catch (error) {
        observed.appLockConsent = 'CONFIRM_CTA_UNREACHABLE';
        observed.appLockConsentDiagnostic = String(error.message).slice(0,430);
      }
    }
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
    appLockConsent: c.appLockConsent, afterConfirmHash: c.afterConfirmHash,
  })), null, 2));
  const notAdvanced = report.filter(c => c.navigation !== 'ROUTE_CHANGED' || c.appLockConsent !== 'ONBOARDING_REACHED');
  if (notAdvanced.length) {
    console.error(`D19 local-first Chrome diagnostic: ${notAdvanced.length}/${report.length} viewports did not advance; details in diagnostic.json`);
    process.exitCode = 1;
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
