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
const base = 'http://127.0.0.1:7367';
async function semantics(page) {
  return await page.locator('flt-semantics').evaluateAll(els =>
    els.map(e => [e.getAttribute('aria-label') || '', e.textContent || ''].join(' ')).join(' ')
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
    await page.goto(base+'/?surface='+surface+'&seed=1&v101=unit-190', {waitUntil:'domcontentloaded',timeout:30000});
    // Flutter only creates the semantics tree after its Web engine initializes.
    // The earlier immediate count() saw zero placeholders and never enabled it.
    await page.waitForTimeout(9000);
    const ph = page.locator('flt-semantics-placeholder');
    if (await ph.count()) {
      await ph.first().focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(750);
    }
    let seen = false; let sample = '';
    const mustProveValue = surface === 'dashboard' || surface === 'reports-local';
    for (let k=0;k<(mustProveValue ? 55 : 15);k++){
      if (surface==='reports-local' && k%3===0) await page.mouse.wheel(0,410);
      sample = await semantics(page);
      if(sample.includes(expected)) { seen=true; break; }
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
      throw new Error(phase+' '+surface+' '+width+' expected '+expected+
        ' mmol/L in semantics; observed='+sample.slice(0,1800)+
        '; dom='+JSON.stringify(dom)+'; errors='+JSON.stringify(runtimeErrors.slice(0,6)));
    }
    if(surface==='reports-local') await page.mouse.wheel(0,130);
    await page.waitForTimeout(250);
    const filename = phase+'-'+surface+'-'+width+'x'+height+'.png';
    const bytes = await page.screenshot({path:out+'/'+filename,fullPage:false});
    return {filename,surface,width,height,observed:seen ? expected : null,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
  }finally{await context.close();}
}
(async()=>{
  const browser = await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const reports=[];
  try {
    for(const [w,h] of [[390,844],[768,1024]])for(const surface of ['dashboard','reports-local','journal','trend']){
      reports.push(await capture(browser,surface,w,h));
    }
  }finally{await browser.close();}
  fs.writeFileSync(out+'/'+phase+'-observations.json',JSON.stringify({phase,expected,reports},null,2));
  if(phase==='after'){
    for(const x of reports){
      const old=fs.readFileSync(out+'/before-'+x.surface+'-'+x.width+'x'+x.height+'.png');
      const fresh=fs.readFileSync(out+'/'+x.filename);
      if((x.surface === 'dashboard' || x.surface === 'reports-local') && old.equals(fresh))
        throw new Error('Identical images: '+x.filename);
    }
  }
  console.log(JSON.stringify({phase,reports}));
})().catch(e=>{console.error(e);process.exit(1)});
