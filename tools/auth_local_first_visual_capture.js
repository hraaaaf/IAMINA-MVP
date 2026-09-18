const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const outDir = path.resolve(process.env.AUTH_VISUAL_OUT || 'auth-local-first-visual');
const beforeUrl = process.env.BEFORE_URL || 'http://127.0.0.1:7357/';
const afterUrl = process.env.AFTER_URL || 'http://127.0.0.1:7358/';
const viewports = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
];

fs.mkdirSync(outDir, { recursive: true });

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const report = {};
  try {
    for (const viewport of viewports) {
      report[viewport.name] = {};
      for (const target of [
        { name: 'before', url: beforeUrl },
        { name: 'after', url: afterUrl },
      ]) {
        const context = await browser.newContext({
          viewport: { width: viewport.width, height: viewport.height },
          locale: 'fr-FR',
          deviceScaleFactor: 1,
        });
        const page = await context.newPage();
        await page.goto(target.url, { waitUntil: 'load', timeout: 60000 });

        // Flutter Web keeps flt-glass-pane hidden in CanvasKit/semantics modes.
        // Attachment proves the engine mounted; visibility is not a valid readiness signal.
        await page.waitForSelector('flt-glass-pane', {
          state: 'attached',
          timeout: 60000,
        });
        await page.waitForTimeout(4000);

        const file = path.join(
          outDir,
          `${target.name}-${viewport.name}-${viewport.width}x${viewport.height}.png`,
        );
        await page.screenshot({ path: file, fullPage: false });

        const metrics = await page.evaluate(() => ({
          href: window.location.href,
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          scrollWidth: document.documentElement.scrollWidth,
          scrollHeight: document.documentElement.scrollHeight,
          bodyWidth: document.body?.scrollWidth || 0,
          bodyHeight: document.body?.scrollHeight || 0,
        }));
        report[viewport.name][target.name] = {
          file: path.basename(file),
          sha256: sha256(file),
          horizontalOverflow:
            metrics.scrollWidth > metrics.innerWidth || metrics.bodyWidth > metrics.innerWidth,
          ...metrics,
        };
        await context.close();
      }

      report[viewport.name].pixelIdentical =
        report[viewport.name].before.sha256 ===
        report[viewport.name].after.sha256;

      // Pixel identity is a valid certification result for behavior-only auth
      // changes. The visual gate protects geometry/overflow; it must not require
      // an intentional visual delta where none is expected.
      if (report[viewport.name].after.horizontalOverflow) {
        throw new Error(`AFTER has horizontal overflow at ${viewport.name}`);
      }
    }

    fs.writeFileSync(
      path.join(outDir, 'browser-report.json'),
      JSON.stringify(report, null, 2),
    );
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
