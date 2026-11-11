// D1.6 independent platform diagnostic: compile official SQLite3 and
// SQLite3MultipleCiphers WebAssembly binaries with no Flutter / Drift.
// No database, patient, secrets or keys touched.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const engineName=process.env.D1_BROWSER||'chromium';
const engine={chromium,webkit}[engineName];
if(!engine)throw Error('unsupported engine');
const outcome={kind:'D1_P0C_INDEPENDENT_WASM_COMPAT',engine:engineName,
 synthetic:true,wasmModules:[],verdict:'NOT_RUN'};
(async()=>{
 const browser=await engine.launch({headless:true,
  ...(engineName==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const context=await browser.newContext({serviceWorkers:'block'});
  try{
   const page=await context.newPage();
   await page.goto('http://127.0.0.1:7398/index.html',
      {waitUntil:'domcontentloaded'});
   for(const path of ['sqlite3.wasm','sqlite3mc.wasm']){
    const obj=await page.evaluate(async name=>{
     const res=await fetch('/'+name,{cache:'no-store'});
     if(!res.ok)throw Error('WASM HTTP '+res.status);
     const bytes=await res.arrayBuffer();
     const module=await WebAssembly.compile(bytes);
     const imports=WebAssembly.Module.imports(module);
     const exports=WebAssembly.Module.exports(module);
     return {asset:name,httpStatus:res.status,
      bytes:bytes.byteLength,
      compileOk:true,
      imports:imports.slice(0,30).map(x=>({module:x.module,name:x.name,kind:x.kind})),
      exportCount:exports.length,
      sqlite3_open_v2_exported:exports.some(x=>x.name==='sqlite3_open_v2'),
     };
    },path);
    outcome.wasmModules.push(obj);
   }
   outcome.verdict='PASS_BOTH_MODULES_COMPILE_ONLY';
   console.log(JSON.stringify(outcome,null,2));
   await page.close();
  }finally{await context.close();}
 }catch(error){
  outcome.verdict='FAIL';
  outcome.error=String(error).slice(0,700);
  console.error(error);
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0c-wasm-compat-'+engineName+'.json',
    JSON.stringify(outcome,null,2));
  await browser.close();
 }
})();
