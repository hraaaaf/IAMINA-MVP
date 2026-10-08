const { chromium } = require('playwright');
const fs = require('fs');

const base = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const out = process.env.E2E_OUT || 'audit-prod-transversal';
fs.mkdirSync(out, { recursive: true });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const results = [];
const events = [];

async function semantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  if (await placeholder.count()) {
    await placeholder.first().focus();
    await page.keyboard.press('Enter');
    await delay(450);
  }
}
async function visibleText(page) {
  const nodes = await page.locator('flt-semantics')
    .evaluateAll(els => els.flatMap(e => [
      e.getAttribute('aria-label'), e.textContent,
    ]).filter(Boolean)).catch(() => []);
  return nodes.join(' ').replace(/\s+/g, ' ').trim();
}
async function capture(page, name) {
  await page.screenshot({ path: out + '/' + name + '.png', fullPage: false });
  fs.writeFileSync(out + '/' + name + '.txt',
    'URL: ' + page.url() + '\n' + await visibleText(page));
}
async function openRoute(page, name, route) {
  const item = {name, requestedRoute: route};
  try {
    await page.evaluate(r => { location.hash = '#' + r; }, route);
    await delay(3000);
    await semantics(page);
    item.observedUrl = page.url();
    item.visibleText = (await visibleText(page)).slice(0, 2400);
    item.blocked = !page.url().includes('#' + route);
    await capture(page, name + '-390x844');
  } catch (e) {
    item.error = String(e.message || e);
    item.blocked = true;
    await capture(page, name + '-blocked-390x844').catch(() => {});
  }
  results.push(item);
}

(async () => {
  const browser = await chromium.launch({
    headless: true, args: ['--force-renderer-accessibility'],
  });
  try {
    const context = await browser.newContext({
      viewport: {width: 390, height: 844},
      locale: 'fr-FR', colorScheme: 'light', serviceWorkers: 'block',
    });
    const page = await context.newPage();
    page.on('pageerror', e => events.push('pageerror: ' + e.message));
    page.on('requestfailed', r => events.push('failed: ' + r.url()));
    page.on('response', r => {
      if (r.url().includes('/api/v1/')) events.push(r.status() + ' ' + r.url());
    });
    await page.goto(base, {waitUntil: 'domcontentloaded', timeout: 30000});
    await delay(8500);
    await semantics(page);
    await capture(page, '01-arrival-390x844');

    const end = Date.now() + 15000;
    let entered = false;
    while (Date.now() < end && !entered) {
      const candidates = [
        page.getByRole('button', {name: /Accès démo/i}),
        page.getByText('Accès démo', {exact: false}),
      ];
      for (const loc of candidates) {
        if (await loc.count() && await loc.first().isVisible().catch(() => false)) {
          await loc.first().click({timeout: 2500});
          entered = true;
          break;
        }
      }
      if (!entered) await delay(300);
    }
    if (!entered) throw new Error('Public demo action not discoverable');

    await delay(8000);
    await semantics(page);
    await capture(page, '02-demo-arrival-390x844');
    const startUrl = page.url();

    const routes = [
      ['03-accueil', '/dashboard'],
      ['04-mesures', '/journal'],
      ['05-rapports', '/summary'],
      ['06-iamina', '/companion'],
      ['07-iamina-chat', '/companion/chat'],
      ['08-import', '/importer'],
      ['09-cgm', '/cgm'],
      ['10-profil', '/profile'],
      ['11-rappels', '/reminders'],
      ['12-traitements', '/medications'],
    ];
    for (const [name, route] of routes) await openRoute(page, name, route);

    // Secondary states: test visibility beyond the first fold, using no writes.
    async function secondary(name, route, action) {
      try {
        await page.evaluate(r => { location.hash = '#' + r; }, route);
        await delay(2400);
        await semantics(page);
        await action();
        await delay(1000);
        await capture(page, name + '-390x844');
        results.push({
          name, requestedRoute: route, observedUrl: page.url(),
          visibleText: (await visibleText(page)).slice(0, 2400),
          interaction: true,
        });
      } catch (e) {
        results.push({name, requestedRoute: route, error: String(e.message || e)});
        await capture(page, name + '-blocked-390x844').catch(() => {});
      }
    }
    await secondary('13-rapports-scroll', '/summary', async () => {
      await page.mouse.move(170, 570);
      await page.mouse.wheel(0, 680);
    });
    await secondary('14-profil-donnees', '/profile', async () => {
      await page.getByText('Données & appareils', {exact: false})
        .first().click({timeout: 4000});
    });
    await secondary('15-cgm-dexcom', '/cgm', async () => {
      await page.getByText('Dexcom G6/G7', {exact: false})
        .first().click({timeout: 4000});
    });
    await secondary('16-navigation-mesures', '/dashboard', async () => {
      await page.getByRole('button', {name: /Mesures/i})
        .first().click({timeout: 4000});
    });
    await secondary('17-navigation-mesures-clavier', '/dashboard', async () => {
      const control = page.getByRole('button', {name: /Mesures/i}).first();
      await control.focus();
      await page.keyboard.press('Enter');
    });
    await secondary('18-navigation-mesures-tactile', '/dashboard', async () => {
      await page.mouse.click(140, 805);
    });
    await secondary('19-navigation-rapports-tactile', '/dashboard', async () => {
      await page.mouse.click(251, 805);
    });
    fs.writeFileSync(out + '/result.json', JSON.stringify({
      base, viewport: '390x844', account: 'public-demo-only',
      startUrl, routes: results,
    }, null, 2));
    fs.writeFileSync(out + '/runtime.log', events.join('\n'));
  } finally {
    await browser.close();
  }
})().catch(err => {
  fs.writeFileSync(out + '/failure.txt', String(err.stack || err));
  fs.writeFileSync(out + '/runtime.log', events.join('\n'));
  console.error(err);
  process.exit(1);
});
