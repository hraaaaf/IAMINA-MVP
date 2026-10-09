const { chromium } = require('playwright');
const fs = require('fs');
const crypto = require('crypto');
const out = process.env.AUDIT_OUT;
const phase = process.env.AUDIT_PHASE;
if (!out || !['before', 'after'].includes(phase)) {
  throw new Error('AUDIT_OUT and AUDIT_PHASE before/after required');
}
fs.mkdirSync(out, {recursive:true});
const expected = phase === 'before' ? '10.6' : '10.5';
const targetExpected = phase === 'before' ? '70' : '3.9';
const base = 'http://127.0.0.1:7367';
async function semantics(page) {
  return await page.locator('flt-semantics').evaluateAll(els =>
    els.map(e => [e.getAttribute('aria-label') || '', e.getAttribute('aria-valuetext') || '', e.getAttribute('value') || '', e.textContent || '', e.querySelector('input')?.value || ''].join(' ')).join(' ')
  ).catch(()=> '');
}
async function capture(browser, surface, width, height) {
  const context = await browser.newContext({
    viewport:{width,height}, locale:'fr-FR',deviceScaleFactor:1,
    serviceWorkers:'block', colorScheme:'light'
  });
  try {
    const page = await context.newPage();
    const runtimeErrors = [];
    page.on('pageerror', e => runtimeErrors.push('pageerror: '+e.message));
    page.on('console', m => { if (m.type()==='error') runtimeErrors.push('console: '+m.text()); });
    const fixture = surface === 'profile' ? 'profile-targets-699' : 'unit-190';
    await page.goto(base+'/?surface='+surface+'&seed=1&v101='+fixture, {waitUntil:'domcontentloaded',timeout:30000});
    // Flutter only creates the semantics tree after its Web engine initializes.
    // The earlier immediate count() saw zero placeholders and never enabled it.
    await page.waitForTimeout(9000);
    const ph = page.locator('flt-semantics-placeholder');
    if (await ph.count()) {
      await ph.first().focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(750);
    }
    if (surface === 'profile') {
      // Expand the real initially-collapsed medical section, then scroll to
      // its target editors at the same viewport on BEFORE and AFTER.
      let opened = false;
      const section = page.getByText('Suivi médical', { exact: true }).first();
      if (await section.count()) {
        try {
          await section.click({ timeout: 3500 });
          opened = true;
        } catch (e) {
          console.log('Profile semantics click unavailable: '+e.message.slice(0,180));
        }
      }
      if (!opened) await page.mouse.click(158, 191);
      await page.waitForTimeout(850);
      await page.mouse.wheel(0, 475);
      await page.waitForTimeout(700);
    }
    let seen = false; let sample = '';
    const required = surface === 'profile' ? targetExpected : expected;
    const mustProveValue = surface === 'dashboard' ||
      surface === 'reports-local' || surface === 'profile';
    for (let k=0;k<(mustProveValue ? 55 : 15);k++){
      if (surface==='reports-local' && k%3===0) await page.mouse.wheel(0,410);
      sample = await semantics(page);
      if(sample.includes(required)) { seen=true; break; }
      await page.waitForTimeout(400);
    }
    if(!seen && mustProveValue) {
      const diagnostic = out+'/diagnostic-'+phase+'-'+surface+'-'+width+'x'+height+'.png';
      await page.screenshot({path:diagnostic,fullPage:false});
      const dom = await page.evaluate(() => ({
        title: document.title,
        placeholders: document.querySelectorAll('flt-semantics-placeholder').length,
        panes: document.querySelectorAll('flt-glass-pane').length,
        semanticNodes: document.querySelectorAll('flt-semantics').length,
        bodyText: document.body.innerText.slice(0,250),
      }));
      throw new Error(phase+' '+surface+' '+width+' expected '+required+
        ' mmol/L in semantics; observed='+sample.slice(0,1800)+
        '; dom='+JSON.stringify(dom)+'; errors='+JSON.stringify(runtimeErrors.slice(0,6)));
    }
    if(surface==='reports-local') await page.mouse.wheel(0,130);
    await page.waitForTimeout(250);
    const filename = phase+'-'+surface+'-'+width+'x'+height+'.png';
    const bytes = await page.screenshot({path:out+'/'+filename,fullPage:false});
    return {filename,surface,width,height,observed:seen ? required : null,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
  }finally{await context.close();}
}
(async()=>{
  const browser = await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const reports=[];
  try {
    for(const [w,h] of [[390,844],[768,1024]])for(const surface of ['dashboard','reports-local','journal','trend','profile']){
      reports.push(await capture(browser,surface,w,h));
    }
  }finally{await browser.close();}
  fs.writeFileSync(out+'/'+phase+'-observations.json',JSON.stringify({phase,expected,reports},null,2));
  if(phase==='after'){
    for(const x of reports){
      const old=fs.readFileSync(out+'/before-'+x.surface+'-'+x.width+'x'+x.height+'.png');
      const fresh=fs.readFileSync(out+'/'+x.filename);
      if((x.surface === 'dashboard' || x.surface === 'reports-local' || x.surface === 'profile') && old.equals(fresh))
        throw new Error('Identical images: '+x.filename);
    }
  }
  console.log(JSON.stringify({phase,reports}));
})().catch(e=>{console.error(e);process.exit(1)});
