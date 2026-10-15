/** Real browser execution: any cross-origin HTTP request is aborted. */
import {readFile,mkdir,writeFile,stat} from 'node:fs/promises';
import {preview} from 'vite';
import {chromium} from 'playwright';

const cases=JSON.parse(await readFile('public/fixtures/cases.json','utf8'));
const profiles=[
  {engine:'tesseract',language:'fr'},
  {engine:'tesseract',language:'ar'},
  {engine:'tesseract',language:'mixed'},
  {engine:'paddle',language:'fr'}
];
for(const path of ['public/assets/worker.min.js','public/assets/tessdata/fra.traineddata.gz','public/assets/tessdata/eng.traineddata.gz','public/assets/tessdata/ara.traineddata.gz',
'public/assets/paddle/PP-OCRv6_small_det_onnx_infer.tar','public/assets/paddle/PP-OCRv6_small_rec_onnx_infer.tar'])await stat(path);

// Serve compiled static assets: Vite dev middleware rejects dynamic ONNX .mjs
// imports from public/ when the WebAssembly loader appends ?import.
const server=await preview({preview:{host:'127.0.0.1',port:0,strictPort:false},clearScreen:false});
let browser;
const report={benchmark:'iamina-pulper-photo-ocr-browser-poc-v1',
  syntheticOnly:true,patientData:false,backendCalls:false,modelAssetsSameOrigin:true,
  browser:'chromium',iPhoneSafariQualified:false,clinicalQualified:false,
  paddleExperimentalUnsafeEval:true,paddleProductionCspCompatible:false,
  results:[],blockedRequests:0,errors:[]};
try{
  const port=server.httpServer.address().port;
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&url.port===String(port))return route.continue();
    report.blockedRequests++;
    return route.abort();
  });
  for(const profile of profiles){
    const page=await context.newPage();
    let stage='bootstrap';
    page.on('pageerror',error=>report.errors.push({
      ...profile,stage:'pageerror',errorClass:error.name||'Error',
      message:String(error.message||'').slice(0,350)
    }));
    page.on('console',message=>{
      if(message.type()==='error' && !/^Estimating resolution as \d+$/.test(message.text()))report.errors.push({
        ...profile,stage:'browser_console',errorClass:'ConsoleError',
        message:String(message.text()).slice(0,350)
      });
    });
    try {
      await page.goto('http://127.0.0.1:'+port+(profile.engine==='paddle'?'/paddle.html':'/'),{waitUntil:'load',timeout:45000});
      await page.waitForFunction(()=>window.__iaminaOcrProbeLoaded===true,null,{timeout:45000});
      stage='engine';
      const items=cases.filter(x=>x.language===profile.language);
      // Bound one engine to make its failures observable, not an indefinite CI hang.
      const result=await page.evaluate(args=>Promise.race([
        window.__runIaminaOcrBatch(args),
        new Promise((_,reject)=>setTimeout(()=>reject(Error('engine_timeout_180s')),180000))
      ]),{...profile,cases:items});
      report.results.push(result);
      console.log(JSON.stringify({engine:profile.engine,language:profile.language,
        passed:result.results.filter(x=>x.safeForReview).length,total:result.results.length,initMs:result.initMs}));
    }catch(error){
      report.errors.push({...profile,stage,errorClass:error.name||'Error',
        message:String(error.message||'').slice(0,350)});
      console.error(profile.engine+'/'+profile.language+': '+(error.name||'Error')+' '+String(error.message||'').slice(0,200));
    }finally{
      await page.close();
    }
  }
  await context.close();
}finally{
  if(browser)await browser.close();
  await new Promise((resolve,reject)=>server.httpServer.close(error=>error?reject(error):resolve()));
  await mkdir('out',{recursive:true});
  report.measuredCases=report.results.reduce((n,x)=>n+x.results.length,0);
  report.passedCases=report.results.reduce((n,x)=>n+x.results.filter(y=>y.safeForReview).length,0);
  report.allCriticalExact=report.measuredCases>0 && report.measuredCases===report.passedCases;
  report.technicalCompleted=report.results.length===profiles.length && report.errors.length===0 && report.blockedRequests===0;
  await writeFile('out/report.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({completed:report.technicalCompleted,passed:report.passedCases,total:report.measuredCases,externalRequestsBlocked:report.blockedRequests,errors:report.errors.length}));
}
process.exitCode=report.technicalCompleted?0:1;
