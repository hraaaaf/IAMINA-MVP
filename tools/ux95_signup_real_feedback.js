const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const BASE = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const OUT = process.env.E2E_OUT || 'ux95-signup-real';
fs.mkdirSync(OUT, {recursive: true});
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const results = [];

async function runCase(browser, spec) {
  const name = spec.kind+'-'+spec.width+'x'+spec.height+(spec.method ? '-'+spec.method : '');
  const result = {name, viewport: spec.width+'x'+spec.height, kind: spec.kind,
    method: spec.method || 'pointer', registerStatuses: []};
  const context = await browser.newContext({
    viewport: {width:spec.width,height:spec.height},
    locale:'fr-FR', colorScheme:'light', serviceWorkers:'block'
  });
  const page = await context.newPage();
  page.on('response', r => {
    if (r.url().includes('/api/v1/auth/register') && r.request().method()==='POST') {
      result.registerStatuses.push(r.status());
    }
  });
  page.on('requestfailed', req => {
    if (req.url().includes('/api/v1/auth/register')) {
      result.registerFailure = req.failure()?.errorText || 'unknown';
    }
  });
  try {
    await page.goto(BASE, {waitUntil:'domcontentloaded',timeout:30000});
    await sleep(7500);
    const placeholder=page.locator('flt-semantics-placeholder');
    if (await placeholder.count()) {
      await placeholder.first().focus();
      await page.keyboard.press('Enter');
    }
    await page.getByRole('button',{name:/Créer un compte/i})
      .first().click({timeout:15000});
    // Flutter routes and semantics materialize asynchronously after the tap.
    // Wait for the dialog's actual submit control; never treat the background
    // login textboxes as proof that the signup form has opened.
    const submit=page.getByRole('button',{name:'Créer',exact:true});
    await submit.waitFor({state:'visible',timeout:10000});
    if (spec.kind==='empty') {
      await submit.click({timeout:10000});
      await page.getByText('Renseignez les trois champs pour créer votre compte.',{exact:false})
        .first().waitFor({state:'visible',timeout:10000});
      result.inlineEmptyVisible=true;
      result.invalidDidNotPOST=result.registerStatuses.length===0;
      await page.screenshot({path:path.join(OUT,name+'-after.png')});
      result.passed=result.inlineEmptyVisible && result.invalidDidNotPOST;
    } else {
      const fields=page.getByRole('textbox');
      const count=await fields.count();
      if (count<3) throw new Error('Signup did not expose three fields');
      const email='ux95-reg-'+crypto.randomBytes(6).toString('hex')+'@example.invalid';
      const pass='A9!'+crypto.randomBytes(12).toString('hex')+'z';
      const values = [email, pass,
        spec.kind==='mismatch' ? pass+'different' : pass];
      if (spec.kind==='valid') {
        // Unlike locator.fill (which can update a transient Flutter Web
        // semantics input), real key events exercise TextEditingController.
        for (let i = 0; i < values.length; i++) {
          await fields.nth(count-3+i).click({timeout:10000});
          await page.keyboard.type(values[i], {delay:25});
          await page.keyboard.press('Tab');
        }
      } else {
        for (let i = 0; i < values.length; i++) {
          await fields.nth(count-3+i).fill(values[i]);
        }
      }
      await sleep(250);
      await page.screenshot({path:path.join(OUT,name+'-filled.png')});
      if (spec.kind==='mismatch') {
        await submit.click({timeout:10000});
        await page.getByText('Les mots de passe ne correspondent pas.',{exact:false})
          .first().waitFor({state:'visible',timeout:10000});
        result.inlineMismatchVisible=true;
        result.invalidDidNotPOST=result.registerStatuses.length===0;
        await page.screenshot({path:path.join(OUT,name+'-after.png')});
        result.passed=result.inlineMismatchVisible && result.invalidDidNotPOST;
      } else {
        if (spec.method==='keyboard') {
          await submit.focus();
          await page.keyboard.press('Enter');
        } else {
          await submit.click({timeout:10000});
        }
        await page.waitForURL(/#\/(app-lock\/setup|onboarding)/,{timeout:30000});
        result.finalRoute=new URL(page.url()).hash;
        result.validPOST200=result.registerStatuses.includes(200);
        result.enteredFirstUse=true;
        await page.screenshot({path:path.join(OUT,name+'-after.png')});
        result.passed=result.validPOST200 && result.enteredFirstUse;
      }
    }
  } catch(e) {
    result.error=String(e.message||e);
    result.finalRoute=new URL(page.url()).hash;
    result.passed=false;
    await page.screenshot({path:path.join(OUT,name+'-failure.png')}).catch(()=>{});
  } finally {
    results.push(result);
    await context.close();
  }
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:['--force-renderer-accessibility']});
  try {
    const specs=[
      {kind:'empty',width:390,height:844},
      {kind:'mismatch',width:360,height:560},
      {kind:'valid',width:390,height:844,method:'keyboard'},
      {kind:'valid',width:360,height:560,method:'pointer'}
    ];
    for (const spec of specs) await runCase(browser,spec);
  } finally {await browser.close();}
  const report={base:BASE,viewportSet:['390x844','360x560'],
    method:'independent virgin sessions; no stateful field correction',
    checks:results,passed:results.every(x=>x.passed)};
  fs.writeFileSync(path.join(OUT,'ux95-signup-real-result.json'),JSON.stringify(report,null,2));
  if (!report.passed) {
    console.error('Real signup test failed: '+results.filter(x=>!x.passed)
      .map(x=>x.name+' '+(x.error||'acceptance missing')).join('; '));
    process.exit(1);
  }
  console.log('Live signup: empty, mismatch, keyboard and pointer all passed.');
})().catch(e=>{console.error(e);process.exit(1);});
