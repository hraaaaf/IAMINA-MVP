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
  // Select the visible, synthetic quick-question in the *actual Flutter UI*.
  // The shortcut pre-fills the real composer and focuses it, avoiding
  // ungrounded screen coordinates that can silently click the wrong surface.
  const button = page.getByRole('button', {name: /Que peux-tu faire/i});
  const semantics = page.locator('flt-semantics[aria-label*="Que peux-tu faire ?"]');
  const suggestion = await button.count() ? button.first() : semantics.first();
  await suggestion.waitFor({state:'visible', timeout:15000});
  await suggestion.click({timeout:5000});
  await page.waitForTimeout(350);

  // Send via the real accessible CTA, or via the focused TextField's native
  // Enter action. Never guess where the button might be on a viewport.
  const submit = page.getByRole('button', {name:/Envoyer le message|Send message/i});
  let delivery = 'accessible-send-button';
  if (await submit.count() && await submit.first().isVisible()) {
    await submit.first().click({timeout:5000});
  } else {
    const focused = await page.evaluate(() => {
      const active = document.activeElement;
      return Boolean(active && (active.matches('input,textarea,[contenteditable="true"]') ||
        active.closest('flt-text-editing-host')));
    });
    if (!focused) {
      throw new Error('Composer input not focused and accessible send button absent');
    }
    delivery = 'focused-native-send-action';
    await page.keyboard.press('Enter');
  }

  for (let attempt=0; attempt<40; attempt++) {
    const names = await getSemanticNames(page);
    const body = await page.locator('body').innerText().catch(()=>'');
    if (names.some(n=>n.includes('Réponse locale limitée')) ||
        body.includes('Réponse locale limitée')) return delivery;
    await page.waitForTimeout(400);
  }
  const names = await getSemanticNames(page);
  throw new Error('Synthetic reply not observed after real UI submission: '+
    JSON.stringify({width,height,delivery,names:names.slice(-30)}));
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
        try {
          await sendSyntheticQuestion(page,width,height);
        } catch (error) {
          const diagnostic = path.join(root,'debug-'+phase+'-'+width+'x'+height);
          await page.screenshot({path:diagnostic+'.png',fullPage:false}).catch(()=>{});
          fs.writeFileSync(diagnostic+'.json',JSON.stringify({
            phase,width,height,error:String(error),
            labels:(await getSemanticNames(page)).slice(-100),
            text:(await page.locator('body').innerText().catch(()=>'' )).slice(-2000),
            focus:await page.evaluate(() => ({
              tag:document.activeElement?.tagName,
              value:document.activeElement?.value || null,
            })).catch(()=>null),
          },null,2));
          throw error;
        }
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
