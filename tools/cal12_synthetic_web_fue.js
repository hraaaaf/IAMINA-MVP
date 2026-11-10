/* CAL-12 Web FUE: real local Chrome running the isolated Flutter Web entrypoint.
 * No patient, identity provider, hospital recipient, Vercel or network egress.
 */
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');

const origin = 'http://127.0.0.1:7394';
const output = 'cal12-web-fue-proof';
const viewports = [[390, 844], [768, 1024], [1280, 900]];
const languages = {
  fr: {
    preview: 'Aperçu fictif', next: 'Continuer',
    consent: 'Consentement fictif',
    agree: 'J’accepte cette simulation uniquement',
    consentNext: 'Valider le consentement',
    recipient: 'Destinataire fictif',
    doctor: 'Médecin fictif 1',
    confirm: 'Je confirme le destinataire sélectionné',
    simulate: 'Simuler le partage',
    done: 'Simulation terminée',
    notSent: 'Aucun document ni message n’a été envoyé.',
    ownerB: 'Profil fictif B', ownerA: 'Profil fictif A',
  },
  ar: {
    preview: 'معاينة تجريبية', next: 'متابعة',
    consent: 'موافقة تجريبية',
    agree: 'أوافق على هذه المحاكاة فقط',
    consentNext: 'تأكيد الموافقة',
    recipient: 'مستلم تجريبي',
    doctor: 'طبيب تجريبي ١',
    confirm: 'أؤكد المستلم المحدد',
    simulate: 'محاكاة المشاركة',
    done: 'اكتملت المحاكاة',
    notSent: 'لم يتم إرسال أي مستند أو رسالة.',
    ownerB: 'ملف تجريبي ب', ownerA: 'ملف تجريبي أ',
  },
};
fs.mkdirSync(output, {recursive: true});
const proof = {
  status: 'INCOMPLETE',
  head: process.env.CAL12_HEAD || 'unknown',
  scope: 'Standalone, isolated Flutter Web fixture in local real Chrome',
  realPatientExport: false,
  networkEgressAllowed: false,
  hostedAppFUE: false,
  clinicalApproval: false,
  cases: [],
  captures: [],
  errors: [],
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function activateSemantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  if (await placeholder.count()) {
    await placeholder.first().focus().catch(() => {});
    await page.keyboard.press('Enter').catch(() => {});
    await placeholder.first().evaluate(el => el.click()).catch(() => {});
    await sleep(300);
  }
}
function probes(page, label) {
  return [
    page.getByRole('button', {name: label, exact:true}),
    page.getByRole('checkbox', {name: label, exact:true}),
    page.getByRole('radio', {name: label, exact:true}),
    page.getByLabel(label, {exact:true}),
    // Flutter may intentionally merge a non-interactive sentence group into
    // one accessible label. Verify the real semantic label, not CSS pixels.
    page.getByLabel(label, {exact:false}),
    page.getByText(label, {exact:true}),
  ];
}
async function visible(page, label) {
  for (const probe of probes(page, label)) {
    const count = Math.min(await probe.count(), 4);
    for (let i = 0; i < count; i++) {
      const loc = probe.nth(i);
      if (await loc.isVisible().catch(() => false)) return loc;
    }
  }
  return null;
}
async function text(page, label) {
  for (let round = 0; round < 70; round++) {
    const loc = await visible(page, label);
    if (loc) return loc;
    await sleep(200);
  }
  const diagnostic = await page.evaluate(() => ({
    title: document.title,
    flutter: !!document.querySelector('flutter-view'),
    placeholder: !!document.querySelector('flt-semantics-placeholder'),
    semanticsCount: document.querySelectorAll('flt-semantics').length,
    samples: [...document.querySelectorAll('flt-semantics')]
      .slice(0, 15)
      .map(x => ({label:x.getAttribute('aria-label'),
                  text:(x.textContent||'').slice(0,80)})),
    bodyText: (document.body?.innerText||'').slice(0,250),
  }));
  throw Error('Missing visible Flutter semantics: '+label+'; '+JSON.stringify(diagnostic));
}
async function click(page, label) {
  const item = await text(page, label);
  await item.scrollIntoViewIfNeeded();
  await item.click({timeout: 12000});
  await sleep(130);
}
async function capture(page, locale, view, stage) {
  const filename = [locale, view[0] + 'x' + view[1], stage].join('-') + '.png';
  const target = path.join(output, filename);
  await page.screenshot({path: target, animations: 'disabled', fullPage: false});
  const bytes = fs.readFileSync(target);
  assert.equal(bytes.subarray(0,8).toString('hex'), '89504e470d0a1a0a');
  assert.ok(bytes.length > 10000, 'Blank screenshot ' + filename);
  const width = bytes.readUInt32BE(16), height = bytes.readUInt32BE(20);
  assert.equal(width, view[0]);
  assert.equal(height, view[1]);
  proof.captures.push({
    name: filename,
    width,
    height,
    sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
  });
}
async function runScenario(browser, locale, view) {
  const c = languages[locale], label = locale + '-' + view.join('x');
  const context = await browser.newContext({
    viewport: {width: view[0], height: view[1]},
    locale: locale === 'ar' ? 'ar-MA' : 'fr-FR',
    serviceWorkers: 'block', acceptDownloads: false, colorScheme: 'light',
  });
  const page = await context.newPage();
  const errors = [], deniedExternal = [], downloads = [], popups = [], writes = [];
  page.on('pageerror', err => errors.push(String(err.message || err).slice(0,450)));
  page.on('crash', () => errors.push('Chrome page crashed'));
  page.on('download', d => downloads.push(d.suggestedFilename()));
  page.on('popup', () => popups.push('Unexpected popup'));
  await page.route('**/*', route => {
    const request = route.request(), url = request.url();
    if (request.method() !== 'GET') {
      writes.push(request.method() + ' ' + url.slice(0,120));
      return route.abort();
    }
    if (url.startsWith(origin + '/') ||
        url.startsWith('data:') || url.startsWith('blob:')) {
      return route.continue();
    }
    deniedExternal.push(url.split('?',1)[0]);
    return route.abort();
  });
  const record = {locale, viewport: view.join('x'), result: 'FAILED', steps: []};
  try {
    const response = await page.goto(origin + '/?lang=' + locale, {
      waitUntil:'domcontentloaded', timeout:60000,
    });
    assert.equal(response.status(), 200);
    await page.waitForSelector('flutter-view, flt-glass-pane', {timeout:60000});
    await activateSemantics(page);
    await text(page, c.preview);
    await text(page, '142 mg/dL');
    record.steps.push('A starts with fictional 142 mg/dL');
    await capture(page, locale, view, 'before-preview');
    await click(page, c.next);
    await text(page, c.consent);

    // An unconfirmed consent MUST NOT advance the screen.
    await click(page, c.agree);
    await click(page, c.consentNext);
    await text(page, c.recipient);
    record.steps.push('Explicit fictional consent accepted');
    await click(page, c.doctor);
    await click(page, c.confirm);
    await click(page, c.simulate);
    await text(page, c.done);
    await text(page, c.notSent);
    await text(page, '142 mg/dL');
    record.steps.push('Destination confirmed; no document or message sent');
    await capture(page, locale, view, 'after-simulation');

    // Same browser instance: switching fictional owner must discard preview,
    // recipient and consent. B must NEVER show A's distinct 142 mg/dL.
    await click(page, c.ownerB);
    await text(page, c.preview);
    await text(page, '119 mg/dL');
    assert.equal(await visible(page, '142 mg/dL'), null);
    assert.equal(await visible(page, c.done), null);
    record.steps.push('A->B: no A reading and authorization reset');
    await capture(page, locale, view, 'b-isolated');

    await click(page, c.ownerA);
    await text(page, c.preview);
    await text(page, '142 mg/dL');
    assert.equal(await visible(page, '119 mg/dL'), null);
    assert.equal(await visible(page, c.done), null);
    await click(page, c.next);
    await text(page, c.consent);
    // Declined consent cannot enable the next stage.
    const consentButton = await text(page, c.consentNext);
    assert.equal(await consentButton.isEnabled(), false,
      'A return must not inherit a previous consent');
    record.steps.push('B->A: prior consent/destination not reused');
    await capture(page, locale, view, 'a-return-no-consent');

    const layout = await page.evaluate(() => ({
      width: window.innerWidth,
      rootScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      direction: document.querySelector('flutter-view')?.getAttribute('dir') || '',
    }));
    assert.equal(layout.width, view[0]);
    assert.ok(layout.rootScrollWidth <= view[0] + 2,
      'Unexpected horizontal overflow: ' + JSON.stringify(layout));
    const unwanted = deniedExternal.filter(url =>
      !/^https:\/\/fonts\.gstatic\.com\/s\/notosans(?:arabic|symbols)/.test(url));
    assert.equal(unwanted.length, 0, 'Unexpected external request: ' + unwanted);
    assert.equal(writes.length, 0, 'Write/network call attempted');
    assert.equal(downloads.length, 0, 'Unexpected download');
    assert.equal(popups.length, 0, 'Unexpected popup');
    assert.equal(errors.length, 0, 'Flutter Chrome errors: ' + errors.join('; '));
    record.layout = layout;
    record.externalDenied = deniedExternal.length;
    record.result = 'PASS';
  } catch (err) {
    record.error = String(err.stack || err).slice(0,1200);
    proof.errors.push({label, error: record.error});
    await capture(page, locale, view, 'failure').catch(() => {});
  } finally {
    proof.cases.push(record);
    await context.close();
  }
}
async function main() {
  const browser = await chromium.launch({headless:true});
  try {
    for (const locale of ['fr','ar']) {
      for (const view of viewports) {
        await runScenario(browser, locale, view);
      }
    }
  } finally {
    await browser.close();
    proof.status = proof.errors.length === 0 && proof.cases.length === 6 &&
        proof.cases.every(item => item.result === 'PASS')
      ? 'PASS_BOUNDED_REAL_CHROME_SYNTHETIC'
      : 'FAIL';
    fs.writeFileSync(path.join(output,'proof.json'),
      JSON.stringify(proof,null,2) + '\n','utf8');
  }
  assert.equal(proof.status, 'PASS_BOUNDED_REAL_CHROME_SYNTHETIC',
    'CAL-12 synthetic browser FUE incomplete: ' + JSON.stringify(proof.errors));
}
main().catch(err => { console.error(err); process.exitCode = 1; });
