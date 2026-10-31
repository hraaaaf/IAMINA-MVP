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
const report={head:process.env.D5_CANDIDATE_SHA||process.env.GITHUB_SHA||'unknown',
  run:'real Chrome on production Flutter screen widgets + synthetic owner/IP fixture',
  notProven:['production authentication','hosted deployment','real patients'],
  cases,errors:[]};
const copy={
  fr:{language:'Français',confirm:'Confirmer ce pays',start:'Commencer',
    choose:'Choisir mon pays',later:'Plus tard',save:'Enregistrer',
    profile:'Mon Profil',preferences:'Langue et pays',
    search:'Rechercher un pays',ma:'Maroc',fr:'France',es:'Espagne'},
  ar:{language:'العربية',confirm:'تأكيد هذا البلد',start:'ابدأ',
    choose:'اختر بلدي',later:'لاحقًا',save:'حفظ',
    profile:'ملفي الشخصي',preferences:'اللغة والبلد',
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
// Verify the *real* selected value after reload, via a pointer-focused
// Flutter editor. On Chrome CanvasKit, a selected dropdown stops exposing its
// placeholder/label to Playwright; getByText('Rechercher un pays') is therefore
// NOT a valid locator once France/Espagne has been selected. No fake callbacks,
// DOM assignments, synthetic storage mutations, or country defaults.
async function assertSelectedCountry(page,expected) {
  const size=page.viewportSize();
  if(size.width!==390 || size.height!==844)
    throw Error('Country reload visual oracle requires certified 390x844 viewport');
  let didClick=false;
  const editors=page.getByRole('textbox');
  for(let i=0;i<await editors.count();i++){
    const editor=editors.nth(i);
    if(!await editor.isVisible().catch(()=>false)) continue;
    const rect=await editor.boundingBox().catch(()=>null);
    if(rect && rect.y>280 && rect.y<380){
      await editor.click({timeout:5000});
      didClick=true;
      break;
    }
  }
  if(!didClick){
    // Grounded in the archived exact 390x844 Chrome capture: the live
    // dropdown rectangle is x=20..328, y=307..354 (click x=94,y=330).
    // A real mouse click is essential: do not programmatically focus inputs.
    await page.mouse.click(94,330);
  }
  let observed={active:null,values:[],semantics:[]};
  for(let n=0;n<40;n++){
    observed=await page.evaluate(()=>{
      const active=document.activeElement;
      const inputs=[...document.querySelectorAll('input,textarea')];
      return {
        active:('value' in active)?active.value:null,
        values:inputs.map(x=>x.value||'').filter(Boolean).slice(0,12),
        semantics:[...document.querySelectorAll('flt-semantics')]
          .map(x=>x.getAttribute('aria-label')||x.getAttribute('aria-valuetext')||'')
          .filter(x=>x.includes('France')||x.includes('Espagne')).slice(0,10),
      };
    });
    if(observed.active===expected || observed.values.includes(expected))
      return;
    await snooze(150);
  }
  throw Error('Selected country mismatch after real pointer focus: expected '+
    expected+' observed='+JSON.stringify(observed).slice(0,650));
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
  const pageErrors=[], failedRequests=[], consoleErrors=[], resources=[];
  page.on('response',r=>{
    const url=new URL(r.url());
    if(['/', '/index.html','/main.dart.js','/flutter_bootstrap.js',
      '/drift_worker.js','/sqlite3.wasm'].includes(url.pathname)){
      resources.push({path:url.pathname,status:r.status(),fromSW:r.fromServiceWorker()});
    }
  });
  page.on('pageerror',e=>pageErrors.push({
    message:String(e.message||e).slice(0,500),
    stack:String(e.stack||'').slice(0,1600),
    name:String(e.name||'').slice(0,100),
  }));
  page.on('crash',()=>pageErrors.push({name:'page-crash'}));
  page.on('requestfailed',r=>failedRequests.push({
    path:new URL(r.url()).pathname.slice(0,130),
    failure:r.failure()?.errorText||'unknown',
  }));
  page.on('console',msg=>{
    if(msg.type()==='error')consoleErrors.push(msg.text().slice(0,260));
  });
  const item={kind:'browser_a_b_a_reload',locale,viewport:'390x844',
    stage:'initial',pass:false,images:[]};
  try{
    item.stage='A first entry';
    await load(page,url('returning','none','a',locale),l.choose);
    await click(page,l.choose);
    await countrySelect(page,l,'FR');await click(page,l.save);
    // The real Profile title is "Mon Profil", not "IAmina".
    item.stage='A reloaded';
    await load(page,url('returning','none','a',locale),l.profile);
    if(await visible(page,l.choose))throw Error('A country lost after reload');
    item.images.push(await capture(page,locale,size,'isolation','a-saved'));
    item.stage='A restored FR';
    await click(page,l.preferences);
    await assertSelectedCountry(page,l.fr);
    item.stage='B initial unknown';
    await load(page,url('returning','none','b',locale),l.choose);
    item.images.push(await capture(page,locale,size,'isolation','b-unknown'));
    await click(page,l.choose);
    await countrySelect(page,l,'ES');await click(page,l.save);
    item.stage='B reloaded';
    await load(page,url('returning','none','b',locale),l.profile);
    if(await visible(page,l.choose))throw Error('B country not restored after reload');
    item.stage='B restored ES';
    await click(page,l.preferences);
    await assertSelectedCountry(page,l.es);
    item.stage='A after B';
    await load(page,url('returning','none','a',locale),l.profile);
    if(await visible(page,l.choose))throw Error('B overwrote A');
    item.images.push(await capture(page,locale,size,'isolation','a-reloaded'));
    item.stage='A still FR';
    await click(page,l.preferences);
    await assertSelectedCountry(page,l.fr);
    if(pageErrors.length)throw Error('Browser page exceptions: '+pageErrors.join('; '));
    item.pass=true;
  }catch(e){
    item.error=String(e.message||e).slice(0,500);
    item.pageErrors=pageErrors.slice(-5);
    item.consoleErrors=consoleErrors.slice(-5);
    item.failedRequests=failedRequests.slice(-5);
    item.lastUrl=page.url();
    item.resources=resources.slice(-35);
    item.browserSnapshot=await page.evaluate(()=>({
      title:document.title,
      bodyText:document.body?.innerText?.slice(0,750)||'',
      flutterSemantics:[...document.querySelectorAll('flt-semantics')]
        .slice(0,12).map(x=>(x.getAttribute('aria-label')||x.textContent||'').slice(0,120)),
      documentState:document.readyState,
      scriptCount:document.scripts.length,
      serviceWorkerControlled:!!navigator.serviceWorker?.controller,
      flutterSurfaceCount:document.querySelectorAll('flt-glass-pane').length,
      flutterLoaderPresent:!!window._flutter,
      flutterInitStage:document.documentElement?.dataset?.d5Stage||null,
      flutterFrameworkError:document.documentElement?.dataset?.d5FlutterError||null,
      flutterBootstrapError:document.documentElement?.dataset?.d5BootError||null,
      cacheKeys:[], // Cache content inspected separately; no clinical content.
    })).catch(e=>({inspectError:String(e.message||e).slice(0,180)}));
    item.images.push(await capture(page,locale,size,'isolation','FAILED').catch(()=>null));
    // Diagnostic only: do not mark the case PASS. Preserve IndexedDB, but
    // remove the local PWA service worker and compare the same A account on a
    // network navigation. This distinguishes cache interception from a
    // persisted-data/Flutter initialization failure without relaxing the gate.
    if(item.stage==='A reloaded' && item.browserSnapshot?.serviceWorkerControlled){
      try{
        item.swBypassProbe={tried:true};
        await page.evaluate(async()=>{
          const registrations=await navigator.serviceWorker.getRegistrations();
          await Promise.all(registrations.map(r=>r.unregister()));
          const keys=await caches.keys();
          await Promise.all(keys.map(k=>caches.delete(k)));
        });
        await page.goto(url('returning','none','a',locale),{
          waitUntil:'domcontentloaded',timeout:30000
        });
        await snooze(4600);
        await semantics(page);
        item.swBypassProbe={tried:true,restored:!!await find(page,l.profile),
          title:await page.title(),
          initStage:await page.evaluate(()=>document.documentElement?.dataset?.d5Stage||null),
          frameworkError:await page.evaluate(()=>
            document.documentElement?.dataset?.d5FlutterError||null),
          failures:failedRequests.slice(-5)};
        item.images.push(await capture(page,locale,size,'isolation','SW_BYPASS_PROBE').catch(()=>null));
      }catch(probeError){
        item.swBypassProbe={tried:true,error:String(probeError.message||probeError).slice(0,250)};
      }
    }
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
    failed:report.errors.map(x=>({kind:x.kind,locale:x.locale,viewport:x.viewport,
      stage:x.stage,error:x.error,errors:x.pageErrors,console:x.consoleErrors,
      requests:x.failedRequests,resources:x.resources,dom:x.browserSnapshot,
      swBypassProbe:x.swBypassProbe}))}));
  if(!report.fuePass)process.exitCode=1;
})().catch(e=>{console.error('D5 FUE harness error: '+String(e.message||e));process.exitCode=1;});
