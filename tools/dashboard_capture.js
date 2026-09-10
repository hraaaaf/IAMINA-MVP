const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const reportPath = 'dashboard-visual-cert/browser-report.json';
const persist = (report) =>
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
const matrix = [
  ['mobile', 390, 844],
  ['tablet', 768, 1024],
  ['desktop', 1280, 900],
];
const minScreenshotBytes = 15000;

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
      const api = [];
      page.on('pageerror', (e) => {
        errors.push({ message: String(e), stack: e.stack || null });
        report[name] = { url: page.url(), errors, consoleErrors, api };
        persist(report);
      });
      page.on('console', (m) => {
        if (m.type() === 'error') {
          consoleErrors.push(m.text());
          report[name] = { url: page.url(), errors, consoleErrors, api };
          persist(report);
        }
      });
      page.on('response', (r) => {
        if (r.url().includes('/api/')) {
          api.push({ url: r.url(), status: r.status() });
        }
      });

      const positions = {
        top: 0,
        mid: Math.round(height * 0.55),
        lower: Math.round(height * 1.10),
      };
      const buffers = {};
      const screenshotBytes = {};

      for (const [position, offset] of Object.entries(positions)) {
        const dashboardReady = page.waitForResponse(
          (r) =>
            r.url().includes('/api/v1/companion/overview') &&
            r.status() >= 200 &&
            r.status() < 300,
          { timeout: 45000 },
        );
        await page.goto(`http://127.0.0.1:7358/?scroll=${offset}`, {
          waitUntil: 'domcontentloaded',
          timeout: 120000,
        });
        await dashboardReady;
        await page.waitForTimeout(1600);
        const screenshotPath = path.join(
          'dashboard-visual-cert',
          `${name}-${position}-${width}x${height}.png`,
        );
        const buffer = await page.screenshot({ path: screenshotPath });
        buffers[position] = buffer;
        screenshotBytes[position] = buffer.length;
      }

      const byteDuplicateCaptures = {
        topMid: buffers.top.equals(buffers.mid),
        midLower: buffers.mid.equals(buffers.lower),
        topLower: buffers.top.equals(buffers.lower),
      };
      report[name] = {
        url: page.url(),
        errors,
        consoleErrors,
        api,
        requestedScrollOffsets: positions,
        screenshotBytes,
        byteDuplicateCaptures,
      };
      persist(report);

      if (errors.length) {
        throw new Error(`${name}: page errors ${JSON.stringify(errors)}`);
      }
      if (api.some((x) => x.status >= 500)) {
        throw new Error(`${name}: backend 5xx`);
      }
      if (
        Object.values(screenshotBytes).some(
          (bytes) => bytes < minScreenshotBytes,
        )
      ) {
        throw new Error(
          `${name}: blank/suspicious capture ${JSON.stringify(screenshotBytes)}`,
        );
      }
      await ctx.close();
    } finally {
      await browser.close();
    }
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
