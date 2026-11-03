/* D14 real browser proof: ephemeral Django/PostgreSQL native auth A→B→A,
 * actual Flutter MealCapturePanel and owner-vault switching, zero AI egress.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const origin = 'http://127.0.0.1:7387';
const api = 'http://127.0.0.1:8000';
const root = 'd14-real-auth-photo-proof';
fs.mkdirSync(root,{recursive:true});
const report={
  scope:'real Flutter AuthService, Django PG16 native login, patient-scoped Web SQLite, actual MealCapturePanel',
  photo:'only synthetic in-memory Future, no uploaded image',
  patientData:'disposable CI-only account identities, no clinical records',
  providerCalls:0,
  fontPrivacyGate:'UNRESOLVED_IF_FALLBACK_ATTEMPTED',
  vercel:'NOT_DEPLOYED',
  cases:[],
  failures:[]
};
const sizes=[{width:390,height:844},{width:768,height:1024},{width:1280,height:900}];
const ciLocale = process.env.D14_CI_LOCALE;
if(!['fr','ar'].includes(ciLocale)) throw new Error('D14_CI_LOCALE must be fr or ar');
const steps=[
  'A_REAL_LOGIN_AND_PENDING_SYNTHETIC_PHOTO',
  'B_REAL_LOGIN_PHOTO_DENIED',
  'A_LATE_RESULT_NOT_VISIBLE_IN_B',
  'LOGOUT_VAULT_CLOSED',
  'A_REAL_RETURN_OFF_AND_CLEAN'
];
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try{
    for(const locale of [ciLocale]){
      for(const viewport of sizes){
        const ctx=await browser.newContext({
          viewport,locale:locale==='ar'?'ar-MA':'fr-FR',
          deviceScaleFactor:1,serviceWorkers:'block'
        });
        const page=await ctx.newPage();
        const external=[],externalResponses=[],photoUploads=[],errors=[],authResponses=[];
        page.on('pageerror',e=>errors.push('pageerror: '+String(e)));
        page.on('response',r=>{
          if(r.url().startsWith(api+'/api/v1/auth/login'))authResponses.push(r.status());
          if(/^https?:/.test(r.url())&&!r.url().startsWith(origin)&&
              !r.url().startsWith(api))externalResponses.push(new URL(r.url()).origin);
        });
        await page.addInitScript(()=>{
          window.__d14AuthReports=[];
          window.addEventListener('message',event=>{
            if(typeof event.data==='string'){
              try{
                const j=JSON.parse(event.data);
                if(j.kind==='IAMINA_D14_REAL_AUTH_REPORT')window.__d14AuthReports.push(j);
              }catch{}
            }
          });
        });
        await page.route('**/*',route=>{
          const url=route.request().url();
          if(url.startsWith(api+'/api/v1/ai/')||/generativelanguage|api\.groq\.com|api\.openai\.com/.test(url)){
            photoUploads.push(new URL(url).origin);
            return route.abort(); // No synthetic image may reach the server or vendor.
          }
          if(url.startsWith(origin)||url.startsWith(api)||
              url.startsWith('data:')||url.startsWith('blob:'))
            return route.continue();
          try {
            const u=new URL(url);
            // Diagnostics exclude credentials, query strings and page payload.
            external.push(u.origin);
          }catch{
            external.push('non-http-scheme');
          }
          return route.abort();
        });
        const name=locale+'-'+viewport.width+'x'+viewport.height;
        try {
          await page.goto(origin+'/?locale='+locale,{waitUntil:'domcontentloaded',timeout:60000});
          await page.waitForFunction(()=>{
            const t=document.title;
            return t==='IAMINA_D14_REAL_AUTH_PASS'||
              t.startsWith('IAMINA_D14_REAL_AUTH_FAIL:');
          },null,{timeout:90000});
          const title=await page.title();
          const details=await page.evaluate(()=>window.__d14AuthReports||[]);
          const item=details.at(-1)||{};
          const screenshot=name+'.png';
          await page.screenshot({path:path.join(root,screenshot),fullPage:false});
          const valid=title==='IAMINA_D14_REAL_AUTH_PASS'&&
            item.status==='PASS'&&
            JSON.stringify(item.steps)===JSON.stringify(steps)&&
            item.photoCalls===1&&item.providerCalls===0&&
            item.clinicalTransport==='disabled'&&
            item.realDjangoAuth===true&&item.realPatientVault===true&&
            JSON.stringify(authResponses)===JSON.stringify([200,200,200])&&
            external.every(x=>x==='https://fonts.gstatic.com')&&
            externalResponses.length===0&&photoUploads.length===0&&errors.length===0&&
            fs.statSync(path.join(root,screenshot)).size>=10000;
          const result={
            locale,viewport,screenshot,passed:valid,steps:item.steps||[],
            nativeLoginStatuses:authResponses,providerRequests:photoUploads.length,
            blockedExternal:external.length,
            blockedExternalOrigins:[...new Set(external)].sort(),
            attemptedFlutterFontFallbacks:external.filter(
              x=>x==='https://fonts.gstatic.com').length,
            remoteResponses:externalResponses.length,
            fontPrivacyGate:external.length?'OPEN_UNRESOLVED':'PASS',
            pageErrors:errors.length,
            finalTitle:title,reason:item.reason||null
          };
          report.cases.push(result);
          if(!valid)report.failures.push(result);
          console.log('D14_NATIVE_AUTH_'+name+'='+ (valid?'PASS':'FAIL'));
        }catch(e){
          report.failures.push({locale,viewport,error:String(e),
            title:await page.title(),nativeLoginStatuses:authResponses,
            errors,providerRequests:photoUploads.length});
        }finally{
          await ctx.close();
        }
        fs.writeFileSync(path.join(root,'report.json'),JSON.stringify(report,null,2));
      }
    }
  }finally{await browser.close();}
  console.log('D14_REAL_AUTH_CHROME='+JSON.stringify({
    passed:report.cases.filter(x=>x.passed).length,
    total:report.cases.length,failures:report.failures.length,
    attemptedFontFallbacks:report.cases.reduce((n,c)=>n+(c.attemptedFlutterFontFallbacks||0),0),
    providerRequests:report.providerCalls
  }));
  if(report.cases.length!==3||report.failures.length)process.exitCode=1;
})().catch(e=>{
  report.failures.push({error:String(e)});
  fs.writeFileSync(path.join(root,'report.json'),JSON.stringify(report,null,2));
  console.error(e);
  process.exitCode=1;
});
