const { chromium } = require('playwright');
const fs = require('fs');

const routes = [
  ['dashboard', '/dashboard'],
  ['journal', '/journal'],
  ['summary', '/summary'],
  ['add', '/ajouter'],
  ['medications', '/medications'],
  ['reminders', '/reminders'],
  ['profile', '/profile'],
  ['importer', '/importer'],
];
const viewports = [
  ['mobile', 390, 844],
  ['small', 360, 560],
];
const locales = [['fr', 'fr-FR'], ['ar', 'ar-MA']];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const report = [];
  for (const [lang, locale] of locales) {
    const context = await browser.newContext({ locale });
    const seed = await context.newPage();
    await seed.setViewportSize({ width: 390, height: 844 });
    await seed.goto(`http://127.0.0.1:4173/?audit=ux12&lang=${lang}#/importer`, { waitUntil: 'networkidle' });
    await seed.waitForTimeout(1800);
    const load = seed.getByRole('button', { name: /Charger|Load|تحميل/i });
    if (await load.count()) {
      try {
        await load.first().click();
        await seed.waitForTimeout(1400);
      } catch (_) {}
    }
    await seed.close();

    for (const [vp, width, height] of viewports) {
      for (const [name, route] of routes) {
        const page = await context.newPage();
        await page.setViewportSize({ width, height });
        const errors = [];
        page.on('pageerror', e => errors.push(String(e)));
        await page.goto(`http://127.0.0.1:4173/?audit=ux12&lang=${lang}#${route}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(name === 'summary' ? 3500 : 1800);
        const views = await page.locator('flutter-view').count();
        const file = `/tmp/ux12-captures/${vp}-${lang}__${name}.png`;
        await page.screenshot({ path: file, fullPage: false });
        report.push({ lang, vp, width, height, name, route, views, errors });
        await page.close();
      }
    }
    await context.close();
  }
  await browser.close();
  fs.writeFileSync('/tmp/ux12-captures/report.json', JSON.stringify(report, null, 2));
})().catch(e => {
  console.error(e);
  process.exit(1);
});
