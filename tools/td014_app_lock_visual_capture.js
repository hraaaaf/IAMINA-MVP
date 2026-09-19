const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const outDir = path.resolve(process.env.TD014_VISUAL_OUT || 'td014-app-lock-visual');
const beforeBase = process.env.BEFORE_URL || 'http://localhost:7361/';
const afterBase = process.env.AFTER_URL || 'http://localhost:7362/';
const viewports = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
];

fs.mkdirSync(outDir, { recursive: true });

const sha256 = (filePath) =>
  crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');

const withAuditRoute = (base, route, extra = '') => {
  const separator = base.includes('?') ? '&' : '?';
  return `${base}${separator}audit=visual-cert&lang=fr${extra}#${route}`;
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const report = {};
  try {
    for (const viewport of viewports) {
      report[viewport.name] = {};
      const targets = [
        { name: 'before', url: beforeBase },
        {
          name: 'setup',
          url: withAuditRoute(
            afterBase,
            '/app-lock/setup',
            '&appLockPreview=supported',
          ),
        },
        {
          name: 'locked',
          url: withAuditRoute(afterBase, '/app-lock/unlock'),
        },
        {
          name: 'recovery',
          url: withAuditRoute(
            afterBase,
            '/app-lock/unlock',
            '&appLockPreview=recovery',
          ),
        },
      ];

      for (const target of targets) {
        const context = await browser.newContext({
          viewport: { width: viewport.width, height: viewport.height },
          locale: 'fr-FR',
          deviceScaleFactor: 1,
        });
        const page = await context.newPage();
        const pageErrors = [];
        page.on('pageerror', (error) => pageErrors.push(error.message));

        await page.goto(target.url, { waitUntil: 'load', timeout: 60000 });
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
        const horizontalOverflow =
          metrics.scrollWidth > metrics.innerWidth ||
          metrics.bodyWidth > metrics.innerWidth;

        report[viewport.name][target.name] = {
          file: path.basename(file),
          sha256: sha256(file),
          horizontalOverflow,
          pageErrors,
          ...metrics,
        };

        if (horizontalOverflow && target.name !== 'before') {
          throw new Error(`${target.name} has horizontal overflow at ${viewport.name}`);
        }
        if (pageErrors.length > 0 && target.name !== 'before') {
          throw new Error(`${target.name} emitted page errors at ${viewport.name}: ${pageErrors.join('; ')}`);
        }
        await context.close();
      }

      const { before, setup, locked, recovery } = report[viewport.name];
      if (before.sha256 === setup.sha256) {
        throw new Error(`BEFORE and setup are pixel-identical at ${viewport.name}`);
      }
      if (setup.sha256 === locked.sha256) {
        throw new Error(`Setup and locked states are pixel-identical at ${viewport.name}`);
      }
      if (locked.sha256 === recovery.sha256) {
        throw new Error(`Locked and recovery states are pixel-identical at ${viewport.name}`);
      }
    }

    fs.writeFileSync(
      path.join(outDir, 'visual-report.json'),
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
