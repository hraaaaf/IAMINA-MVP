// D18 CI-ONLY: active XSS-canary control proving the candidate policy blocks
// inline JavaScript and eval() IN THE PAGE REALM, while the identical page
// without CSP permits both. DevTools page.evaluate() is not a valid eval probe.
'use strict';
const {chromium,webkit}=require('playwright');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const name=process.env.D18_TEST_BROWSER||'chromium';
if(!['chromium','webkit'].includes(name))throw Error('D18_UNSUPPORTED_ENGINE');
const engine=name==='webkit'?webkit:chromium;
const baseDir=fs.mkdtempSync(path.join(os.tmpdir(),'d18-csp-attack-canary-'));
const evidence=[];
async function probe(ctx,origin,shouldBlock,label){
 const page=await ctx.newPage();
 try {
  const response=await page.goto(origin+'/d18_csp_canary.html',{
    waitUntil:'domcontentloaded',timeout:45000});
  if(!response||!response.ok())throw Error('D18_CSP_PROBE_NO_DOCUMENT');
  const policy=response.headers()['content-security-policy']||'';
  if(shouldBlock && !policy.includes("script-src 'self' 'wasm-unsafe-eval'"))
    throw Error('D18_CSP_POLICY_NOT_ACTIVE');
  if(!shouldBlock && policy)
    throw Error('D18_CSP_BASELINE_NOT_UNPROTECTED');
  // Load the external canary through a real static HTML script tag. Neither
  // page.evaluate() nor page.addScriptTag() may inject attack code, as
  // automation/debugger script injection can bypass or misreport CSP.
  const observed=await page.evaluate(()=>
    window.__d18ExternalCanaryResult||null);
  if(!observed || observed.externalScriptLoaded!==true)
    throw Error('D18_CSP_EXTERNAL_CANARY_NOT_EXECUTED');
  const pass=shouldBlock
    ? !observed.inlineExecuted && !observed.evalExecuted &&
        observed.evalThrows
    : observed.inlineExecuted && observed.evalExecuted &&
        !observed.evalThrows;
  evidence.push({phase:label,pass,engine:name,
    inlineExecuted:observed.inlineExecuted,
    inlineInsertionThrows:observed.inlineInsertionThrows,
    evalExecuted:observed.evalExecuted,
    evalThrows:observed.evalThrows,
    evalErrorName:observed.evalErrorName});
  if(!pass)throw Error('D18_CSP_XSS_CANARY_UNEXPECTED_EXECUTION');
 }finally{
  await page.close();
 }
}
(async()=>{
 let ctx;
 try {
  ctx=await engine.launchPersistentContext(path.join(baseDir,'browser'),{
    headless:true,viewport:{width:390,height:844},
    ...(name==='chromium'?{
      args:['--no-sandbox','--disable-dev-shm-usage']
    }:{})
  });
  await probe(ctx,'http://127.0.0.1:7399',false,'without_csp_positive_control');
  await probe(ctx,'http://127.0.0.1:7398',true,'with_csp_must_block_xss');
 }catch(e){
  evidence.push({phase:'harness',pass:false,
    errorCode:String(e.message||e.name).replace(/[^A-Za-z0-9_]/g,'_').slice(0,140)});
 }finally {
  if(ctx)await ctx.close().catch(()=>{});
  fs.rmSync(baseDir,{recursive:true,force:true});
 }
 fs.mkdirSync('d18-csp-negative-proof',{recursive:true});
 fs.writeFileSync('d18-csp-negative-proof/report.json',
   JSON.stringify({sha:process.env.GITHUB_SHA||null,
     engine:name,phases:evidence},null,2));
 console.log(JSON.stringify(evidence));
 const expected=['without_csp_positive_control','with_csp_must_block_xss'];
 if(evidence.length!==2||evidence.some((r,i)=>r.phase!==expected[i]||!r.pass))
   process.exitCode=1;
})().catch(e=>{
 console.error('D18_CSP_ATTACK_HARNESS_FATAL',e.name);
 process.exitCode=1;
});
