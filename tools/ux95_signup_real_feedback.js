const {chromium} = require('playwright');
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const BASE = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const OUT = process.env.E2E_OUT || 'ux95-signup-real';
fs.mkdirSync(OUT, {recursive: true});
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [];

async function attempt(browser, width, height, method) {
  const name = width + 'x' + height + '-' + method;
  const result = {name, viewport: width + 'x' + height, method, registerStatuses: []};
  const context = await browser.newContext({
    viewport: {width, height},
    locale: 'fr-FR',
    colorScheme: 'light',
    serviceWorkers: 'block',
  });
  const page = await context.newPage();
  page.on('response', r => {
    if (r.url().includes('/api/v1/auth/register') && r.request().method() === 'POST') {
      result.registerStatuses.push(r.status());
    }
  });
  page.on('requestfailed', req => {
    if (req.url().includes('/api/v1/auth/register')) {
      result.registerFailure = req.failure()?.errorText || 'unknown';
    }
  });
  try {
    await page.goto(BASE, {waitUntil: 'domcontentloaded', timeout: 30000});
    await sleep(7500);
    const placeholder = page.locator('flt-semantics-placeholder');
    if (await placeholder.count()) {
      await placeholder.first().focus();
      await page.keyboard.press('Enter');
    }
    await page.getByRole('button', {name: /Créer un compte/i}).first().click({timeout:15000});
    const submit = page.getByRole('button', {name: 'Créer', exact:true});
    await submit.click({timeout:8000});
    await page.getByText('Renseignez les trois champs pour créer votre compte.', {exact:false})
      .first().waitFor({state:'visible', timeout:8000});
    result.emptyFeedback = true;
    result.emptyDidNotPOST = result.registerStatuses.length === 0;
    await page.screenshot({path: path.join(OUT, name+'-empty.png')});
    
    const fields = page.getByRole('textbox');
    const count = await fields.count();
    if (count < 3) throw new Error('Expected 3 signup fields, got '+count);
    const email = 'ux95-real-'+crypto.randomBytes(6).toString('hex')+'@example.invalid';
    const pass = 'A9!'+crypto.randomBytes(12).toString('hex')+'z';
    // Flutter Web exposes transient semantics inputs. Their DOM inputValue
    // may lag or differ from the TextEditingController. The true acceptance
    // gate is visible validation + successful protected register POST.
    const typeField = async (locator, value) => {
      await locator.fill(value, {timeout:8000});
      await locator.press('Tab');
      await sleep(150);
    };
    await typeField(fields.nth(count - 3), email);
    await typeField(fields.nth(count - 2), pass);
    await typeField(fields.nth(count - 1), pass+'wrong');
    const beforeMismatch = await Promise.all([
      fields.nth(count-3).inputValue(),
      fields.nth(count-2).inputValue(),
      fields.nth(count-1).inputValue(),
    ]);
    result.beforeMismatch = {
      emailPresent: beforeMismatch[0] === email,
      passwordPresent: beforeMismatch[1] === pass,
      confirmDifferent: beforeMismatch[2] !== beforeMismatch[1],
    };
    await page.screenshot({path: path.join(OUT, name+'-before-mismatch.png')});
    await submit.click({timeout:8000});
    await page.getByText('Les mots de passe ne correspondent pas.', {exact:false})
      .first().waitFor({state:'visible', timeout:8000});
    result.mismatchFeedback = true;
    result.mismatchDidNotPOST = result.registerStatuses.length === 0;
    await page.screenshot({path: path.join(OUT, name+'-mismatch.png')});
    
    await typeField(fields.nth(count - 1), pass);
    const beforeFinal = await Promise.all([
      fields.nth(count-3).inputValue(),
      fields.nth(count-2).inputValue(),
      fields.nth(count-1).inputValue(),
    ]);
    result.beforeFinal = {
      emailPresent: beforeFinal[0] === email,
      passwordMatched: beforeFinal[1] === pass && beforeFinal[2] === pass,
    };
    await page.screenshot({path: path.join(OUT, name+'-before-submit.png')});
    if (method === 'keyboard') {
      await submit.focus();
      await page.keyboard.press('Enter');
    } else {
      await submit.click({timeout:8000});
    }
    await page.waitForURL(/#\/(?:app-lock\/setup|onboarding)/, {timeout:30000});
    result.finalRoute = new URL(page.url()).hash;
    result.validPOST200 = result.registerStatuses.includes(200);
    result.enteredFirstUse = /app-lock\/setup|onboarding/.test(result.finalRoute);
    await page.screenshot({path: path.join(OUT, name+'-success.png')});
  } catch (error) {
    result.error = String(error?.message || error);
    result.finalRoute = new URL(page.url()).hash;
    await page.screenshot({path: path.join(OUT, name+'-failure.png')}).catch(() => {});
  } finally {
    const required = [
      'emptyFeedback', 'emptyDidNotPOST',
      'mismatchFeedback', 'mismatchDidNotPOST',
      'validPOST200', 'enteredFirstUse'
    ];
    result.passed = required.every(key => result[key] === true);
    checks.push(result);
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({headless:true, args:['--force-renderer-accessibility']});
  try {
    for (const [w,h,method] of [
      [390,844,'keyboard'], [390,844,'pointer'],
      [360,560,'keyboard'], [360,560,'pointer']
    ]) {
      await attempt(browser,w,h,method);
    }
  } finally {
    await browser.close();
  }
  const result = {
    deployedUrl: BASE,
    target: 'real signup feedback and valid transition',
    iterations: checks.length,
    checks,
    passed: checks.every(c => c.passed),
  };
  fs.writeFileSync(path.join(OUT,'ux95-signup-real-result.json'),JSON.stringify(result,null,2));
  if (!result.passed) {
    console.error('UX95 signup real browser gate failed: '+checks.filter(c=>!c.passed).map(c=>c.name+' '+(c.error||'missing proof')).join('; '));
    process.exit(1);
  }
  console.log('Four real signup iterations passed: empty, mismatch, pointer/keyboard.');
})().catch(err=>{console.error(err);process.exit(1);});
