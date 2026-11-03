// Synthetic Web photo-consent proof: real Chromium + real Flutter widget.
// Never calls a model provider or writes patient data. All pages use seed=0.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = process.env.D14_OUTPUT_DIR || 'd14-web-cert';
fs.mkdirSync(root, {recursive: true});
const viewports = [
  {name:'mobile',width:390,height:844},
  {name:'tablet',width:768,height:1024},
  {name:'desktop',width:1280,height:900},
];
const locales = ['fr','ar'];
const scenarios = ['off','proposal','revoke-pending','revoke-proposal','reconsent'];
const beforeOrigin = process.env.D14_BEFORE_URL || 'http://127.0.0.1:7358';
const afterOrigin = process.env.D14_AFTER_URL || 'http://127.0.0.1:7359';
const report = {base:process.env.D14_BASE_SHA||null,head:process.env.D14_HEAD_SHA||null,viewports:{},scenarios:[], errors:[]};

function fail(msg) { throw new Error(msg); }
function assertScenario(s, label) {
  if(s.step !== 'done') fail(label + ': fixture error or incomplete ' + JSON.stringify(s));
  if(s.fixtureOnly !== true || s.externalProviderCalls !== 0) fail(label + ': provider/no-PHI proof unavailable');
  if(s.selectedIds.length) fail(label + ': artificial proposal mutated meal items automatically');
  if(s.scenario === 'off' && (s.allowed || s.recognitionCalls !== 0 || s.proposalVisible)) fail(label+': OFF not enforced');
  if(s.scenario === 'proposal' && (!s.allowed || s.recognitionCalls !== 1 || !s.proposalVisible)) fail(label+': proposal not confirmed as draft-only');
  if(s.scenario === 'revoke-pending' && (s.allowed || s.recognitionCalls !== 1 || s.proposalVisible)) fail(label+': late response after revoke surfaced');
  if(s.scenario === 'revoke-proposal' && (s.allowed || !s.proposalSeenBeforeRevocation || s.proposalVisible)) fail(label+': existing proposal not cleared');
  if(s.scenario === 'reconsent' && (!s.allowed || s.recognitionCalls !== 2 || !s.proposalVisible)) fail(label+': reconsent request contaminated by stale result');
  if(s.locale === 'ar' && s.direction !== 'rtl') fail(label+': Arabic layout not RTL');
  if(s.locale === 'fr' && s.direction !== 'ltr') fail(label+': French layout not LTR');
}
async function load(browser, origin, query, viewport, locale, name, synthetic) {
  const ctx=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:locale==='ar'?'ar-MA':'fr-FR'});
  const page=await ctx.newPage();
  const fatalErrors=[];
  const providerRequests=[];
  const offOriginRequests=[];
  const allowedOrigins = new Set([new URL(beforeOrigin).origin, new URL(afterOrigin).origin]);
  page.on('pageerror', error=>fatalErrors.push(String(error)));
  page.on('request', request=>{
    const url=request.url();
    if (/generativelanguage\.googleapis\.com|api\.groq\.com|\/api\/v1\/ai\//.test(url))
      providerRequests.push('AI_REQUEST_DENIED');
  });
  await page.route('**/*', async route=>{
    const url=route.request().url();
    if(url.startsWith('data:')||url.startsWith('blob:'))return route.continue();
    if(/^https?:/.test(url)&&!allowedOrigins.has(new URL(url).origin)){
      const remote=new URL(url);
      offOriginRequests.push(remote.origin);
      // BEFORE is historic main without the new bootstrap setting. Satisfy its
      // known Google font requests from bundled local fonts to avoid any actual
      // third-party request by this synthetic comparison job.
      if(origin===beforeOrigin && remote.hostname==='fonts.gstatic.com'){
        const basename=remote.pathname.includes('/notosansarabic/')
          ? 'NotoSansArabic.ttf'
          : remote.pathname.includes('/notosanssymbols/')
          ? 'NotoSansSymbols.ttf' : null;
        if(basename){
          const local=await ctx.request.get(origin+'/assets/assets/fonts/'+basename);
          if(local.ok())return route.fulfill({
            status:200,body:await local.body(),contentType:'application/octet-stream',
          });
        }
      }
      return route.abort();
    }
    return route.continue();
  });
  try {
    const url=origin+'/?'+new URLSearchParams({surface:synthetic?'d14-photo-cert':'meal-picker',locale,seed:'0',...(synthetic?{scenario:query}:{})}).toString();
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForSelector('flutter-view',{timeout:60000});
    let state=null;
    if (synthetic) {
      try {
        await page.waitForFunction(()=>{
          try {
            const s=JSON.parse(globalThis.d14BrowserCert||'{}');
            return s.step==='done'||s.step==='error';
          }catch{return false;}
        },null,{timeout:60000});
      } catch(e){
        const x=await page.evaluate(()=>globalThis.d14BrowserCert||null);
        fail(name+': D14 status timeout '+JSON.stringify(x)+' / '+String(e));
      }
      state=await page.evaluate(()=>JSON.parse(globalThis.d14BrowserCert));
      assertScenario(state,name);
      await page.waitForTimeout(450);
    } else {
      // Existing audit surface: wait for Web font, local database and catalog.
      await page.waitForTimeout(11000);
    }
    const target=path.join(root,name+'.png');
    await page.screenshot({path:target,fullPage:false});
    if(fs.statSync(target).size<10000) fail(name+': suspicious blank screenshot');
    if(fatalErrors.length) fail(name+': JS pageerror '+fatalErrors.join('; '));
    if(providerRequests.length) fail(name+': forbidden provider request');
    // BEFORE is a historical baseline; reject external requests on candidate only.
    if(origin===afterOrigin && offOriginRequests.length)
      fail(name+': Web candidate attempted external font/other request: '+JSON.stringify([...new Set(offOriginRequests)]));
    return {image:target,size:fs.statSync(target).size,state,providerRequests:providerRequests.length,offOriginRequestCount:offOriginRequests.length};
  }finally{await ctx.close();}
}
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader']});
  try {
    for(const vp of viewports){
      for(const locale of locales){
        const id=vp.name+'-'+locale+'-'+vp.width+'x'+vp.height;
        const before=await load(browser,beforeOrigin,null,vp,locale,'before-'+id,false);
        const after=await load(browser,afterOrigin,null,vp,locale,'after-'+id,false);
        report.viewports[id]={before:before.image,after:after.image,bytesBefore:before.size,bytesAfter:after.size};
        for(const scenario of scenarios){
          const result=await load(browser,afterOrigin,scenario,vp,locale,scenario+'-'+id,true);
          report.scenarios.push({id:scenario+'-'+id,case:scenario,viewport:vp.name,locale,...result});
        }
        fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify(report,null,2));
      }
    }
    console.log('D14 real Chrome scenarios PASS: '+report.scenarios.length+' / 30');
    console.log('D14 before/after screenshot pairs: '+Object.keys(report.viewports).length+' / 6');
  }finally{await browser.close();}
})().catch(err=>{
  report.errors.push(String(err));
  fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify(report,null,2));
  console.error(err);
  process.exit(1);
});
