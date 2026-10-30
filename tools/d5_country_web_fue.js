/* D5 real Chrome FUE: production Flutter widgets, synthetic identities and IP.
 * Never touches production accounts, remote endpoints or patient health data.
 * Do not treat this as a production-auth/E2E deployment certificate.
 */
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const origin = 'http://127.0.0.1:7385';
const out = 'd5-web-fue-proof';
fs.mkdirSync(out,{recursive:true});
const viewports=[[390,844],[768,1024],[1280,900]];
const cases=[];
const report={head:process.env.GITHUB_SHA||'unknown',
  run:'real Chrome on production Flutter screen widgets + synthetic owner/IP fixture',
  notProven:['production authentication','hosted deployment','real patients'],
  cases,errors:[]};
const copy={
  fr:{language:'Français',confirm:'Confirmer ce pays',start:'Commencer',
    choose:'Choisir mon pays',later:'Plus tard',save:'Enregistrer',
    search:'Rechercher un pays',ma:'Maroc',fr:'France',es:'Espagne'},
  ar:{language:'العربية',confirm:'تأكيد هذا البلد',start:'ابدأ',
    choose:'اختر بلدي',later:'لاحقًا',save:'حفظ',
    search:'ابحث عن بلد',ma:'المغرب',fr:'فرنسا',es:'إسبانيا'},
};
function url(mode,ip,owner,locale) {
  return origin+'/?mode='+mode+'&ip='+ip+'&owner='+owner+'&locale='+locale;
}
const snooze=n=>new Promise(r=>setTimeout(r,n));
async function semantics(page){
  const toggle=page.locator('flt-semantics-placeholder');
  if(await toggle.count()){await toggle.first().focus();await page.keyboard.press('Enter');await snooze(350);}
}
async function find(page,label){
  const locators=[
    page.getByRole('button',{name:label,exact:true}),
    page.getByRole('radio',{name:label,exact:true}),
    page.getByRole('checkbox',{name:label,exact:true}),
    page.getByText(label,{exact:true}),
    page.getByRole('button',{name:label,exact:false}),
    page.getByText(label,{exact:false}),
  ];
  for(const l of locators){
    const n=await l.count();
    for(let i=0;i<n;i++){
      const w=l.nth(i);
      if(await w.isVisible().catch(()=>false))return w;
    }
  }
  return null;
}
async function waitFor(page,label){
  for(let i=0;i<55;i++){
    const x=await find(page,label);if(x)return x;
    await snooze(180);
  }
  throw Error('Missing visible UI label '+label);
}
async function click(page,label){
  const x=await waitFor(page,label);await x.scrollIntoViewIfNeeded();
  await x.click({timeout:4500});await snooze(400);
}
async function capture(page,locale,size,scenario,phase){
  const file=[locale,size[0]+'x'+size[1],scenario,phase].join('-')+'.png';
  await page.screenshot({path:path.join(out,file),animations:'disabled',fullPage:false});
  return file;
}
async function load(page,href,label){
  await page.goto(href,{waitUntil:'domcontentloaded',timeout:40000});
  await snooze(3800);
  await semantics(page);
  await waitFor(page,label);
}
async function visible(page,label){return !!await find(page,label);}
async function countrySelect(page,l,code) {
  const key=code==='FR'?'fr':code==='ES'?'es':'ma';
  const probes=[
    page.getByRole('textbox',{name:/Rechercher un pays|ابحث عن بلد|Pays/}),
    page.getByRole('combobox',{name:/Rechercher un pays|ابحث عن بلد|Pays/}),
    page.getByText(l.search,{exact:false}),
  ];
  let field=null;
  for(const x of probes)if(await x.count()){field=x.first();break;}
  if(!field)throw Error('Missing real country search');
  await field.click({timeout:5000});
  await page.keyboard.insertText(l[key].slice(0,3));
  await snooze(450);
  await click(page,l[key]);
}
async function startState(page,l,width,ready) {
  const btn=await find(page,l.start);
  if(ready){
    if(!btn || !await btn.isEnabled())throw Error('Expected active start CTA');
    const b=await btn.boundingBox();
    if(width<900 && (!b || b.y<0 || b.y+b.height>page.viewportSize().height))
      throw Error('Start CTA not inside mobile browser viewport '+JSON.stringify(b));
  }else{
    if(btn && await btn.isEnabled())
      throw Error('Unconfirmed country incorrectly permits Start');
  }
}
async function scenario(page,locale,size,kind,owner) {
  const [width,height]=size,l=copy[locale];
  const item={locale,viewport:width+'x'+height,kind,owner,pass:false,images:[]};
  try{
    if(kind==='ip_proposal'){
      await load(page,url('new','ma',owner,locale),l.language);
      await click(page,l.language);
      const confirm=await waitFor(page,l.confirm);
      await startState(page,l,width,false);
      item.images.push(await capture(page,locale,size,kind,'before-confirm'));
      // Click an actual accessible Flutter control, never call widget callbacks.
      await confirm.click({timeout:4500});await snooze(450);
      if(await visible(page,l.confirm))throw Error('Proposal not cleared after confirmation');
      await startState(page,l,width,true);
      item.images.push(await capture(page,locale,size,kind,'after-confirm'));
      await click(page,l.start);
      await waitFor(page,'D5_FUE_DASHBOARD');
      item.images.push(await capture(page,locale,size,kind,'saved'));
    } else if(kind==='no_ip'){
      await load(page,url('new','none',owner,locale),l.language);
      await click(page,l.language);
      if(await visible(page,l.confirm))throw Error('Unexpected IP estimate');
      await startState(page,l,width,false);
      item.images.push(await capture(page,locale,size,kind,'country-empty'));
      await countrySelect(page,l,'FR');
      await startState(page,l,width,true);
      item.images.push(await capture(page,locale,size,kind,'manual-selected'));
      await click(page,l.start);
      await waitFor(page,'D5_FUE_DASHBOARD');
    } else if(kind==='legacy_later'){
      await load(page,url('returning','none',owner,locale),l.choose);
      item.images.push(await capture(page,locale,size,kind,'before-later'));
      await click(page,l.later);
      if(await visible(page,l.choose))throw Error('Later did not dismiss reminder');
      item.images.push(await capture(page,locale,size,kind,'after-later'));
    }else throw Error('Unknown scenario');
    item.pass=true;
  }catch(e){
    item.error=String(e.message||e).slice(0,500);
    item.images.push(await capture(page,locale,size,kind,'FAILED').catch(()=>null));
    report.errors.push(item);
  }
  cases.push(item);
  return item.pass;
}
async function isolation(browser){
  // One actual Chrome origin/context: A saves FR; B sees unknown; B saves ES;
  // after reload A still has FR and B still has ES.
  const locale='fr',l=copy.fr,size=[390,844];
  const context=await browser.newContext({
    viewport:{width:size[0],height:size[1]},
    locale:'fr-FR',serviceWorkers:'allow',colorScheme:'light',
  });
  const page=await context.newPage();
  const item={kind:'browser_a_b_a_reload',locale,viewport:'390x844',pass:false,images:[]};
  try{
    await load(page,url('returning','none','a',locale),l.choose);
    await click(page,l.choose);
    await countrySelect(page,l,'FR');await click(page,l.save);
    // Reload A: preference must still belong to A, no legacy prompt.
    await load(page,url('returning','none','a',locale),'IAmina');
    if(await visible(page,l.choose))throw Error('A country lost after reload');
    item.images.push(await capture(page,locale,size,'isolation','a-saved'));
    await load(page,url('returning','none','b',locale),l.choose);
    item.images.push(await capture(page,locale,size,'isolation','b-unknown'));
    await click(page,l.choose);
    await countrySelect(page,l,'ES');await click(page,l.save);
    await load(page,url('returning','none','b',locale),'IAmina');
    if(await visible(page,l.choose))throw Error('B country not restored after reload');
    await load(page,url('returning','none','a',locale),'IAmina');
    if(await visible(page,l.choose))throw Error('B overwrote A');
    item.images.push(await capture(page,locale,size,'isolation','a-reloaded'));
    item.pass=true;
  }catch(e){
    item.error=String(e.message||e).slice(0,500);
    item.images.push(await capture(page,locale,size,'isolation','FAILED').catch(()=>null));
    report.errors.push(item);
  }finally{
    cases.push(item);await context.close();
  }
}
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--force-renderer-accessibility']});
  try{
    for(const locale of ['fr','ar']){
      for(const size of viewports){
        for(const kind of ['ip_proposal','no_ip','legacy_later']){
          const context=await browser.newContext({
            viewport:{width:size[0],height:size[1]},locale:locale==='ar'?'ar-MA':'fr-FR',
            serviceWorkers:'allow',colorScheme:'light',
          });
          const page=await context.newPage();
          const errors=[];
          page.on('pageerror',e=>errors.push(String(e.message||e).slice(0,160)));
          await scenario(page,locale,size,kind,'a');
          if(errors.length){const latest=cases[cases.length-1];latest.pass=false;
            latest.browserErrors=errors;report.errors.push(latest);}
          await context.close();
        }
      }
    }
    await isolation(browser);
  }finally{await browser.close();}
  report.requiredCount=19;
  report.passed=cases.filter(x=>x.pass).length;
  report.fuePass=report.passed===19&&report.errors.length===0;
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));
  console.log('D5_WEB_FUE='+JSON.stringify({passed:report.passed,total:report.requiredCount,
    failed:report.errors.map(x=>({kind:x.kind,locale:x.locale,viewport:x.viewport,error:x.error}))}));
  if(!report.fuePass)process.exitCode=1;
})().catch(e=>{console.error('D5 FUE harness error: '+String(e.message||e));process.exitCode=1;});
