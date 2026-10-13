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

async function chooseCountry(page, width, height) {
  const probes = [
    page.getByRole('textbox', {name:/Rechercher un pays|Pays/i}),
    page.getByRole('combobox', {name:/Rechercher un pays|Pays/i}),
    page.getByText('Rechercher un pays', {exact:false}),
  ];
  let field = null;
  for (const probe of probes) {
    if (await probe.count() && await probe.first().isVisible().catch(()=>false)) {
      field = probe.first();
      break;
    }
  }
  if (!field) throw new Error('Country search control unavailable');
  await field.click({timeout:5000});
  // Flutter's text-editing host can detach between count() and fill().
  // Use the focused keyboard path; assert that the suggestion is rendered.
  await page.keyboard.type('Mar');
  await page.waitForTimeout(250);
  // The open search suggestions must be visible at the same three viewport
  // sizes; capture *before* selecting, so the user can validate UX.
  const proposed = page.getByText('Maroc', {exact:true});
  await proposed.last().waitFor({state:'visible',timeout:8000});
  await page.screenshot({
    path: out + '/onboarding-country-suggestions-' + width + 'x' + height + '.png',
    fullPage:false,
  });
  await choose(page, 'Maroc');
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
        // V1 decision #6 removes tone selection entirely. Explicitly assert
        // that neither legacy tone choice nor its question is present.
        const obsoleteTone = ['Quel ton préférez-vous ?', 'Simple et chaleureux',
                              'Neutre et professionnel'];
        for (const legacy of obsoleteTone) {
          const match = page.getByText(legacy, {exact: true});
          if (await match.count()) {
            throw new Error('Obsolete tone picker still exposed: ' + legacy);
          }
        }
        await choose(page, 'Français');
        await chooseCountry(page, width, height);
        for (const choice of ['Diabète Type 2', 'Comprimés']) {
          await choose(page, choice);
        }
        // Actual Chrome debug DOM: compact viewports merge step copy into a
        // parent ARIA label; desktop exposes it as visible text without ARIA.
        // Both must state exactly five steps after the four required choices.
        let stepEvidence;
        if (width < 900) {
          const progress = page.locator(
            'flt-semantics[aria-label*="Étape 5 sur 5"]',
          );
          await progress.first().waitFor({state:'attached', timeout:15000});
          stepEvidence = await progress.first().getAttribute('aria-label');
        } else {
          await page.getByText('Étape 5 sur 5', {exact:false}).first()
            .waitFor({state:'visible', timeout:15000});
          stepEvidence = await page.locator('body').innerText();
        }
        if (!stepEvidence || !stepEvidence.includes('Étape 5 sur 5')) {
          throw new Error('Expected five-step progress on ' + width + 'x' +
            height + ', got ' + JSON.stringify(stepEvidence));
        }
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
