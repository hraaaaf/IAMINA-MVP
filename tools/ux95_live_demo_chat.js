const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const base = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const out = process.env.E2E_OUT || 'first-user-prod-e2e';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const normalize = text => String(text || '').replace(/\s+/g, ' ').trim();
const browserOptions = { headless: true, args: ['--force-renderer-accessibility'] };

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({
      viewport: {width: 390, height: 844},
      locale: 'fr-FR', colorScheme: 'light',
      serviceWorkers: 'block',
    });
    await page.goto(base, {waitUntil: 'domcontentloaded', timeout: 30000});
    await delay(6500);
    const placeholder = page.locator('flt-semantics-placeholder');
    if (await placeholder.count()) {
      await placeholder.first().focus();
      await page.keyboard.press('Enter');
    }
    const demo = page.getByRole('button', {name: /Accès démo/i});
    await demo.first().click({timeout: 15000});
    await delay(5000);
    await page.evaluate(() => { location.hash = '#/companion/chat'; });
    await delay(3200);
    if (!(page.url().includes('/companion/chat'))) {
      throw new Error('Demo did not reach Companion Chat');
    }
    const input = page.getByRole('textbox').first();
    await input.fill('Que peux-tu me dire de ma dernière mesure de glycémie ?');
    await page.getByRole('button', {name: 'Envoyer le message'}).first().click();
    await delay(2800);
    const text = normalize(await page.locator('body').innerText());
    await page.screenshot({path: path.join(out, 'ux95-demo-chat-390x844.png')});
    const checks = {
      deviceReading: /Votre dernière mesure enregistrée sur cet appareil est de [0-9]+(?:[.,][0-9]+)? mg\/dL/.test(text),
      syncDisclosure: /en attente de synchronisation|marquée comme synchronisée|dernière tentative de synchronisation a échoué/.test(text),
      noUnsupportedTrend: text.includes('Cette mesure seule ne permet pas'),
      deviceSourceLabel: text.toLowerCase().includes('sur cet appareil'),
      governedFallbackLabeled: !text.includes('Je peux continuer avec les fonctions locales') || text.includes('IA externe indisponible'),
    };
    const result = {base,viewport:'390x844',url:page.url(),checks,passed:Object.values(checks).every(Boolean)};
    fs.writeFileSync(path.join(out,'ux95-demo-chat-checks.json'),JSON.stringify(result,null,2));
    if (!result.passed) throw new Error('Live demo chat checks failed: '+Object.entries(checks).filter(([,ok])=>!ok).map(([name])=>name).join(', '));
    console.log('Real demo chat local continuity passed');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
