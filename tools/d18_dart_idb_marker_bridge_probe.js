// Browser invokes the actual Flutter Dart D18CutoverMarkerStore contract.
// JS fixture ONLY implements low-level IDB; no JS direct marker operations.
'use strict';
const {chromium,webkit}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const engineName=process.env.D18_DART_IDB_BROWSER||'chromium';
if(!['chromium','webkit'].includes(engineName))throw Error('BAD_ENGINE');
const engine=engineName==='chromium'?chromium:webkit;
const root=fs.mkdtempSync(path.join(os.tmpdir(),'d18-dart-idb-marker-'));
const profile=path.join(root,'profile');
const origin='http://127.0.0.1:7397/';
const fixture=path.resolve(__dirname,'fixtures/d18_marker_idb_bridge.js');
const reports=[];
function check(ok,code){if(!ok)throw Error(code);}
async function openContext(){
  return engine.launchPersistentContext(profile,{
    headless:true,locale:'fr-FR',viewport:{width:390,height:844},
    deviceScaleFactor:2,
    ...(engineName==='chromium'?{args:['--no-sandbox','--disable-dev-shm-usage']}:{}),
  });
}
async function phase(ctx,name){
  const page=await ctx.newPage();
  try{
    await page.addInitScript({path:fixture});
    await page.goto(origin+'?phase='+name,{
      waitUntil:'domcontentloaded',timeout:45000});
    await page.waitForFunction(()=>
      document.title.startsWith('D18_DART_MARKER_PASS:')||
      document.title.startsWith('D18_DART_MARKER_FAIL:'),
      null,{timeout:60000});
    return page.evaluate(()=>({title:document.title,
      error:document.documentElement.dataset.d18DartMarkerError||null}));
  }finally{await page.close();}
}
async function requirePass(ctx,step,label=step){
  const x=await phase(ctx,step);
  check(x.title==='D18_DART_MARKER_PASS:'+step,
    'D18_DART_PHASE_FAIL_'+label+'_'+(x.error||'UNKNOWN'));
  reports.push({phase:label,pass:true});
}
async function run(){
  let ctx;
  try {
    ctx=await openContext();
    const [a,b]=await Promise.all([phase(ctx,'prepare'),phase(ctx,'prepare')]);
    check([a,b].filter(x=>x.title==='D18_DART_MARKER_PASS:prepare').length===1&&
      [a,b].filter(x=>x.title==='D18_DART_MARKER_FAIL:prepare').length===1,
      'D18_DART_CAS_DOUBLE_PREPARE');
    reports.push({phase:'one_prepared_winner_two_dart_tabs',pass:true});
    await requirePass(ctx,'read_prepared');
    await requirePass(ctx,'stale_prepare');
    await ctx.close();ctx=null;
    ctx=await openContext();
    await requirePass(ctx,'read_prepared','prepared_survives_browser_restart');
    const [c,d]=await Promise.all([phase(ctx,'activate'),phase(ctx,'activate')]);
    check([c,d].filter(x=>x.title==='D18_DART_MARKER_PASS:activate').length===1&&
      [c,d].filter(x=>x.title==='D18_DART_MARKER_FAIL:activate').length===1,
      'D18_DART_CAS_DOUBLE_ACTIVATE');
    reports.push({phase:'one_active_winner_two_dart_tabs',pass:true});
    await requirePass(ctx,'read_active');
    await requirePass(ctx,'replay_denied');
    await requirePass(ctx,'other_scope_empty');
    await requirePass(ctx,'audit_scope_denied');
    await requirePass(ctx,'reverse_transition_denied');
    await ctx.close();ctx=null;
    ctx=await openContext();
    await requirePass(ctx,'read_active','active_survives_browser_restart');
  }finally{
    await ctx?.close().catch(()=>{});
    fs.rmSync(root,{recursive:true,force:true});
  }
}
(async()=>{
  try{await run();}
  catch(e){
    reports.push({phase:'harness',pass:false,
      code:String(e.message||'UNKNOWN').replace(/[^A-Za-z0-9_]/g,'_').slice(0,130)});
    process.exitCode=1;
  }
  fs.mkdirSync('d18-dart-idb-marker-proof',{recursive:true});
  fs.writeFileSync('d18-dart-idb-marker-proof/report-'+engineName+'.json',
    JSON.stringify({sha:process.env.GITHUB_SHA||null,
      kind:'CI_ONLY_REAL_FLUTTER_DART_INDEXEDDB_CAS',
      engine:engineName,reports},null,2));
  console.log(JSON.stringify(reports));
  if(reports.length!==11||reports.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error('D18_DART_MARKER_FATAL',e.name);process.exitCode=1;});
