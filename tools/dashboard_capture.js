const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const reportPath = 'dashboard-visual-cert/browser-report.json';
const persist = (report) => fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
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
        if (r.url().includes('/api/')) api.push({ url: r.url(), status: r.status() });
      });

      const dashboardReady = page.waitForResponse(
        (r) => r.url().includes('/api/v1/companion/overview') && r.status() >= 200 && r.status() < 300,
        { timeout: 45000 },
      );
      await page.goto('http://127.0.0.1:7358/', {
        waitUntil: 'domcontentloaded',
        timeout: 120000,
      });
      await dashboardReady;
      await page.waitForTimeout(2000);

      const topPath = path.join('dashboard-visual-cert', `${name}-top-${width}x${height}.png`);
      const top = await page.screenshot({ path: topPath });

      // Flutter Web owns scrolling inside its rendering surface. A browser
      // wheel event is not a reliable proof that the Flutter Scrollable moved.
      // Use Chrome's native synthesized touch gesture instead, starting over
      // the non-interactive left padding of the Dashboard content.
      const cdp = await page.context().newCDPSession(page);
      const gestureX = width >= 700 ? 110 : 24;
      const gestureY = Math.round(height * 0.72);
      const gestureDistance = -Math.round(height * 0.55);
      const scrollOnce = async () => {
        await cdp.send('Input.synthesizeScrollGesture', {
          x: gestureX,
          y: gestureY,
          xDistance: 0,
          yDistance: gestureDistance,
          speed: 1000,
          preventFling: true,
          gestureSourceType: 'touch',
        });
        await page.waitForTimeout(900);
      };

      await scrollOnce();
      const midPath = path.join('dashboard-visual-cert', `${name}-mid-${width}x${height}.png`);
      const mid = await page.screenshot({ path: midPath });

      await scrollOnce();
      const lowerPath = path.join('dashboard-visual-cert', `${name}-lower-${width}x${height}.png`);
      const lower = await page.screenshot({ path: lowerPath });

      const screenshotBytes = { top: top.length, mid: mid.length, lower: lower.length };
      const byteDuplicateCaptures = {
        topMid: top.equals(mid),
        midLower: mid.equals(lower),
        topLower: top.equals(lower),
      };
      report[name] = {
        url: page.url(),
        errors,
        consoleErrors,
        api,
        gesture: {
          method: 'Input.synthesizeScrollGesture',
          source: 'touch',
          x: gestureX,
          y: gestureY,
          yDistance: gestureDistance,
        },
        screenshotBytes,
        byteDuplicateCaptures,
      };
      persist(report);

      if (errors.length) throw new Error(`${name}: page errors ${JSON.stringify(errors)}`);
      if (api.some((x) => x.status >= 500)) throw new Error(`${name}: backend 5xx`);
      if (Object.values(screenshotBytes).some((bytes) => bytes < minScreenshotBytes)) {
        throw new Error(`${name}: blank/suspicious capture ${JSON.stringify(screenshotBytes)}`);
      }
      await cdp.detach();
      await ctx.close();
    } finally {
      await browser.close();
    }
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
