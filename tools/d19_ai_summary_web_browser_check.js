/* D19 real Chrome *actual AISummaryScreen* synthetic visual FUE.
 * No patient session, no external network or LLM; GET requests are all local.
 */
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const out = path.resolve(process.env.D19_AI_WEB_OUT || 'd19-ai-summary-browser');
const origin = process.env.D19_AI_WEB_ORIGIN || 'http://127.0.0.1:7358';
fs.mkdirSync(out, { recursive: true });
const viewports = [
  {name:'mobile',width:390,height:844},
  {name:'tablet',width:768,height:1024},
  {name:'desktop',width:1280,height:900},
];
const tests=[];
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    for(const loc of ['fr','ar']){
      for(const v of viewports){
        for(const scenario of ['manual','verified','unavailable']){
          if(process.env.D19_DIAGNOSTIC_ONLY==='1' && (loc!=='fr'||v.name!=='mobile'||scenario!=='manual'))continue;
          const context=await browser.newContext({viewport:{width:v.width,height:v.height},locale:loc==='ar'?'ar-MA':'fr-FR',deviceScaleFactor:1,serviceWorkers:'block'});
          const page=await context.newPage();
          const errors=[], outbound=[];
          page.on('pageerror',err=>errors.push(err.message.slice(0,400)));
          page.on('console',msg=>{if(msg.type()==='error'||msg.text().includes('D19_AI_SUMMARY_RENDER_ERROR')) errors.push(msg.text().slice(0,2500));});
          await page.route('**/*',route=>{
            const u=route.request().url();
            if(u.startsWith(origin)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
            outbound.push(u.slice(0,120));return route.abort();
          });
          const url=origin+'/?locale='+loc+'&scenario='+scenario;
          const response=await page.goto(url,{waitUntil:'load',timeout:60000});
          await page.waitForSelector('flt-glass-pane',{state:'attached',timeout:60000});
          await page.waitForTimeout(4500);
          const file=loc+'-'+v.name+'-'+v.width+'x'+v.height+'-'+scenario+'.png';
          const bytes=await page.screenshot({path:path.join(out,file),fullPage:false});
          const hash=crypto.createHash('sha256').update(bytes).digest('hex');
          const dims=await page.evaluate(()=>({w:window.innerWidth,h:window.innerHeight,scrollWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth}));
          tests.push({locale:loc,viewport:v.name,scenario,status:response.status(),filename:file,bytes:bytes.length,sha256:hash,errors,outbound,overflow:dims.scrollWidth>dims.w||dims.bodyWidth>dims.w});
          await context.close();
        }
      }
    }
    const failed=[];
    for(const t of tests){
      if(t.status!==200||t.bytes<15000||t.errors.length||t.outbound.length||t.overflow)failed.push(t);
    }
    if(process.env.D19_DIAGNOSTIC_ONLY!=='1')for(const loc of ['fr','ar'])for(const v of viewports){
      const items=tests.filter(t=>t.locale===loc&&t.viewport===v.name);
      if(new Set(items.map(t=>t.sha256)).size<2)failed.push({locale:loc,viewport:v.name,reason:'no distinct clinical state render'});
    }
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({codeTarget:'actual AISummaryScreen',network:'strict localhost-only',fixtures:['manual CGM unavailable','verified CGM TIR/CV','summary API unavailable'],tests,failed},null,2));
    console.log(JSON.stringify({tested:tests.length,failures:failed.length,details:failed.map(f=>({locale:f.locale,viewport:f.viewport,scenario:f.scenario,reason:f.reason,errors:f.errors}))},null,2));
    if(process.env.D19_AI_WEB_BASELINE!=='1' && failed.length)process.exitCode=1;
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
