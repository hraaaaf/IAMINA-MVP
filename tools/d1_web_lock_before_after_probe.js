// D1 P0. Synthetic visual diff only: never touches patient data or remote API.
// Both viewports and locale are identical BEFORE/AFTER. Flutter widget tests
// are the authoritative behavioral assertion for the missing Web opt-out CTA.
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const baseBefore = process.env.D1_BEFORE_URL || 'http://localhost:7381/';
const baseAfter = process.env.D1_AFTER_URL || 'http://localhost:7382/';
const dir = path.resolve(process.env.D1_VISUAL_DIR || 'd1-web-lock-visual');
const fixtures = [
  { w: 390, h: 844, locale: 'fr' },
  { w: 430, h: 932, locale: 'ar' },
  { w: 768, h: 1024, locale: 'fr' },
  { w: 1280, h: 900, locale: 'ar' },
];
fs.mkdirSync(dir, { recursive: true });
const url = (base, locale) =>
  `${base}?audit=visual-cert&lang=${locale}&appLockPreview=supported#/app-lock/setup`;
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

(async () => {
  const browser = await chromium.launch({headless: true});
  const report = [];
  try {
    for (const spec of fixtures) {
      const captures = [];
      for (const [label, base] of [['before',baseBefore], ['after',baseAfter]]) {
        const context = await browser.newContext({
          viewport: { width: spec.w, height: spec.h },
          locale: spec.locale === 'ar' ? 'ar-MA' : 'fr-FR',
          deviceScaleFactor: 1,
          serviceWorkers: 'block',
        });
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        await page.goto(url(base,spec.locale), {waitUntil:'load',timeout:60000});
        await page.waitForSelector('flt-glass-pane', {state:'attached',timeout:60000});
        await page.waitForTimeout(2700);
        const bytes = await page.screenshot({fullPage:false});
        const filename = `${label}-${spec.locale}-${spec.w}x${spec.h}.png`;
        fs.writeFileSync(path.join(dir, filename), bytes);
        const size = await page.evaluate(() => ({
          width: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body?.scrollWidth || 0,
        }));
        if (errors.length) throw new Error(`${filename} browser errors: ${errors.join(' | ')}`);
        if (size.scrollWidth > size.width || size.bodyWidth > size.width) {
          throw new Error(`${filename} horizontal overflow`);
        }
        captures.push({label,filename,sha256:hash(bytes),size});
        await context.close();
      }
      if (captures[0].sha256 === captures[1].sha256) {
        throw new Error(`No visible difference in first-use app-lock at ${spec.locale} ${spec.w}x${spec.h}`);
      }
      report.push({locale:spec.locale,width:spec.w,height:spec.h,before:captures[0],after:captures[1]});
    }
    fs.writeFileSync(path.join(dir,'report.json'), JSON.stringify({verified:true,report},null,2));
    console.log('D1 P0 WEB LOCK VISUAL DIFF PASS',report.length);
  } finally {
    await browser.close();
  }
})().catch(e => {console.error(e);process.exitCode=1;});
