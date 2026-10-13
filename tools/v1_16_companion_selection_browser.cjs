const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');

const root = 'v1-16-selection-proof';
fs.mkdirSync(root, {recursive: true});
const viewports = [[390,844], [768,1024], [1280,900]];
const observations = [];

async function activateSemantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  if (await placeholder.count()) {
    await placeholder.first().focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(400);
  }
}

async function getSemanticNames(page) {
  return page.locator('[aria-label]').evaluateAll(
    elements => elements.map(el => (el.getAttribute('aria-label') || '').slice(0,500))
  ).catch(() => []);
}

async function sendSyntheticQuestion(page, width, height) {
  const field = page.getByRole('textbox');
  let sentFromSemantics = false;
  if (await field.count()) {
    const el = field.first();
    if (await el.isVisible().catch(() => false)) {
      await el.fill('Une question simple').catch(async () => {
        await el.click(); await page.keyboard.insertText('Une question simple');
      });
      sentFromSemantics = true;
    }
  }
  if (!sentFromSemantics) {
    await page.mouse.click(width < 900 ? width/2 : width/2, height - 54);
    await page.keyboard.insertText('Une question simple');
  }
  await page.waitForTimeout(250);
  const button = page.getByRole('button', {name: /Envoyer|Send message/i});
  let submitted = false;
  if (await button.count()) {
    const el = button.first();
    if (await el.isVisible().catch(() => false) && await el.isEnabled().catch(() => false)) {
      await el.click();
      submitted = true;
    }
  }
  if (!submitted) {
    await page.mouse.click(width < 900 ? width - 31 : width/2 + 320, height - 54);
  }
  for (let attempt=0;attempt<30;attempt++) {
    const names = await getSemanticNames(page);
    const body = await page.locator('body').innerText().catch(()=>'');
    if (names.some(n=>n.includes('Réponse locale limitée')) ||
        body.includes('Réponse locale limitée')) return;
    await page.waitForTimeout(400);
  }
  const names = await getSemanticNames(page);
  throw new Error('Synthetic reply not observed after send: '+JSON.stringify({width,height,names:names.slice(-20)}));
}

(async () => {
  const browser = await chromium.launch({headless:true,args:['--force-renderer-accessibility']});
  try {
    for (const phase of ['before','after']) {
      const port = phase === 'before' ? 7358 : 7359;
      for (const [width,height] of viewports) {
        const ctx = await browser.newContext({
          viewport:{width,height},deviceScaleFactor:1,locale:'fr-FR',
          colorScheme:'light',serviceWorkers:'block',
        });
        const page = await ctx.newPage();
        const problems = [];
        page.on('pageerror',e=>problems.push('pageerror:'+String(e.message)));
        page.on('console',m=>{if(m.type()==='error')problems.push('console:'+m.text())});
        await page.goto('http://127.0.0.1:'+port+'/?p1-proof=1',
          {waitUntil:'domcontentloaded',timeout:30000});
        await page.waitForTimeout(4500);
        await activateSemantics(page);
        await sendSyntheticQuestion(page,width,height);
        const base=path.join(root,phase+'-'+width+'x'+height);
        await page.screenshot({path:base+'.png',fullPage:false});
        const labels=await getSemanticNames(page);
        fs.writeFileSync(base+'.json',JSON.stringify({
          viewport:{width,height},phase,replyObserved:true,
          semanticLabels:labels.slice(0,120),errors:problems,url:page.url()
        },null,2));
        observations.push({phase,width,height,errorCount:problems.length});
        if(problems.length)throw new Error('Browser errors: '+JSON.stringify(problems));
        await ctx.close();
      }
    }
    fs.writeFileSync(path.join(root,'result.json'),JSON.stringify({
      source:'synthetic_companion_governance_fallback',patientData:false,
      viewports:observations,success:true,
    },null,2));
    console.log(JSON.stringify(observations));
  } finally {
    await browser.close();
  }
})().catch(e => {
  fs.writeFileSync(path.join(root,'failure.txt'),String(e.stack||e));
  console.error(e);process.exitCode=1;
});
