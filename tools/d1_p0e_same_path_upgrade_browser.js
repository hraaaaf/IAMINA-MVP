// IAMINA D1 P0-E: browser-only compatibility probe at EXACTLY SAME URL.
// The disposable CI server root switches from a staged 2.31.0 bundle to
// a staged 2.35.4 bundle after the old tab has closed. Nothing is changed in
// the deployed site or in patient data. No hidden migration/rewriting.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {chromium,webkit}=require('playwright');
const engineName=process.env.D1_BROWSER||'chromium';
const type={chromium,webkit}[engineName];
const folder=process.env.D1_UPGRADE_WEB_ROOT;
if(!type || !folder)throw Error('required browser or CI staging folder absent');
const root=path.resolve(folder);
const live=path.join(root,'app');
const origin='http://127.0.0.1:7398/app/';
const result={kind:'D1_P0E_SAME_URL_OLD_TO_NEW',engine:engineName,
 sameUrl:origin,synthetic:true,cases:[],phases:[],result:'NOT_RUN',
 limitations:['Old v5 PWA unavailable','Synthetic v12 fixture only',
 'No validated clinical recovery or encrypted at-rest storage']};
function install(bundle) {
 const source=path.join(root,bundle);
 if (!['old','new'].includes(bundle)||!fs.statSync(source).isDirectory())
  throw Error('invalid CI staging bundle');
 fs.rmSync(live,{recursive:true,force:true});
 fs.cpSync(source,live,{recursive:true,force:true});
 // Both binaries MUST load from the same /app/ path. Flutter's bundled
 // index.html was built with /old/ or /new/ base-href for the separate
 // control arm. Rewrite only this disposable HTML base tag, never patient
 // files or the source bundles. Otherwise the browser would still load
 // scripts and workers from /old/ and /new/, invalidating this experiment.
 const index=path.join(live,'index.html');
 const html=fs.readFileSync(index,'utf8');
 const basePattern=/<base\s+href=["']\/(?:old|new)\/["']\s*\/?>/;
 if(!basePattern.test(html))
   throw Error('Unexpected Flutter HTML base href; same-path evidence INVALID');
 const fixed=html.replace(basePattern,'<base href="/app/">');
 fs.writeFileSync(index,fixed,'utf8');
 if (!fs.existsSync(path.join(live,'drift_worker.js')) ||
     !fs.existsSync(path.join(live,'sqlite3.wasm'))) {
  throw Error('missing SQLite runtime assets at canonical served URL');
 }
}
async function phase(page,phaseName,label) {
 const expected='IAMINA_W02_'+phaseName.toUpperCase()+'_PASS';
 await page.goto(origin+'?phase='+phaseName,
                 {waitUntil:'domcontentloaded',timeout:60000});
 await page.waitForFunction(({expected})=>{
  const lease=document.documentElement.dataset.iaminaTabLease;
  return document.title===expected||
    document.title.startsWith('IAMINA_W02_FAIL:')||
    lease==='occupied'||lease==='unavailable';
 },{expected},{timeout:90000});
 const info=await page.evaluate(async()=>({
  title:document.title,
  basePath:new URL(document.baseURI).pathname,
  lease:document.documentElement.dataset.iaminaTabLease||null,
  backend:document.documentElement.getAttribute('data-d1-drift-storage'),
  // Read-only database-name inventory, never row values.
  idbDatabases:typeof indexedDB.databases==='function'
    ?(await indexedDB.databases()).map(x=>x.name):null,
  crossOriginIsolated:globalThis.crossOriginIsolated===true,
 }));
 const pass=info.title===expected&&info.basePath==='/app/'&&info.lease==='holding'&&
   !!info.backend&&!info.crossOriginIsolated;
 result.phases.push({label,phase:phaseName,info,pass});
 if(!pass)throw Error(label+': '+JSON.stringify(info).slice(0,500));
}
async function trial(browser,label,nextBundle) {
 const outcome={name:label,nextBundle,result:'NOT_RUN'};
 install('old');
 const context=await browser.newContext({locale:'fr-FR',
  serviceWorkers:'block',viewport:{width:390,height:844}});
 try {
  const old=await context.newPage();
  try{await phase(old,'seed_a',label+'-seed-old');}
  finally{await old.close();}
  // Same origin and URL. Only the disposable static file bytes change.
  install(nextBundle);
  const next=await context.newPage();
  try{await phase(next,'verify_a',label+'-verify');outcome.result='PASS';}
  finally{await next.close();}
 }catch(e){outcome.result='FAIL';outcome.error=String(e).slice(0,750);}
 finally{await context.close();}
 result.cases.push(outcome);
}
(async()=>{
 const browser=await type.launch({headless:true,
  ...(engineName==='chromium'?{args:['--no-sandbox']}:{}),
 });
 try{
  await trial(browser,'old_231_to_old_231','old');
  await trial(browser,'old_231_to_new_2354','new');
  result.result=result.cases.every(t=>t.result==='PASS')
    ?'PASS_SAME_PATH_BACKWARD_COMPAT':'FAIL_SAME_PATH_BACKWARD_COMPAT';
  console.log(JSON.stringify({engine:result.engine,result:result.result,
    cases:result.cases},null,2));
  if(result.result!=='PASS_SAME_PATH_BACKWARD_COMPAT')process.exitCode=1;
 }catch(e){
  result.result='FAIL_HARNESS';
  result.error=String(e).slice(0,700);
  console.error(e);
  process.exitCode=1;
 }finally{
  fs.writeFileSync('d1-p0e-'+engineName+'-same-path-upgrade-proof.json',
   JSON.stringify(result,null,2));
  await browser.close();
 }
})();