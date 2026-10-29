/* D19 CI: real AuthService native token, Django PG16 clinical endpoints,
 * actual Flutter AISummaryScreen. Synthetic accounts, local-only networking.
 */
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const origin='http://127.0.0.1:7383', api='http://127.0.0.1:8000';
const directory='d19-real-auth-web-proof';
fs.mkdirSync(directory,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true});
 const report={scope:'Flutter AuthService + ApiClient + scoped IndexedDB + Django PG16',hosted_vercel:'NOT_RUN',patient_data:'synthetic',tests:[],failed:[]};
 try{
  for(const locale of ['fr','ar']){
   for(const viewport of [{width:390,height:844},{width:768,height:1024},{width:1280,height:900}]){
   const context=await browser.newContext({viewport,locale:locale==='fr'?'fr-FR':'ar-MA',serviceWorkers:'block'});
   for(const principal of ['a','b','a']){
    const page=await context.newPage();
    const errors=[],external=[],requests=[],loginStatuses=[],loginTransportFailures=[];
    page.on('pageerror',e=>errors.push(e.message.slice(0,300)));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text().slice(0,300));});
    page.on('response',r=>{
      if(r.url().startsWith(api+'/api/v1/auth/login'))
        loginStatuses.push(r.status());
    });
    page.on('requestfailed',r=>{
      if(r.url().startsWith(api+'/api/v1/auth/login'))
        loginTransportFailures.push('auth login transport failed');
    });
    page.on('request',r=>{
      if(r.url().startsWith(api) && /\/api\/v1\/(ai\/summary|kpis\/)/.test(r.url()))
        requests.push(r.url().split('?')[0]);
    });
    await page.route('**/*',route=>{
      const u=route.request().url();
      if(u.startsWith(origin)||u.startsWith(api)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
      external.push('blocked external resource');return route.abort();
    });
    await page.goto(origin+'/?principal='+principal+'&locale='+locale,{waitUntil:'load',timeout:60000});
    let title='';
    try{
      await page.waitForFunction(()=>/^IAMINA_D19_REAL_HTTP_(A|B)_PASS$/.test(document.title)||document.title.startsWith('IAMINA_D19_REAL_HTTP_FAIL:'),{timeout:90000});
      title=await page.title();
    }catch(e){title=await page.title();}
    await page.waitForTimeout(4200);
    const target='IAMINA_D19_REAL_HTTP_'+principal.toUpperCase()+'_PASS';
    const file=locale+'-'+viewport.width+'-'+principal+'-'+report.tests.length+'.png';
    await page.screenshot({path:path.join(directory,file)});
    const observation={locale,viewport:viewport.width+'x'+viewport.height,principal,expectedTitle:target,
      pass:title===target&&requests.length>=4&&errors.length===0&&external.length===0,
      backendRequestCount:requests.length,loginStatuses,loginTransportFailures:loginTransportFailures.length,consoleErrors:errors.length,
      blockedExternal:external.length,file};
    report.tests.push(observation);
    if(!observation.pass)report.failed.push({...observation,actualTitle:title});
    await page.close();
   }
   await context.close();
   }
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(directory,'report.json'),JSON.stringify(report,null,2));
 console.log('D19_NATIVE_WEB_HTTP='+JSON.stringify({passed:report.tests.filter(x=>x.pass).length,total:report.tests.length,failed:report.failed.map(x=>({locale:x.locale,principal:x.principal,title:x.actualTitle,loginStatuses:x.loginStatuses,loginTransportFailures:x.loginTransportFailures,requests:x.backendRequestCount,errors:x.consoleErrors,external:x.blockedExternal}))}));
 if(report.failed.length||report.tests.length!==18)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
