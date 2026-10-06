const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const OUT = process.env.E2E_OUT || 'first-user-prod-e2e';
fs.mkdirSync(OUT,{recursive:true});

const sleep = ms => new Promise(r=>setTimeout(r,ms));
async function enableFlutterSemantics(page){
  const placeholder=page.locator('flt-semantics-placeholder');
  if(await placeholder.count()){
    await placeholder.first().focus();
    await page.keyboard.press('Enter');
    await sleep(500);
  }
}
async function capture(page,name){
  await page.screenshot({path:`${OUT}/${name}.png`,fullPage:false});
  const semantics = await page.locator('flt-semantics').evaluateAll(els =>
    els.map(e => e.getAttribute('aria-label') || e.textContent || '').filter(Boolean)
  ).catch(()=>[]);
  fs.writeFileSync(`${OUT}/${name}.txt`, [
    `URL: ${page.url()}`,
    ...semantics
  ].join('\n'));
}
function routeOf(page){ const u=new URL(page.url()); return u.pathname + u.hash; }
async function waitPath(page, part, timeout=20000){
  const end=Date.now()+timeout;
  while(Date.now()<end){
    if(routeOf(page).includes(part)) return;
    await sleep(250);
  }
  throw new Error(`Expected path containing ${part}, got ${page.url()}`);
}
async function clickText(page, texts, timeout=12000){
  for(const text of texts){
    const loc=page.getByText(text,{exact:false});
    const n=await loc.count();
    for(let i=0;i<n;i++){
      const el=loc.nth(i);
      if(await el.isVisible().catch(()=>false)){
        await el.scrollIntoViewIfNeeded().catch(()=>{});
        await el.click({timeout:3000});
        return text;
      }
    }
  }
  throw new Error(`None of texts clickable: ${texts.join(' | ')}`);
}
async function clickEnabledButton(page, timeout=15000){
  const end=Date.now()+timeout;
  while(Date.now()<end){
    const btns=page.getByRole('button');
    const n=await btns.count();
    for(let i=0;i<n;i++){
      const b=btns.nth(i);
      if(await b.isVisible().catch(()=>false) && await b.isEnabled().catch(()=>false)){
        await b.click();
        return;
      }
    }
    await sleep(300);
  }
  throw new Error('No enabled visible button found');
}
async function expectText(page,text,timeout=15000){
  await page.getByText(text,{exact:false}).first().waitFor({state:'visible',timeout});
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:['--force-renderer-accessibility']});
  const context=await browser.newContext({
    viewport:{width:390,height:844},
    locale:'fr-FR',
    colorScheme:'light',
    serviceWorkers:'block'
  });
  const page=await context.newPage();
  const cdp=await context.newCDPSession(page);
  await cdp.send('WebAuthn.enable');
  await cdp.send('WebAuthn.addVirtualAuthenticator',{options:{
    protocol:'ctap2',
    transport:'internal',
    hasResidentKey:true,
    hasUserVerification:true,
    isUserVerified:true,
    automaticPresenceSimulation:true
  }});

  await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:30000});
  await sleep(8000);
  await enableFlutterSemantics(page);
  await capture(page,'01-arrival');

  if(routeOf(page).includes('/login')){
    await clickText(page,['Créer un compte']);
    const dialog=page.getByRole('dialog');
    await dialog.waitFor({state:'visible',timeout:10000});
    const fields=dialog.getByRole('textbox');
    if(await fields.count()<3) throw new Error('Signup dialog did not expose 3 textboxes');
    const unique = `e2e-first-user-${process.env.GITHUB_RUN_ID || Date.now()}-${process.env.GITHUB_RUN_ATTEMPT || 1}@example.invalid`;
    const password = 'IAmina-E2E-2026!Strong#42';
    await fields.nth(0).fill(unique);
    await fields.nth(1).fill(password);
    await fields.nth(2).fill(password);
    await clickText(dialog,['Créer']);
    await waitPath(page,'/onboarding',25000);
    await sleep(1500);
  }
  await capture(page,'02-onboarding-arrival');

  if(routeOf(page).includes('/app-lock/setup')){
    await clickEnabledButton(page,20000);
    await waitPath(page,'/onboarding');
    await sleep(1200);
  }

  await expectText(page,'Bonjour ! Je suis IAmina',20000);
  await clickText(page,['Français']);
  await clickText(page,['Maroc']);
  await clickText(page,['Simple et chaleureux','Neutre et professionnel']);
  await clickText(page,['Diabète Type 2']);
  await clickText(page,['Comprimés']);
  await clickText(page,['mg/dL']);
  await capture(page,'03-onboarding-ready');

  await clickText(page,['Commencer']);
  await waitPath(page,'/consent',20000);
  await sleep(1200);
  await expectText(page,'Continuer sans IA');
  await expectText(page,'Accepter et continuer');
  await capture(page,'04-consent');

  await page.reload({waitUntil:'domcontentloaded'});
  await sleep(6000);
  await enableFlutterSemantics(page);
  await waitPath(page,'/consent',15000);
  if(await page.getByText('Bonjour ! Je suis IAmina',{exact:false}).count()){
    throw new Error('Onboarding resurfaced after reload: persistence regression');
  }
  await capture(page,'05-consent-after-reload');

  await clickText(page,['Accepter et continuer']);
  await waitPath(page,'/dashboard',20000);
  await sleep(5000);
  await expectText(page,'Ajouter ma première mesure',20000);
  await capture(page,'06-empty-dashboard');

  await clickText(page,['Ajouter ma première mesure']);
  await waitPath(page,'/ajouter',15000);
  await sleep(1500);
  await capture(page,'07-new-reading');

  const boxes=page.getByRole('textbox');
  const boxCount=await boxes.count();
  if(boxCount<1) throw new Error('No glucose textbox found');
  await boxes.first().fill('128');
  await clickText(page,['Enregistrer la mesure']);
  await expectText(page,'Mesure enregistrée.',20000);
  await capture(page,'08-post-save-receipt');

  await clickText(page,['Terminé','Fermer','Retour au tableau de bord']);
  await waitPath(page,'/dashboard',15000).catch(()=>{});
  await sleep(5000);
  await capture(page,'09-first-insight');

  if(!routeOf(page).includes('/dashboard')){
    await page.goto(BASE+'/dashboard',{waitUntil:'domcontentloaded'});
    await sleep(5000);
  }
  await clickText(page,['Parler avec IAmina']);
  await waitPath(page,'/companion/chat',15000);
  await sleep(2000);

  const chatBox=page.getByRole('textbox').last();
  await chatBox.fill('Que peux-tu me dire de ma première mesure ?');
  await chatBox.press('Enter');
  await expectText(page,'Vous',20000).catch(()=>{});
  await sleep(10000);
  await capture(page,'10-first-chat');

  const text = (await page.locator('body').innerText().catch(()=>'')) +
    ' ' + (await page.locator('flt-semantics').allTextContents().catch(()=>[])).join(' ');
  if(!/128/.test(text)) throw new Error('Saved reading 128 not observable after save');
  if(!/IAmina/i.test(text)) throw new Error('IAmina chat surface not observable');

  fs.writeFileSync(`${OUT}/result.json`, JSON.stringify({
    ok:true,
    finalUrl:page.url(),
    base:BASE,
    viewport:'390x844'
  },null,2));
  await browser.close();
})().catch(async err=>{
  fs.writeFileSync(`${OUT}/failure.txt`, String(err && err.stack || err));
  console.error(err);
  process.exit(1);
});
