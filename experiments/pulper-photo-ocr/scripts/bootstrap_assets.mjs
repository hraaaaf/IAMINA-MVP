/** Official assets fetched only at setup, then served from local origin. */
import {createHash} from 'node:crypto';
import {createReadStream,createWriteStream} from 'node:fs';
import {copyFile,mkdir,readdir,rename,rm,stat,writeFile} from 'node:fs/promises';
import {pipeline} from 'node:stream/promises';
import {Readable,Transform} from 'node:stream';
import {createGzip} from 'node:zlib';
import path from 'node:path';

const root=path.resolve('public/assets'), hashes={};
async function sha(file){
  const h=createHash('sha256');
  for await(const bytes of createReadStream(file))h.update(bytes);
  return h.digest('hex');
}
async function copyAssets(source,dest,filter){
  await mkdir(dest,{recursive:true});
  const files=(await readdir(source)).filter(filter);
  if(!files.length)throw Error('Missing local runtime assets');
  for(const name of files){
    const target=path.join(dest,name);
    await copyFile(path.join(source,name),target);
    hashes[path.relative(root,target)]=await sha(target);
  }
}
async function fetchOfficial(url,dest,max){
  const parsed=new URL(url);
  if(parsed.protocol!=='https:'||!['raw.githubusercontent.com','paddle-model-ecology.bj.bcebos.com'].includes(parsed.hostname))throw Error('Unapproved asset host');
  const res=await fetch(url,{redirect:'error'});
  if(!res.ok||!res.body)throw Error('Asset fetch failed HTTP '+res.status);
  if(Number(res.headers.get('content-length')||0)>max)throw Error('Model exceeds configured maximum');
  await mkdir(path.dirname(dest),{recursive:true});
  const tmp=dest+'.incomplete';
  let count=0;
  const guard=new Transform({transform(chunk,_,cb){count+=chunk.length;cb(count>max?Error('Asset too large'):null,chunk);}});
  try{
    await pipeline(Readable.fromWeb(res.body),guard,createWriteStream(tmp,{flags:'wx'}));
    await rename(tmp,dest);
  }catch(e){await rm(tmp,{force:true});throw e;}
  hashes[path.relative(root,dest)]=await sha(dest);
}
await mkdir(root,{recursive:true});
const worker=path.join(root,'worker.min.js');
await copyFile('node_modules/tesseract.js/dist/worker.min.js',worker);
hashes['worker.min.js']=await sha(worker);
await copyAssets('node_modules/tesseract.js-core',path.join(root,'core'),x=>x.startsWith('tesseract-core') && /\.(wasm|wasm\.js|js)$/.test(x));
await copyAssets('node_modules/onnxruntime-web/dist',path.join(root,'ort'),x=>x.startsWith('ort-wasm') && /\.(wasm|mjs|js)$/.test(x));
for(const lang of ['eng','fra','ara']){
  const target=path.join(root,'tessdata',lang+'.traineddata');
  await fetchOfficial('https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/'+lang+'.traineddata',target,30*1024*1024);
  await pipeline(createReadStream(target),createGzip({level:9}),createWriteStream(target+'.gz'));
  hashes[path.relative(root,target+'.gz')]=await sha(target+'.gz');
  await rm(target);
  delete hashes[path.relative(root,target)];
}
for(const stem of ['PP-OCRv6_small_det','PP-OCRv6_small_rec']){
  const file=stem+'_onnx_infer.tar';
  await fetchOfficial('https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/'+file,path.join(root,'paddle',file),220*1024*1024);
}
await writeFile('.assets-manifest.json',JSON.stringify({syntheticOnly:true,hostedLocally:true,hashes},null,2)+'\n');
console.log(JSON.stringify({assetCount:Object.keys(hashes).length,allSameOrigin:true,bytes:(await Promise.all(Object.keys(hashes).map(async x=>(await stat(path.join(root,x))).size))).reduce((a,b)=>a+b,0)}));
