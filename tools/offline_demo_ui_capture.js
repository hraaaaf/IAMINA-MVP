const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outputDir = 'offline-demo-ui-cert';
const reportPath = path.join(outputDir, 'browser-report.json');
const matrix = [
  ['mobile', 390, 844, 620],
  ['tablet', 768, 1024, 500],
  ['desktop', 1280, 900, 360],
];
const minScreenshotBytes = 15000;
const auditBase = 'http://127.0.0.1:7359/?audit=visual-cert&lang=fr';

fs.mkdirSync(outputDir, { recursive: true });

const persist = (report) =>
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

async function openAuditRoute(page, route) {
  await page.goto(`${auditBase}#${route}`, {
    waitUntil: 'domcontentloaded',
    timeout: 120000,
  });
  await page.waitForURL(new RegExp(`#${route.replace('/', '\\/')}$`), {
    timeout: 60000,
  });
  await page.waitForTimeout(1800);
}

(async () => {
  const report = {};
  for (const [name, width, height, trendScroll] of matrix) {
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

      await openAuditRoute(page, '/dashboard');
      await page.mouse.wheel(0, trendScroll);
      await page.waitForTimeout(700);
      const dashboardPath = path.join(
        outputDir,
        `dashboard-trend-${name}-${width}x${height}.png`,
      );
      const dashboardBuffer = await page.screenshot({ path: dashboardPath });

      await page.evaluate(() => {
        window.location.hash = '#/summary';
      });
      await page.waitForURL(/#\/summary$/, { timeout: 30000 });
      await page.waitForTimeout(1400);
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
