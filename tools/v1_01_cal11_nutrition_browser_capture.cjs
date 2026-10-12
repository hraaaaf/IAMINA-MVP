// Strict CAL-11 real-Chromium image evidence: identical fixture, locale and viewport.
const {chromium} = require('playwright');
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const out = process.env.AUDIT_OUT;
const phase = process.env.AUDIT_PHASE;
if (!out || !['before','after'].includes(phase)) throw new Error('AUDIT_OUT / AUDIT_PHASE required');
fs.mkdirSync(out,{recursive:true});
const interval = phase === 'before' ? '14.2–15.7' : '14.1–15.7';
const viewports = [[390,844],[768,1024],[1280,900]];
const languages = ['fr','en','ar'];

async function render(browser, lang, width, height) {
  const context = await browser.newContext({
    viewport:{width,height}, deviceScaleFactor:1,
    locale:lang === 'ar' ? 'ar-MA' : lang === 'fr' ? 'fr-FR' : 'en-US',
    serviceWorkers:'block', colorScheme:'light'
  });
  try {
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:7367/?locale='+lang,
      {waitUntil:'domcontentloaded',timeout:30000});
    // CanvasKit semantics are disabled until engine startup and keyboard activation.
    await page.waitForTimeout(9000);
    const placeholder=page.locator('flt-semantics-placeholder');
    if (await placeholder.count()) {
      await placeholder.first().focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(800);
    }
    const sample = async() => page.locator('flt-semantics').evaluateAll(
      els => els.map(e => [(e.getAttribute('aria-label')||''),(e.textContent||'')].join(' ')).join(' ')
    ).catch(()=>'');
    let evidence='';
    for (let tries=0;tries<40;tries++) {
      evidence=await sample();
      if (evidence.includes(interval) && evidence.includes('USDA')) break;
      await page.waitForTimeout(350);
    }
    if (!evidence.includes(interval) || !evidence.includes('USDA')) {
      const diagnostic=path.join(out,'diagnostic-'+phase+'-'+lang+'-'+width+'x'+height+'.png');
      await page.screenshot({path:diagnostic,fullPage:false});
      throw new Error('Missing visible source-backed interval: '+phase+' '+lang+' '+width+'x'+height+
        '; expected='+interval+'; semantics='+evidence.slice(0,1800)+'; errors='+JSON.stringify(errors));
    }
    if(errors.length) console.warn('NON-FATAL-BROWSER-PAGEERROR: '+JSON.stringify(errors));
    const filename=phase+'-apple-100g-'+lang+'-'+width+'x'+height+'.png';
    const bytes=await page.screenshot({path:path.join(out,filename),fullPage:false});
    if(bytes.length < 4000 || bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')
      throw new Error('PNG integrity failed: '+filename);
    if(bytes.readUInt32BE(16)!==width || bytes.readUInt32BE(20)!==height)
      throw new Error('PNG viewport mismatch: '+filename);
    return {phase,lang,width,height,expectedInterval:interval,filename,
      bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
      pageErrors:errors};
  } finally {await context.close();}
}
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const results=[];
  try {
    for(const lang of languages) for(const [w,h] of viewports)
      results.push(await render(browser,lang,w,h));
  } finally {await browser.close();}
  if(phase==='after') {
    for(const row of results) {
      const before=path.join(out,'before-apple-100g-'+row.lang+'-'+row.width+'x'+row.height+'.png');
      if(!fs.existsSync(before)) throw new Error('Missing BEFORE PNG: '+before);
      if(fs.readFileSync(before).equals(fs.readFileSync(path.join(out,row.filename))))
        throw new Error('Before/after screenshots unexpectedly identical: '+row.filename);
    }
  }
  fs.writeFileSync(path.join(out,phase+'-observations.json'),JSON.stringify({
    phase, expectedInterval:interval, results,
    qualification:'Real headless Chromium captures of identical product widget; human visual inspection pending'
  },null,2));
  console.log(JSON.stringify({phase,results},null,2));
})().catch(e=>{console.error(e);process.exit(1)});
