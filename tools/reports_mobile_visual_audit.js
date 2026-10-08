const {chromium} = require('playwright');
const fs = require('fs');

const base = process.env.AUDIT_URL || 'http://127.0.0.1:7367';
const out = process.env.AUDIT_OUT || 'reports-mobile-visual-proof';
fs.mkdirSync(out, {recursive: true});
const sleep = n => new Promise(resolve => setTimeout(resolve, n));

(async () => {
  const browser = await chromium.launch({
    headless: true, args: ['--force-renderer-accessibility'],
  });
  const observations = [];
  try {
    for (const [width, height] of [[390, 844], [768, 1024], [1280, 900]]) {
      const context = await browser.newContext({
        viewport: {width, height},
        locale: 'fr-FR',
        deviceScaleFactor: 1,
        serviceWorkers: 'block',
        colorScheme: 'light',
      });
      try {
        const page = await context.newPage();
        const url = base + '/?surface=reports-local&seed=1';
        await page.goto(url, {waitUntil:'domcontentloaded',timeout:30000});
        await sleep(10000);
        const placeholder = page.locator('flt-semantics-placeholder');
        if (await placeholder.count()) {
          await placeholder.first().focus();
          await page.keyboard.press('Enter');
          await sleep(700);
        }
        const capture = async suffix => page.screenshot({
          path: out+'/reports-'+suffix+'-'+width+'x'+height+'.png',
          fullPage:false,
        });
        await capture('first-fold');
        const firstSemantics = await page.locator('flt-semantics')
          .evaluateAll(xs => xs.map(x => ({
            label:x.getAttribute('aria-label'),
            text:x.textContent?.trim()?.slice(0,160),
          }))).catch(() => []);
        await page.mouse.move(width/2, height/2);
        await page.mouse.wheel(0, 570);
        await sleep(1200);
        await capture('scrolled');

        const semantics = await page.locator('flt-semantics')
          .evaluateAll(xs => xs.map(x => ({
            label:x.getAttribute('aria-label'),
            text:x.textContent?.trim()?.slice(0,160),
          }))).catch(() => []);
        const joined = [...firstSemantics, ...semantics]
          .flatMap(x => [x.label,x.text])
          .filter(Boolean).join(' ');
        observations.push({
          width, height, url:page.url(),
          observedTitle:joined.includes('Rapport de vos mesures'),
          observedDistribution:joined.includes('Répartition des mesures'),
          semantics:joined.slice(0,2200),
        });
      } finally {
        await context.close();
      }
    }
    const report={ok:true,mode:'Flutter isolated browser seeded demo data',
      viewports:observations};
    fs.writeFileSync(out+'/result.json',JSON.stringify(report,null,2));
    // Screen proof is meaningful only if the actual report rendered at least once.
    if (!observations.some(x => x.observedTitle)) {
      throw new Error('Report title missing from all browser semantics snapshots');
    }
    console.log(JSON.stringify(observations.map(x => ({
      size:x.width+'x'+x.height,
      report:x.observedTitle,
      distribution:x.observedDistribution,
    }))));
  } finally {
    await browser.close();
  }
})().catch(err => {
  fs.writeFileSync(out+'/failure.txt',String(err.stack || err));
  console.error(err);
  process.exit(1);
});
