/** Native Tesseract proxy only; NOT Tesseract.js browser evidence. */
import {execFileSync} from 'node:child_process';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';
import {scoreTranscription} from '../src/metrics.mjs';

const cases=JSON.parse(await readFile('public/fixtures/cases.json','utf8'));
const language={fr:'fra+eng',ar:'ara+eng',mixed:'fra+ara+eng'};
const results=[];
for(const info of cases){
  const start=performance.now();
  const text=execFileSync('tesseract',['public/fixtures/'+info.filename,'stdout','-l',language[info.language],'--psm','3'],{encoding:'utf8',timeout:30000,stdio:['ignore','pipe','pipe']});
  results.push({...scoreTranscription(info,text),elapsedMs:Math.round(performance.now()-start)});
}
const report={benchmark:'iamina-pulper-photo-ocr-native-tesseract-reference',browser:false,isTesseractJs:false,
  clinicallyQualified:false,syntheticOnly:true,noNetworkCalls:true,results,
  passed:results.filter(x=>x.safeForReview).length,total:results.length};
await mkdir('out',{recursive:true});
await writeFile('out/native-reference.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,total:report.total,failed:results.filter(x=>!x.safeForReview).map(x=>x.caseId)}));
