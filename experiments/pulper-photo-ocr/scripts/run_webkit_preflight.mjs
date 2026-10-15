/**
 * Synthetic WebKit / iPhone-like viewport compatibility preflight.
 * This runs on Playwright's Linux WebKit, NOT on an actual iOS Safari device.
 * An engine failure is a measured incompatibility, never silently a pass.
 */
import {mkdir,readFile,stat,writeFile} from 'node:fs/promises';
import {preview} from 'vite';
import {webkit} from 'playwright';

const cases=JSON.parse(await readFile('public/fixtures/cases.json','utf8'));
await stat('public/fixtures/fr_clean.heic');
const profiles=[
  {engine:'tesseract',language:'fr'},
  {engine:'tesseract',language:'ar'},
  {engine:'tesseract',language:'mixed'},
  {engine:'paddle',language:'fr'}
];
const report={
  benchmark:'iamina-pulper-ocr-webkit-linux-preflight-v1',
  syntheticOnly:true,patientData:false,backendCalls:false,
  browser:'playwright-webkit-linux',viewport:{width:390,height:844},
  actualIosSafari:false,heicIphoneQualified:false,
  clinicalQualified:false,paddleProductionCspCompatible:false,
  paddleExperimentalUnsafeEval:true,externalRequestsBlocked:0,
  engines:[],heicCodec:null,infrastructureError:null
};
let server=null,browser=null,context=null;
try {
  server=await preview({preview:{host:'127.0.0.1',port:0,strictPort:false},clearScreen:false});
  const port=server.httpServer.address().port;
  browser=await webkit.launch({headless:true});
  context=await browser.newContext({
    viewport:{width:390,height:844},hasTouch:true,serviceWorkers:'block'
  });
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&url.port===String(port))
      return route.continue();
    if(url.protocol==='blob:'||url.protocol==='data:')return route.continue();
    report.externalRequestsBlocked++;
    return route.abort();
  });
  for(const profile of profiles){
    const outcome={...profile,status:'not_run',errors:[]};
    let page=null;
    try {
      page=await context.newPage();
      page.on('pageerror',error=>outcome.errors.push({
        stage:'pageerror',errorClass:error.name||'Error',
        message:String(error.message||'').slice(0,300)
      }));
      page.on('console',message=>{
        if(message.type()==='error'&&!/^Estimating resolution as \d+$/.test(message.text()))
          outcome.errors.push({stage:'console',errorClass:'ConsoleError',
            message:String(message.text()).slice(0,300)});
      });
      await page.goto('http://127.0.0.1:'+port+
        (profile.engine==='paddle'?'/paddle.html':'/'),
        {waitUntil:'load',timeout:45000});
      await page.waitForFunction(()=>window.__iaminaOcrProbeLoaded===true,null,{timeout:45000});
      const items=cases.filter(x=>x.language===profile.language);
      const measured=await page.evaluate(args=>Promise.race([
        window.__runIaminaOcrBatch(args),
        new Promise((_,reject)=>setTimeout(()=>reject(Error('engine_timeout_180s')),180000))
      ]),{...profile,cases:items});
      outcome.status='measured';
      outcome.initMs=measured.initMs;
      outcome.total=measured.results.length;
      outcome.passed=measured.results.filter(x=>x.safeForReview).length;
      outcome.cases=measured.results;
    } catch(error){
      outcome.status='incompatible_or_failed';
      outcome.errorClass=error.name||'Error';
      outcome.reason=String(error.message||'').slice(0,300);
    } finally {
      if(page)await page.close();
      report.engines.push(outcome);
      console.log(JSON.stringify({
        engine:profile.engine,language:profile.language,status:outcome.status,
        passed:outcome.passed??0,total:outcome.total??0,errors:outcome.errors.length
      }));
    }
  }
  const heicPage=await context.newPage();
  try {
    await heicPage.goto('http://127.0.0.1:'+port+'/',{waitUntil:'load',timeout:45000});
    report.heicCodec=await heicPage.evaluate(async()=>{
      const response=await fetch('/fixtures/fr_clean.heic',{cache:'no-store'});
      if(!response.ok)return {checked:true,localDecode:false,localPngTranscode:false,
        reason:'http_'+String(response.status)};
      const heic=await response.blob();
      try{
        const bitmap=await createImageBitmap(heic);
        const canvas=document.createElement('canvas');
        canvas.width=bitmap.width;
        canvas.height=bitmap.height;
        const ctx=canvas.getContext('2d');
        if(!ctx)throw new Error('Canvas2DUnavailable');
        ctx.drawImage(bitmap,0,0);
        bitmap.close();
        const png=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
        if(!png||png.type!=='image/png')throw new Error('PNGTranscodeUnavailable');
        return {checked:true,localDecode:true,localPngTranscode:true,
          width:canvas.width,height:canvas.height,heicBytes:heic.size,pngBytes:png.size};
      }catch(error){
        return {checked:true,localDecode:false,localPngTranscode:false,
          errorClass:error?.name||'Error'};
      }
    });
  }catch(error){
    report.heicCodec={checked:false,errorClass:error.name||'Error'};
  }finally{
    await heicPage.close();
  }
}catch(error){
  report.infrastructureError={errorClass:error.name||'Error',
    message:String(error.message||'').slice(0,300)};
}finally{
  if(context)await context.close();
  if(browser)await browser.close();
  if(server)await new Promise((resolve,reject)=>
    server.httpServer.close(error=>error?reject(error):resolve()));
  await mkdir('out',{recursive:true});
  report.measuredCases=report.engines.reduce((n,x)=>n+(x.total||0),0);
  report.passedCases=report.engines.reduce((n,x)=>n+(x.passed||0),0);
  report.probeCompleted=report.engines.length===profiles.length &&
    report.heicCodec?.checked===true && report.externalRequestsBlocked===0 &&
    report.infrastructureError===null;
  // A successful preflight only means the compatibility probes ran, even if
  // the recorded HEIC codec or OCR engine is unsupported. Never imply clinical pass.
  report.qualificationPassed=false;
  await writeFile('out/report-webkit.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({probeCompleted:report.probeCompleted,
    measured:report.measuredCases,passed:report.passedCases,
    heicLocalDecode:report.heicCodec?.localDecode??false,
    externalRequestsBlocked:report.externalRequestsBlocked,
    compatibilityFailures:report.engines.filter(x=>x.status!=='measured').length,
    infrastructureFailure:report.infrastructureError?.errorClass||null}));
}
process.exitCode=report.probeCompleted?0:1;
