import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const baseUrl = process.env.TARGET_URL || 'http://127.0.0.1:4173';
const expectedCommit = 'ffaeae75d64c69359ddcc41cd688ae232097128f';
const outDir = process.env.OUTPUT_DIR || 'p0-certification-evidence';
fs.mkdirSync(outDir, { recursive: true });

const audit = {
  sourceCommit: expectedCommit,
  targetUrl: baseUrl,
  startedAt: new Date().toISOString(),
  pages: [],
  consoleErrors: [],
  pageErrors: [],
  requestFailures: [],
  assertions: [],
  authenticatedDemo: false,
  arabicRtlConfirmed: false,
};

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1100 },
  deviceScaleFactor: 1,
  locale: 'fr-FR',
  colorScheme: 'light',
});
const page = await context.newPage();
let uiLanguage = 'fr';

const corsHeaders = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
  'access-control-allow-headers': '*',
  'content-type': 'application/json; charset=utf-8',
};

await page.route('http://localhost:8000/**', async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  const pathname = url.pathname.replace(/\/+$/, '');
  if (request.method() === 'OPTIONS') {
    await route.fulfill({ status: 204, headers: corsHeaders, body: '' });
    return;
  }
  if (pathname === '/api/v1/profile/locale') {
    await route.fulfill({
      status: 200,
      headers: corsHeaders,
      body: JSON.stringify({
        explicit: { ui_language: uiLanguage },
        resolved: { ui_language: uiLanguage, response_language: uiLanguage },
      }),
    });
    return;
  }
  if (pathname === '/api/v1/demo/seed') {
    await route.fulfill({ status: 200, headers: corsHeaders, body: '{}' });
    return;
  }
  if (pathname === '/api/v1/account/modules') {
    await route.fulfill({
      status: 200,
      headers: corsHeaders,
      body: JSON.stringify({ modules: ['diabetes'], active_modules: ['diabetes'] }),
    });
    return;
  }
  if (pathname.includes('/api/v1/kpis')) {
    await route.fulfill({ status: 404, headers: corsHeaders, body: '{}' });
    return;
  }
  if (pathname === '/api/v1/ai/summary') {
    await route.fulfill({ status: 503, headers: corsHeaders, body: '{}' });
    return;
  }
  await route.fulfill({ status: 200, headers: corsHeaders, body: '{}' });
});

page.on('console', (msg) => {
  if (msg.type() === 'error') audit.consoleErrors.push(msg.text());
});
page.on('pageerror', (error) => audit.pageErrors.push(String(error)));
page.on('requestfailed', (request) => {
  const failure = request.failure();
  audit.requestFailures.push({ url: request.url(), error: failure?.errorText || 'unknown' });
});

async function activateSemantics() {
  await page.evaluate(() => {
    const placeholder = document.querySelector('flt-semantics-placeholder');
    if (placeholder instanceof HTMLElement) placeholder.click();
  }).catch(() => {});
  await page.waitForTimeout(800);
}

async function waitForFlutter() {
  await page.waitForSelector('flutter-view, flt-glass-pane', { timeout: 30000 });
  await page.waitForTimeout(4500);
  await activateSemantics();
}

async function shot(name, fullPage = true) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage });
  audit.pages.push({ name, file, url: page.url(), viewport: page.viewportSize() });
}

async function assert(name, condition, details = '') {
  audit.assertions.push({ name, pass: Boolean(condition), details });
}

async function openHash(route, settleMs = 2500) {
  await page.evaluate((value) => {
    window.location.hash = value;
  }, route);
  await page.waitForTimeout(settleMs);
  await activateSemantics();
}

async function captureRoute(route, name, settleMs = 2500) {
  await openHash(route, settleMs);
  const bodyText = await page.locator('body').innerText().catch(() => '');
  const renderError = bodyText.includes('Une erreur de rendu est survenue');
  await assert(`${name}: no Flutter render error`, !renderError, renderError ? bodyText.slice(0, 500) : '');
  await shot(name);
}

try {
  const buildResponse = await context.request.get(`${baseUrl}/certified-build.json`);
  const buildText = await buildResponse.text();
  await assert('certified-build marker reachable', buildResponse.ok(), `${buildResponse.status()} ${buildText}`);
  await assert('certified-build source commit matches', buildText.includes(expectedCommit), buildText);

  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await waitForFlutter();
  await shot('01-login-desktop');

  const loginText = await page.locator('body').innerText().catch(() => '');
  await assert('login screen rendered', /IAmina/i.test(loginText), loginText.slice(0, 500));

  const demoPatterns = [/Accès démo/i, /Demo access/i, /وصول تجريبي/i];
  let clickedDemo = false;
  for (const pattern of demoPatterns) {
    const locator = page.getByText(pattern).last();
    if (await locator.isVisible({ timeout: 1200 }).catch(() => false)) {
      await locator.click();
      clickedDemo = true;
      break;
    }
  }
  await assert('demo action discoverable', clickedDemo);
  if (clickedDemo) {
    await page.waitForTimeout(12000);
    await activateSemantics();
  }

  const afterDemoText = await page.locator('body').innerText().catch(() => '');
  audit.authenticatedDemo = !/Accès démo|Demo access|وصول تجريبي/i.test(afterDemoText) && /Accueil|Tableau|Journal|IAmina/i.test(afterDemoText);
  await assert('demo session reaches application shell', audit.authenticatedDemo, afterDemoText.slice(0, 1200));

  if (audit.authenticatedDemo) {
    await captureRoute('/dashboard', '02-dashboard-desktop');
    await captureRoute('/summary', '03-summary-desktop', 12000);
    await captureRoute('/journal', '04-journal-desktop');
    await captureRoute('/importer', '05-importer-desktop');
    await captureRoute('/pulper', '06-document-import-desktop');
    await captureRoute('/profile', '07-profile-desktop');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(1200);
    await captureRoute('/dashboard', '08-dashboard-mobile-390');
    await captureRoute('/summary', '09-summary-mobile-390', 12000);
    await captureRoute('/journal', '10-journal-mobile-390');
    await captureRoute('/importer', '11-importer-mobile-390');
    await captureRoute('/pulper', '12-document-import-mobile-390');
    await captureRoute('/profile', '13-profile-mobile-390');

    uiLanguage = 'ar';
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await waitForFlutter();
    await openHash('/dashboard');
    const arabicText = await page.locator('body').innerText().catch(() => '');
    audit.arabicRtlConfirmed = /الرئيسية|الإعدادات|اليومية|استيراد|لوحة/.test(arabicText);
    await assert('Arabic application shell rendered', audit.arabicRtlConfirmed, arabicText.slice(0, 700));
    await shot('14-dashboard-arabic-rtl-mobile');
    await captureRoute('/importer', '15-importer-arabic-rtl-mobile');
    await captureRoute('/profile', '16-profile-arabic-rtl-mobile');
  }
} catch (error) {
  audit.fatalError = String(error?.stack || error);
  try { await shot('99-fatal-state'); } catch {}
} finally {
  audit.finishedAt = new Date().toISOString();
  audit.passedAssertions = audit.assertions.filter((item) => item.pass).length;
  audit.failedAssertions = audit.assertions.filter((item) => !item.pass).length;
  fs.writeFileSync(path.join(outDir, 'audit.json'), JSON.stringify(audit, null, 2));
  await browser.close();
}

if (audit.failedAssertions > 0 || audit.fatalError) process.exitCode = 2;
