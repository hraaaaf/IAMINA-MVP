import {createLocalEngine} from './engines.mjs';
import {scoreTranscription} from './metrics.mjs';
const MAX_BYTES=7*1024*1024;
const TYPES=new Set(['image/jpeg','image/png','image/webp']);
async function runBatch({engine,language,cases}) {
  if(!Array.isArray(cases)||cases.length>30) throw Error('Invalid synthetic corpus');
  const start=performance.now();
  let ocr=null;
  try {
    ocr=await createLocalEngine(engine,language);
    const initMs=Math.round(performance.now()-start),results=[];
    for(const info of cases) {
      if(!/^[a-z0-9_]+$/.test(info.id)) throw Error('Unsafe case ID');
      const response=await fetch('/fixtures/'+info.filename,{cache:'no-store'});
      if(!response.ok) throw Error('Synthetic fixture unavailable');
      const blob=await response.blob();
      if(!TYPES.has(blob.type)||blob.size===0||blob.size>MAX_BYTES)throw Error('Unsupported or oversized fixture');
      const t0=performance.now();
      const extracted=await ocr.recognize(blob);
      results.push({...scoreTranscription(info,extracted),elapsedMs:Math.round(performance.now()-t0)});
    }
    return {engine,language,initMs,results};
  } finally {if(ocr)await ocr.close();}
}
window.__runIaminaOcrBatch=runBatch;
window.__iaminaOcrProbeLoaded=true;
