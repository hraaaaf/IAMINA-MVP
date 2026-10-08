const {chromium} = require('playwright');
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const base = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const out = process.env.E2E_OUT || 'first-user-prod-e2e';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
fs.mkdirSync(out,{recursive:true});

(async () => {
  const browser = await chromium.launch({headless:true,args:['--force-renderer-accessibility']});
  const responses=[];
  const report={base,viewport:'390x844',method:'pointer click',network:responses};
  try {
    const page=await browser.newPage({
      viewport:{width:390,height:844},locale:'fr-FR',
      colorScheme:'light',serviceWorkers:'block'
    });
    page.on('response', r=>{
      if(r.url().includes('/api/v1/auth/register')) {
        responses.push({status:r.status(),method:r.request().method()});
      }
    });
    page.on('requestfailed', req=>{
      if(req.url().includes('/api/v1/auth/register'))
        responses.push({requestFailed:true,reason:req.failure()?.errorText||'unknown'});
    });
    await page.goto(base,{waitUntil:'domcontentloaded',timeout:30000});
    await sleep(7500);
    const placeholder=page.locator('flt-semantics-placeholder');
    if(await placeholder.count()) {
      await placeholder.first().focus();
      await page.keyboard.press('Enter');
    }
    await page.getByRole('button',{name:/Créer un compte/i}).first().click({timeout:12000});
    const submit=page.getByRole('button',{name:'Créer',exact:true});
    await submit.waitFor({state:'visible',timeout:12000});
    const boxes=page.getByRole('textbox');
    const count=await boxes.count();
    report.textboxCount=count;
    if(count<3)throw new Error('Signup did not expose three fields');
    const suffix=crypto.randomBytes(5).toString('hex');
    const email='ux95-signup-'+suffix+'@example.invalid';
    const pass='Ax!'+crypto.randomBytes(12).toString('hex')+'Z9';
    for (const [i,value] of [email,pass,pass].entries()) {
      await boxes.nth(count-3+i).click({timeout:10000});
      await page.keyboard.type(value,{delay:25});
      await page.keyboard.press('Tab');
    }
    report.inputMethod='real keyboard events';
    await page.screenshot({path:path.join(out,'ux95-signup-filled-390x844.png')});
    await submit.click({timeout:12000});
    const until=Date.now()+30000;
    while(Date.now()<until &&
          !/\/#\/(?:app-lock\/setup|onboarding)/.test(page.url())) {
      await sleep(250);
    }
    await sleep(250);
    report.finalRoute=new URL(page.url()).hash;
    report.signupApiObserved=responses.some(x=>x.method==='POST' && x.status===200);
    report.success=report.signupApiObserved &&
      (report.finalRoute.includes('/onboarding') || report.finalRoute.includes('/app-lock/setup'));
    await page.screenshot({path:path.join(out,'ux95-signup-after-submit-390x844.png')});
    fs.writeFileSync(path.join(out,'ux95-signup-diagnostic.json'),JSON.stringify(report,null,2));
    if(!report.success)throw new Error('Signup did not send POST and enter onboarding/app-lock');
    console.log('Synthetic pointer signup reached onboarding with a backend POST.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
