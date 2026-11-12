// D1 PRF prototype: Chromium CDP virtual PRF; WebKit negative mock only.
// Neither mode tests a physical iPhone, real account or clinical patient.
'use strict';
const fs=require('node:fs');
const {chromium,webkit}=require('playwright');
const name=process.env.D1_BROWSER||'chromium';
const base='http://localhost:7419/d1_webauthn_prf_harness.html';
const ownerA='amina_vault_v1_native_731',ownerB='amina_vault_v1_native_812';
const report={lot:'D1_WEBAUTHN_PRF_GATED_KEY',browser:name,
 synthetic:true,physicalSafariIphone:false,hardwareKeyTest:false,
 realAccountAuthentication:false,noAutomaticFallback:true,
 patientRelease:'NO_GO',result:'NOT_RUN',checks:[]};
async function settled(page,label){
 await page.waitForFunction(()=>window.d1Research?.settled===true,null,{timeout:60000});
 const last=await page.evaluate(()=>window.d1Research.last);
 report.checks.push({label,outcome:last});
 return last;
}
(async()=>{
 const engine={chromium,webkit}[name];if(!engine)throw Error('INVALID_BROWSER');
 const browser=await engine.launch({headless:true,...(name==='chromium'?{args:['--no-sandbox']}:{})});
 try{
  const context=await browser.newContext({locale:'fr-FR',serviceWorkers:'block'});
  if(name==='webkit'){
   await context.addInitScript(()=>{
    // Fake PRF-unsupported credential; never counted as Safari Face ID support.
    window.PublicKeyCredential=class {};
    const fake={
     create:async()=>({
      type:'public-key',rawId:new Uint8Array(32).buffer,
      authenticatorAttachment:'platform',
      getClientExtensionResults(){return {prf:{enabled:false}}}
     }),
     get:async()=>{throw Error('NO_PRF_AUTHENTICATOR')}
    };
    Object.defineProperty(navigator,'credentials',{configurable:true,get:()=>fake});
   });
  }
  const page=await context.newPage();
  let cdp=null,authenticatorId=null;
  if(name==='chromium'){
   cdp=await context.newCDPSession(page);
   await cdp.send('WebAuthn.enable',{enableUI:false});
   const a=await cdp.send('WebAuthn.addVirtualAuthenticator',{
    options:{protocol:'ctap2',ctap2Version:'ctap2_1',transport:'internal',
      hasResidentKey:true,hasUserVerification:true,isUserVerified:true,
      hasPrf:true,hasHmacSecret:true,automaticPresenceSimulation:true}
   });
   authenticatorId=a.authenticatorId;
   report.authenticator='CHROMIUM_VIRTUAL_PRF_ONLY';
  }else report.authenticator='WEBKIT_UNSUPPORTED_PRF_STUB_ONLY';
  await page.goto(base,{waitUntil:'domcontentloaded'});
  const cap=await page.evaluate(()=>window.iaminaD1PrfGate.capability());
  if(cap.patientReady!==false||cap.provenPrfCredential!==false)
   throw Error('CAPABILITY_HINT_MISTAKEN_FOR_VALIDATED_PASSKEY');
  report.checks.push({label:'capability hints not permission to open',outcome:'PASS_NO_GO'});
  // Before registration, no caller can obtain DEK. Automation may mark a
  // script evaluation as user-activated, so never assert a specific UX error.
  const preEnrollment=await page.evaluate(async owner=>{
   try{
    const key=await window.iaminaD1PrfGate.unlock(owner);
    key?.fill(0);return 'UNEXPECTED_DEK';
   }catch(e){return String(e)}
  },ownerA);
  if(preEnrollment==='UNEXPECTED_DEK')throw Error('UNENROLLED_KEY_LEAK');
  report.checks.push({label:'no credential or wrapped DEK means fail-closed',
    outcome:'PASS_REFUSED'});
  await page.click('#enroll');
  const reg=await settled(page,'register platform PRF');
  if(name==='webkit'){
   if(!reg.startsWith('FAIL_ENROLL_'))throw Error('UNSUPPORTED_PRF_ADMITTED');
   const inspect=await page.evaluate(owner=>
    window.iaminaD1PrfGate.inspect(owner),ownerA);
   if(inspect.enrolled)throw Error('UNSUPPORTED_PRF_WRAPPED_DEK');
   report.checks.push({label:'no PRF => no encrypted envelope',
    outcome:'PASS_FAIL_CLOSED_SIMULATED'});
   report.result='PASS_FAIL_CLOSED_UNSUPPORTED_PRF_SIMULATION';
  }else{
   if(reg!=='PASS_ENROLL')throw Error('PRF_REGISTRATION_NOT_PROVEN:'+reg);
   const inspect=await page.evaluate(owner=>
    window.iaminaD1PrfGate.inspect(owner),ownerA);
   if(!inspect.enrolled||!inspect.hasPrfWrap)
    throw Error('PRF_ENVELOPE_NOT_PERSISTED');
   report.checks.push({label:'real PRF credential creates wrapped DEK',outcome:'PASS'});
   if((await page.evaluate(owner=>
       window.iaminaD1PrfGate.inspect(owner),ownerB)).enrolled)
    throw Error('FOREIGN_OWNER_ENROLLED');
   await page.click('#unlock');
   const unlock=await settled(page,'assertion UV and PRF unwrap');
   if(unlock!=='PASS_UNLOCK')throw Error('PRF_UNLOCK_FAILED:'+unlock);
   const correct=await page.evaluate(()=>{
    const k=window.d1Research.key;
    const ok=k?.length===32&&k.every((v,i)=>v===i+1);
    k?.fill(0);window.d1Research.key=null;return ok;
   });
   if(!correct)throw Error('PRF_UNWRAP_WRONG_FIXTURE_DEK');
   report.checks.push({label:'assertion PRF unwraps exact 256-bit synthetic DEK',outcome:'PASS'});
   await page.evaluate(owner=>{
    const button=document.createElement('button');button.id='foreign';
    button.textContent='Foreign owner';
    button.onclick=async()=>{
     try{await window.iaminaD1PrfGate.unlock(owner);window.__foreign='PASS_WRONG'}
     catch(e){window.__foreign=String(e)}
    };document.body.appendChild(button);
   },ownerB);
   await page.click('#foreign');
   await page.waitForFunction(()=>typeof window.__foreign==='string');
   const foreign=await page.evaluate(()=>window.__foreign);
   if(!foreign.includes('D1_PRF_MISSING_OR_FOREIGN'))
    throw Error('FOREIGN_OWNER_NOT_REFUSED:'+foreign);
   report.checks.push({label:'wrong owner denied before PRF assertion',outcome:'PASS'});
   await cdp.send('WebAuthn.setUserVerified',{authenticatorId,isUserVerified:false});
   await page.click('#unlock');
   const badUV=await settled(page,'unverified user refused');
   if(!badUV.startsWith('FAIL_UNLOCK_'))throw Error('UV_BYPASS_ALLOWED:'+badUV);
   report.checks.push({label:'unverified authenticator cannot expose DEK',outcome:'PASS'});
   await cdp.send('WebAuthn.setUserVerified',{authenticatorId,isUserVerified:true});
   await page.evaluate(async owner=>{
    const db=await new Promise((resolve,reject)=>{
     const q=indexedDB.open('iamina_d1_prf_research_v1');
     q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error)
    });
    const r=await new Promise((resolve,reject)=>{
     const q=db.transaction('vaultPrf','readonly').objectStore('vaultPrf').get(owner);
     q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error)
    });
    window.__d1Original=structuredClone(r);
    const ct=r.ciphertext;
    r.ciphertext=(ct.startsWith('A')?'B':'A')+ct.slice(1);
    await new Promise((resolve,reject)=>{
     const tx=db.transaction('vaultPrf','readwrite');
     tx.objectStore('vaultPrf').put(r);
     tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)
    });db.close();
   },ownerA);
   await page.click('#unlock');
   const tamper=await settled(page,'AES-GCM tampering denial');
   if(tamper!=='FAIL_UNLOCK_D1_PRF_AUTH_FAILED')
    throw Error('TAMPER_NOT_REFUSED:'+tamper);
   report.checks.push({label:'tampered PRF envelope rejected by AEAD',outcome:'PASS'});
   await page.evaluate(async()=>{
    const db=await new Promise((resolve,reject)=>{
     const q=indexedDB.open('iamina_d1_prf_research_v1');
     q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error)
    });
    await new Promise((resolve,reject)=>{
     const tx=db.transaction('vaultPrf','readwrite');
     tx.objectStore('vaultPrf').put(window.__d1Original);
     tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)
    });delete window.__d1Original;db.close();
   });
   await page.reload();
   await page.click('#unlock');
   const reopen=await settled(page,'PRF cold reopening');
   if(reopen!=='PASS_UNLOCK')throw Error('PRF_REOPEN_FAILED:'+reopen);
   await page.evaluate(()=>{window.d1Research.key?.fill(0);window.d1Research.key=null});
   report.checks.push({label:'PRF passkey unwrap after page reload',outcome:'PASS'});
   report.result='PASS_VIRTUAL_PRF_UV_KEY_WRAP_SYNTHETIC';
  }
  console.log(JSON.stringify(report,null,2));await context.close();
 }catch(e){report.result='FAIL';report.error=String(e).slice(0,320);
  console.error(e);process.exitCode=1}
 finally{
  fs.writeFileSync('d1-webauthn-prf-'+name+'.json',JSON.stringify(report,null,2));
  await browser.close();
 }
})();
