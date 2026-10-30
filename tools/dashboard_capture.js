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

      // A new native account has ZERO clinical measurements. Certify the
      // truthful empty-state copy instead of expecting fabricated charts.
      await page.goto('http://127.0.0.1:7358/?scroll=0', {
        waitUntil: 'domcontentloaded',
        timeout: 120000,
      });
      const emptyTitle = page.getByText('Commencez par une première mesure', { exact: true });
      await emptyTitle.waitFor({ state: 'visible', timeout: 45000 });
      const zeroClinicalCopy = page.getByText(
        'Votre tableau de bord se construira uniquement à partir de vos données réelles.',
        { exact: true },
      );
      await zeroClinicalCopy.waitFor({ state: 'visible', timeout: 10000 });

      const positions = {
        top: 0,
        mid: Math.round(height * 0.55),
        lower: Math.round(height * 1.10),
      };
      const buffers = {};
      const screenshotBytes = {};

      // One real login per viewport. Previously we reloaded for every
      // screenshot (4 logins/viewport); the 11th login hit HTTP 429.
      // Wheel within the same authenticated Flutter page instead. A true
      // empty clinical dashboard can legitimately be non-scrollable.
      await page.mouse.move(Math.round(width / 2), Math.round(height / 2));
      let previousOffset = 0;
      for (const [position, offset] of Object.entries(positions)) {
        const delta = offset - previousOffset;
        if (delta > 0) await page.mouse.wheel(0, delta);
        previousOffset = offset;
        // Each screenshot must still show the real, truthful empty state.
        await emptyTitle.waitFor({ state: 'visible', timeout: 15000 });
        await zeroClinicalCopy.waitFor({ state: 'visible', timeout: 15000 });
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
        verifiedEmptyState: true,
      };
      persist(report);

      if (errors.length) {
        throw new Error(`${name}: page errors ${JSON.stringify(errors)}`);
      }
      const loginResponses = api.filter((x) =>
        new URL(x.url).pathname === '/api/v1/auth/login');
      if (loginResponses.length !== 1 ||
          loginResponses[0].status !== 200) {
        throw new Error(
          `${name}: expected exactly one native login HTTP 200 per viewport, got ` +
          JSON.stringify(loginResponses.map((x) => x.status)),
        );
      }
      if (api.some((x) => x.status >= 400)) {
        throw new Error(
          `${name}: unexpected backend HTTP 4xx/5xx`,
        );
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
