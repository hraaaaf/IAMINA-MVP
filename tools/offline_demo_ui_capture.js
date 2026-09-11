const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outputDir = 'offline-demo-ui-cert';
const reportPath = path.join(outputDir, 'browser-report.json');
const matrix = [
  ['mobile', 390, 844],
  ['tablet', 768, 1024],
  ['desktop', 1280, 900],
];
const minScreenshotBytes = 15000;

fs.mkdirSync(outputDir, { recursive: true });

const persist = (report) =>
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

async function loginDemo(page) {
  await page.goto('http://127.0.0.1:7359/#/login', {
    waitUntil: 'domcontentloaded',
    timeout: 120000,
  });
  const demo = page.getByText('Accès démo', { exact: true });
  await demo.waitFor({ state: 'visible', timeout: 60000 });
  await demo.click();
  await page.waitForURL(/#\/dashboard/, { timeout: 60000 });
  await page.waitForTimeout(1400);
}

(async () => {
  const report = {};
  for (const [name, width, height] of matrix) {
    const browser = await chromium.launch({ headless: true });
    try {
      const ctx = await browser.newContext({
        viewport: { width, height },
        deviceScaleFactor: 1,
        locale: 'fr-FR',
      });
      const page = await ctx.newPage();
      const errors = [];
      const consoleErrors = [];
      page.on('pageerror', (error) => errors.push(String(error)));
      page.on('console', (message) => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });

      await loginDemo(page);

      const trendHeading = page.getByText('Tendance', { exact: true }).first();
      await trendHeading.waitFor({ state: 'visible', timeout: 30000 });
      await trendHeading.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      const dashboardPath = path.join(
        outputDir,
        `dashboard-trend-${name}-${width}x${height}.png`,
      );
      const dashboardBuffer = await page.screenshot({ path: dashboardPath });

      // Use a hash-only navigation so the in-memory offline demo session remains
      // authenticated even when the desktop sidebar has collapsed to icon-only mode.
      await page.evaluate(() => {
        window.location.hash = '#/summary';
      });
      await page.waitForURL(/#\/summary/, { timeout: 30000 });
      const reportsHeading = page.getByText('Rapport de vos mesures', {
        exact: true,
      });
      await reportsHeading.waitFor({ state: 'visible', timeout: 30000 });
      await page.waitForTimeout(500);
      const reportsPath = path.join(
        outputDir,
        `reports-${name}-${width}x${height}.png`,
      );
      const reportsBuffer = await page.screenshot({ path: reportsPath });

      report[name] = {
        viewport: { width, height },
        dashboardBytes: dashboardBuffer.length,
        reportsBytes: reportsBuffer.length,
        errors,
        consoleErrors,
      };
      persist(report);

      if (errors.length) {
        throw new Error(`${name}: page errors ${JSON.stringify(errors)}`);
      }
      if (dashboardBuffer.length < minScreenshotBytes) {
        throw new Error(`${name}: suspicious dashboard capture`);
      }
      if (reportsBuffer.length < minScreenshotBytes) {
        throw new Error(`${name}: suspicious reports capture`);
      }

      await ctx.close();
    } finally {
      await browser.close();
    }
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
