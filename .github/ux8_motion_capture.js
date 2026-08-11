const { chromium } = require('playwright');
const fs = require('fs');

const routes = ['dashboard', 'journal', 'importer', 'profile', 'summary'];
const locales = [
  { name: 'fr', locale: 'fr-FR' },
  { name: 'ar', locale: 'ar-MA' },
];
const modes = [
  { name: 'normal', reducedMotion: 'no-preference' },
  { name: 'reduced', reducedMotion: 'reduce' },
];

(async () => {
  fs.mkdirSync('ux8-motion/videos', { recursive: true });
  fs.mkdirSync('ux8-motion/stills', { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = [];

  for (const lang of locales) {
    for (const mode of modes) {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        locale: lang.locale,
        timezoneId: 'Africa/Casablanca',
        reducedMotion: mode.reducedMotion,
        recordVideo: {
          dir: 'ux8-motion/videos',
          size: { width: 390, height: 844 },
        },
      });
      const page = await context.newPage();
      const pageErrors = [];
      page.on('pageerror', error => pageErrors.push(String(error)));
      const base = `http://127.0.0.1:8080/?audit=visual-cert&lang=${lang.name}`;
      await page.goto(`${base}#/dashboard`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.locator('flutter-view').waitFor({ state: 'attached', timeout: 30000 });
      await page.waitForTimeout(5000);

      for (let i = 0; i < routes.length; i++) {
        const route = routes[i];
        if (i > 0) {
          await page.evaluate(r => { window.location.hash = `#/${r}`; }, route);
          await page.waitForTimeout(60);
          await page.screenshot({
            path: `ux8-motion/stills/${lang.name}-${mode.name}-${route}-mid.png`,
          });
          await page.waitForTimeout(mode.name === 'normal' ? 500 : 180);
        }
        const finalUrl = page.url();
        if (!finalUrl.includes(`#/${route}`)) {
          throw new Error(`${lang.name}-${mode.name}-${route}: wrong route ${finalUrl}`);
        }
        await page.screenshot({
          path: `ux8-motion/stills/${lang.name}-${mode.name}-${route}-final.png`,
        });
        report.push({
          lang: lang.name,
          mode: mode.name,
          route,
          finalUrl,
          flutterViews: await page.locator('flutter-view').count(),
          pageErrors: [...pageErrors],
        });
      }

      const video = page.video();
      await page.close();
      const videoPath = await video.path();
      const target = `ux8-motion/videos/${lang.name}-${mode.name}.webm`;
      fs.renameSync(videoPath, target);
      await context.close();
    }
  }

  fs.writeFileSync('ux8-motion/report.json', JSON.stringify(report, null, 2));
  fs.writeFileSync('ux8-motion/source-sha.txt', '9f8bd4e6e4427e6ec6d7d8dced9936b5abec3ccc\n');
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
