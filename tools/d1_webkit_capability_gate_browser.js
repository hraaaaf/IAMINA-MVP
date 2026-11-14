// D1-P0: genuine Playwright WebKit engine capability / fail-closed gate.
// NOT Safari/iOS hardware certification. Synthetic bytes, no patient data.
'use strict';
const {webKit} = {webKit: require('playwright').webkit};
const fs = require('fs');
const folder='d1-webkit-capability-proof';
const ownerA='amina_vault_v1_native_735';
const ownerB='amina_vault_v1_native_736';
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',
  engine:'Playwright WebKit (not Safari/iOS device)',
  clinicalGo:false,result:'NOT_RUN'};
function check(ok, message) {if(!ok) throw Error('WEBKIT_GATE: '+message);}
async function lease(page,owner) {
  return page.evaluate(async owner=>{
    try {
      const token=await IaminaD1CryptoCandidate.acquireExclusiveLease(owner);
      return {granted:true,token};
    } catch(e){return {granted:false,error:String(e)};}
  },owner);
}
async function release(page,owner,token) {
  return page.evaluate(({owner,token})=>
    IaminaD1CryptoCandidate.releaseExclusiveLease(owner,token),{owner,token});
}
(async()=>{
 fs.mkdirSync(folder,{recursive:true});
 const browser=await webKit.launch({headless:true});
 try{
  const ctx=await browser.newContext({locale:'en-US',serviceWorkers:'block'});
  const a=await ctx.newPage();
  const b=await ctx.newPage();
  const errors=[];
  for(const p of [a,b]) p.on('pageerror',e=>errors.push(String(e).slice(0,400)));
  await Promise.all([
    a.goto('http://127.0.0.1:7476/',{waitUntil:'load'}),
    b.goto('http://127.0.0.1:7476/',{waitUntil:'load'})
  ]);
  const c=await a.evaluate(async()=>{
    const api=globalThis.IaminaD1CryptoCandidate;
    const encode=bytes=>btoa(String.fromCharCode(...bytes))
      .replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
    const result={candidateLoaded:!!api,secureContext:isSecureContext,
      cryptoAvailable:!!crypto.subtle,
      inventoryApiAvailable:typeof indexedDB.databases==='function',
      locksApiAvailable:typeof navigator.locks?.request==='function',
      randomUuidAvailable:typeof crypto.randomUUID==='function',
      webCryptoRoundTrip:false,ownerAadRejects:false,
      wrongRecoveryRejects:false,inventoryRead:false,
      inventoryExplicitRefusal:false,invalidOwnerRejects:false};
    if(!api) return result;
    const r=encode(new Uint8Array(32).fill(7));
    const key=encode(new Uint8Array(32).fill(21));
    const salt=encode(new Uint8Array(16).fill(18));
    const iv=encode(new Uint8Array(12).fill(22));
    if(result.cryptoAvailable && result.secureContext){
      const ct=await api.encrypt(r,key,salt,iv,'amina_vault_v1_native_735');
      result.webCryptoRoundTrip=
        await api.decrypt(r,ct,salt,iv,'amina_vault_v1_native_735')===key
        && ct!==key;
      try{await api.decrypt(r,ct,salt,iv,'amina_vault_v1_native_736');}
      catch(e){result.ownerAadRejects=true;}
      try{await api.decrypt(encode(new Uint8Array(32).fill(6)),
        ct,salt,iv,'amina_vault_v1_native_735');}
      catch(e){result.wrongRecoveryRejects=true;}
    }
    try{result.inventoryRead=Array.isArray(
      JSON.parse(await api.indexedDbNames()));}
    catch(e){result.inventoryExplicitRefusal=
      String(e).includes('D1_INDEXEDDB_INVENTORY_UNSUPPORTED');}
    try{const t=await api.acquireExclusiveLease('amina');
      await api.releaseExclusiveLease('amina',t);}
    catch(e){result.invalidOwnerRejects=
      String(e).includes('D1_VAULT_LOCK_OWNER_INVALID');}
    return result;
  });
  proof.capabilities=c;
  check(c.candidateLoaded && c.secureContext,'secure fixture not loaded');
  check(c.cryptoAvailable && c.webCryptoRoundTrip &&
    c.ownerAadRejects && c.wrongRecoveryRejects,
    'native WebCrypto or authenticated owner/recovery property failed');
  check(c.inventoryApiAvailable ? c.inventoryRead : c.inventoryExplicitRefusal,
    'IndexedDB inventory must return names OR explicit refusal');
  check(c.invalidOwnerRejects,'invalid owner scope accepted');
  if(c.locksApiAvailable && c.randomUuidAvailable){
    const held=await lease(a,ownerA);
    check(held.granted,'first exclusive owner lease rejected');
    try{
      const denied=await lease(b,ownerA);
      proof.sameOwnerSecondTabDenied=!denied.granted &&
        denied.error.includes('D1_VAULT_TAB_BUSY');
      check(proof.sameOwnerSecondTabDenied,'second tab got owner A lease');
      const independent=await lease(b,ownerB);
      proof.otherOwnerIndependent=independent.granted;
      check(proof.otherOwnerIndependent,'independent owner locked out');
      await release(b,ownerB,independent.token);
    }finally{await release(a,ownerA,held.token);}
    const again=await lease(b,ownerA);
    proof.ownerReacquiredAfterRelease=again.granted;
    check(proof.ownerReacquiredAfterRelease,'owner A not released');
    await release(b,ownerA,again.token);
    proof.webLocksBehavior='exclusive-pass';
  }else{
    const denied=await lease(a,ownerA);
    proof.webLocksUnsupportedDenied=!denied.granted &&
      denied.error.includes('D1_VAULT_WEB_LOCKS_UNSUPPORTED');
    check(proof.webLocksUnsupportedDenied,'missing Web Locks not denied');
    proof.webLocksBehavior='unsupported-fail-closed';
  }
  proof.browserEligibleForCandidate=c.inventoryRead &&
    c.locksApiAvailable && c.randomUuidAvailable;
  proof.pageErrors=errors;
  check(errors.length===0,'unexpected JS page error');
  await ctx.close();
  proof.result='PASS_SAFE_BEHAVIOR_ONLY';
 }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2300);throw e;}
 finally{fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
  console.log('D1_WEBKIT_CAPABILITY_GATE='+JSON.stringify(proof));
  await browser.close();}
})().catch(()=>{process.exitCode=1;});
