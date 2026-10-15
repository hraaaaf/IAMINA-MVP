import {createWorker} from 'tesseract.js';
import {PaddleOCR} from '@paddleocr/paddleocr-js';
const LANGS={fr:['fra','eng'],ar:['ara','eng'],mixed:['fra','ara','eng']};

export async function createLocalEngine(engine,language) {
  if(engine==='tesseract') {
    if(!LANGS[language]) throw Error('Unqualified language profile');
    const worker=await createWorker(LANGS[language],1,{
      workerPath:'/assets/worker.min.js', corePath:'/assets/core',
      langPath:'/assets/tessdata',gzip:true,workerBlobURL:false,cacheMethod:'none'
    });
    await worker.setParameters({tessedit_pageseg_mode:'3'});
    return {
      async recognize(blob){const {data}=await worker.recognize(blob);return data.text||'';},
      async close(){await worker.terminate();}
    };
  }
  if(engine==='paddle') {
    if(language!=='fr') throw Error('PaddleOCR.js Arabic NOT qualified');
    const ocr=await PaddleOCR.create({
      lang:'fr',ocrVersion:'PP-OCRv6',
      textDetectionModelName:'PP-OCRv6_small_det',
      textRecognitionModelName:'PP-OCRv6_small_rec',
      textDetectionModelAsset:{url:'/assets/paddle/PP-OCRv6_small_det_onnx_infer.tar'},
      textRecognitionModelAsset:{url:'/assets/paddle/PP-OCRv6_small_rec_onnx_infer.tar'},
      worker:false,
      ortOptions:{backend:'wasm',wasmPaths:'/assets/ort/',numThreads:1,simd:true}
    });
    return {
      async recognize(blob){const [result]=await ocr.predict(blob);return (result?.items||[]).map(x=>x.text).join('\n');},
      async close(){await ocr.dispose();}
    };
  }
  throw Error('Unsupported OCR engine');
}
