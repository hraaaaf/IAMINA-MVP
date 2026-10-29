// Post-merge synthetic Flutter Web AR/RTL visual + interaction certificate.
// Never requests a patient account, uploads health data, or bypasses auth.
const { chromium } = require('playwright');
const fs = require('fs');
const out = process.env.AUDIT_OUT || 'onboarding-ar-rtl-proof';
const base = process.env.AUDIT_URL || 'http://127.0.0.1:7366';
fs.mkdirSync(out, {recursive:true});
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function enableSemantics(page) {
  const toggle = page.locator('flt-semantics-placeholder');
  if (await toggle.count()) {
    await toggle.first().focus();
    await page.keyboard.press('Enter');
    await sleep(350);
  }
}

function candidates(page, label) {
  return [
    page.getByRole('checkbox', {name:label, exact:false}),
    page.getByRole('button', {name:label, exact:false}),
    page.getByRole('radio', {name:label, exact:false}),
    page.getByText(label, {exact:true}),
    page.getByText(label, {exact:false}),
  ];
}

async function locate(page, label) {
  for (const query of candidates(page,label)) {
    for (let n=0; n<await query.count(); n++) {
      const control=query.nth(n);
      if (!(await control.isVisible().catch(()=>false))) continue;
      const rect=await control.boundingBox().catch(()=>null);
      if (rect && rect.width>0 && rect.height>0) return {control, rect};
    }
  }
  return null;
}

async function choose(page,label,opts={}) {
  for (let tryNo=0; tryNo<35; tryNo++) {
    const found=await locate(page,label);
    if (found) {
      if (opts.scroll!==false) await found.control.scrollIntoViewIfNeeded();
      await found.control.click({timeout:2500});
      await sleep(400);
      return;
    }
    await sleep(250);
  }
  throw new Error('Missing Arabic onboarding control: '+label);
}

async function screenshot(page,name,size) {
  await page.screenshot({path:out+'/'+name+'-'+size[0]+'x'+size[1]+'.png',fullPage:false});
}

async function mustBeInViewport(page,label,size,name) {
  const obj=await locate(page,label);
  if (!obj || obj.rect.y<-1 || obj.rect.y>size[1]-54 ||
      obj.rect.x<-1 || obj.rect.x>size[0]-12) {
    throw new Error('Arabic RTL step not revealed '+JSON.stringify({label,size,rect:obj?.rect||null}));
  }
  await screenshot(page,name,size);
  return obj.rect;
}

(async () => {
  const browser = await chromium.launch({
    headless:true,args:['--force-renderer-accessibility']
  });
  const results=[];
  try {
    for (const size of [[390,844],[768,1024],[1280,900]]) {
      const [width,height]=size;
      const context=await browser.newContext({
        viewport:{width,height},locale:'ar-MA',
        deviceScaleFactor:1,colorScheme:'light',serviceWorkers:'block',
      });
      try {
        const page=await context.newPage();
        const exceptions=[];
        page.on('pageerror',e=>exceptions.push(String(e)));
        await page.goto(base+'/?surface=onboarding&seed=0&locale=ar',{
          waitUntil:'domcontentloaded',timeout:30000,
        });
        await sleep(6500);
        await enableSemantics(page);
        await mustBeInViewport(page,'العربية',size,'arabic-initial');
        await choose(page,'العربية');
        await sleep(450);
        const countryProbes=[
          page.getByRole('textbox',{name:/ابحث عن بلد|اكتب اسم البلد/}),
          page.getByRole('combobox',{name:/ابحث عن بلد|اكتب اسم البلد/}),
          page.getByText('ابحث عن بلد',{exact:false}),
        ];
        let country=null;
        for (const probe of countryProbes) {
          if (!(await probe.count())) continue;
          const el=probe.first();
          const rect=await el.boundingBox().catch(()=>null);
          if (rect){country={el,rect};break;}
        }
        if (!country || country.rect.y<0 || country.rect.y>height-55)
          throw new Error('Arabic country input not visible after language '+JSON.stringify({size,country:country?.rect}));
        await screenshot(page,'arabic-country-revealed',size);
        await country.el.click();
        // insertText is Unicode-safe for Arabic search on Chrome/Flutter.
        await page.keyboard.insertText('المغر');
        await sleep(400);
        await screenshot(page,'arabic-country-search',size);
        await choose(page,'المغرب');
        await sleep(450);
        if(width<900)
          await mustBeInViewport(page,'السكري النوع 2',size,'arabic-type-revealed');
        else
          await screenshot(page,'arabic-type-desktop',size);
        await choose(page,'السكري النوع 2');
        await sleep(450);
        if(width<900)
          await mustBeInViewport(page,'أدوية فموية أتناولها',size,'arabic-treatment-revealed');
        else
          await screenshot(page,'arabic-treatment-desktop',size);
        // Multi-choice: each chip must remain patient-driven, not auto-advance.
        await choose(page,'أدوية فموية أتناولها');
        await choose(page,'نمط الحياة');
        const continueLink=await locate(page,'المتابعة إلى الوحدات');
        if(width<900){
          if(!continueLink)throw new Error('Missing Arabic explicit unit continuation');
          await continueLink.control.click({timeout:2500});
          await sleep(450);
          await mustBeInViewport(page,'mg/dL',size,'arabic-units-revealed');
        }else{
          if(continueLink)throw new Error('Redundant continuation on RTL desktop');
          await screenshot(page,'arabic-units-desktop',size);
        }
        const start=await locate(page,'ابدأ');
        if(!start)throw new Error('Missing Arabic start CTA');
        const rect=start.rect;
        if(rect.x<0 || rect.y<0 || rect.x+rect.width>width+1 ||
           rect.y+rect.height>height+1)
           throw new Error('Arabic start CTA clipped '+JSON.stringify({size,rect}));
        await screenshot(page,'arabic-final',size);
        if(exceptions.length) throw new Error('Flutter Web uncaught browser exceptions: '+exceptions.join(' | '));
        results.push({width,height,locale:'ar',country:'MA',
          type:'type2',treatmentChips:2,unitsAdvanced:width<900,
          ctaRect:rect,pageErrors:exceptions.length});
      }finally{await context.close()}
    }
    fs.writeFileSync(out+'/result.json',JSON.stringify({
      ok:true,origin:'synthetic Flutter Web browser harness',
      ref:'main@07477defc3ad pre-test',rtl:'Arabic Flutter locale plus widget Directionality',
      results,
    },null,2));
    console.log(JSON.stringify(results));
  }finally{await browser.close()}
})().catch(e=>{
  fs.writeFileSync(out+'/failure.txt',String(e.stack||e));
  console.error(e);
  process.exit(1);
});