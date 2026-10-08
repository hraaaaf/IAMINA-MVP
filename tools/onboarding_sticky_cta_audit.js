const {chromium} = require('playwright');
const fs = require('fs');

const base = process.env.AUDIT_URL || 'http://127.0.0.1:7366';
const out = process.env.AUDIT_OUT || 'onboarding-sticky-proof';
fs.mkdirSync(out, {recursive: true});
const sleep = n => new Promise(resolve => setTimeout(resolve, n));

async function enableSemantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  if (await placeholder.count()) {
    await placeholder.first().focus();
    await page.keyboard.press('Enter');
    await sleep(350);
  }
}

async function choose(page, label) {
  const candidates = [
    page.getByRole('checkbox', {name: label, exact: true}),
    page.getByRole('button', {name: label, exact: false}),
    page.getByRole('radio', {name: label, exact: false}),
    page.getByText(label, {exact: true}),
  ];
  for (let attempt = 0; attempt < 45; attempt++) {
    for (const locator of candidates) {
      const count = await locator.count();
      for (let index = 0; index < count; index++) {
        const el = locator.nth(index);
        if (!await el.isVisible().catch(() => false)) continue;
        if (!await el.isEnabled().catch(() => false)) continue;
        await el.scrollIntoViewIfNeeded().catch(() => {});
        await el.click({timeout: 2500});
        await sleep(350);
        return;
      }
    }
    await sleep(300);
  }
  throw new Error('Cannot select onboarding choice: ' + label);
}

(async () => {
  const browser = await chromium.launch({
    headless: true, args: ['--force-renderer-accessibility'],
  });
  const results = [];
  try {
    for (const [width, height] of [[390,844], [768,1024], [1280,900]]) {
      const ctx = await browser.newContext({
        viewport: {width, height}, locale: 'fr-FR',
        deviceScaleFactor: 1, colorScheme: 'light', serviceWorkers: 'block',
      });
      try {
        const page = await ctx.newPage();
        await page.goto(base + '/?surface=onboarding&seed=0',
          {waitUntil: 'domcontentloaded', timeout: 30000});
        await sleep(7000);
        await enableSemantics(page);
        await page.screenshot({
          path: out + '/debug-onboarding-initial-' + width + 'x' + height + '.png',
          fullPage: false,
        });
        const sem = await page.locator('flt-semantics').evaluateAll(elements =>
          elements.map(el => ({
            label: el.getAttribute('aria-label'),
            text: el.textContent?.trim()?.slice(0, 200),
            outer: el.outerHTML.slice(0, 450),
          })),
        ).catch(() => []);
        const placeholderCount = await page.locator('flt-semantics-placeholder').count();
        const body = await page.locator('body').innerText().catch(() => '');
        fs.writeFileSync(out + '/debug-dom-' + width + 'x' + height + '.json',
          JSON.stringify({
            url: page.url(), placeholderCount, semantics: sem.slice(0, 80),
            visibleText: body.slice(0, 2000),
          }, null, 2));
        for (const choice of [
          'Français', 'Maroc', 'Simple et chaleureux',
          'Diabète Type 2', 'Comprimés',
        ]) await choose(page, choice);
        const action = page.getByRole('button', {name: 'Commencer', exact: true});
        await action.first().waitFor({state:'visible', timeout: 15000});
        const count = await action.count();
        const rect = await action.first().boundingBox();
        if (count !== 1 || !rect || rect.y < 0 ||
            rect.y + rect.height > height || rect.x < 0 ||
            rect.x + rect.width > width || rect.height < (width < 900 ? 44 : 32)) {
          throw new Error('CTA not singular, tappable and visible: ' +
            JSON.stringify({count, rect, width, height}));
        }
        await page.screenshot({path:out + '/onboarding-ready-after-' +
          width + 'x' + height + '.png', fullPage:false});
        results.push({width,height,rect,buttonCount:count,url:page.url()});
      } finally {
        await ctx.close();
      }
    }
    fs.writeFileSync(out+'/result.json',JSON.stringify({
      ok:true,source:'isolated_flutter_web_browser_harness',
      data:'no_real_patient_data',results,
    },null,2));
    console.log(JSON.stringify(results));
  } finally {
    await browser.close();
  }
})().catch(err => {
  fs.writeFileSync(out+'/failure.txt',String(err.stack || err));
  console.error(err);
  process.exit(1);
});
