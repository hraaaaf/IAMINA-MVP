/** Real browser execution: any cross-origin HTTP request is aborted. */
import {readFile,mkdir,writeFile,stat} from 'node:fs/promises';
import {createServer} from 'vite';
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

const server=await createServer({server:{host:'127.0.0.1',port:0},clearScreen:false});
let browser;
const report={benchmark:'iamina-pulper-photo-ocr-browser-poc-v1',
  syntheticOnly:true,patientData:false,backendCalls:false,modelAssetsSameOrigin:true,
  browser:'chromium',iPhoneSafariQualified:false,clinicalQualified:false,
  results:[],blockedRequests:0,errors:[]};
try{
  await server.listen();
  const port=server.httpServer.address().port;
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&url.port===String(port))return route.continue();
    report.blockedRequests++;
    return route.abort();
  });
  const page=await context.newPage();
  page.on('pageerror',error=>report.errors.push({stage:'pageerror',errorClass:error.name}));
  await page.goto('http://127.0.0.1:'+port+'/',{waitUntil:'load'});
  await page.waitForFunction(()=>window.__iaminaOcrProbeLoaded===true,null,{timeout:60000});
  for(const profile of profiles){
    try{
      const items=cases.filter(x=>x.language===profile.language);
      const result=await page.evaluate(args=>window.__runIaminaOcrBatch(args),{...profile,cases:items});
      report.results.push(result);
      console.log(JSON.stringify({engine:profile.engine,language:profile.language,
        passed:result.results.filter(x=>x.safeForReview).length,total:result.results.length,initMs:result.initMs}));
    }catch(error){
      report.errors.push({...profile,stage:'engine',errorClass:error.name||'Error'});
      console.error(profile.engine+'/'+profile.language+': '+(error.name||'Error')+' '+error.message.slice(0,120));
    }
  }
  await context.close();
}finally{
  if(browser)await browser.close();
  await server.close();
  await mkdir('out',{recursive:true});
  report.measuredCases=report.results.reduce((n,x)=>n+x.results.length,0);
  report.passedCases=report.results.reduce((n,x)=>n+x.results.filter(y=>y.safeForReview).length,0);
  report.allCriticalExact=report.measuredCases>0 && report.measuredCases===report.passedCases;
  report.technicalCompleted=report.results.length===profiles.length && report.errors.length===0 && report.blockedRequests===0;
  await writeFile('out/report.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({completed:report.technicalCompleted,passed:report.passedCases,total:report.measuredCases,externalRequestsBlocked:report.blockedRequests,errors:report.errors.length}));
}
process.exitCode=report.technicalCompleted?0:1;
