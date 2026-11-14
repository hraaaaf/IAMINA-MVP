// D1/J2 Chrome test of actual browser inventory and worker registrations.
// All identities/data are synthetic. Read-only assessment; no migration code.
'use strict';
const {chromium}=require('playwright');
const fs=require('fs');
const dir='d1-j2-synthetic-preflight-proof';
const origin='http://127.0.0.1:7482/';
const dbA='amina_vault_v1_native_734';
const dbB='amina_vault_v1_native_812';
const device='amina_vault_v1_device_1234567841234abc8abcdef012345678';
const attested={sourceName:dbA,ownerType:'native',nativeId:734,
  remoteAccountVerified:true,sourcePossessionVerified:true,
  explicitConsent:true,writerRetirementAttested:true,
  backupRestoreIndependentlyVerified:true,backupManifestSha256:'a'.repeat(64)};
const proof={head:process.env.D1_CANDIDATE_SHA||'unknown',
  scope:'read-only browser source inventory with synthetic attestations',
  clinicalGo:false,permissionToMigrate:false,result:'NOT_RUN',checks:{}};
function check(ok,msg){if(!ok)throw Error('J2 ASSERT '+msg);}
async function seed(page,dbName){
  await page.evaluate(async dbName=>{
    const req=indexedDB.open(dbName,1);
    req.onupgradeneeded=()=>req.result.createObjectStore('synthetic');
    const db=await new Promise((res,rej)=>{
      req.onsuccess=()=>res(req.result);req.onerror=()=>rej(req.error);
    });
    try{
      const tx=db.transaction('synthetic','readwrite');
      tx.objectStore('synthetic').put('SYNTHETIC_DO_NOT_MIGRATE','sentinel');
      await new Promise((resolve,reject)=>{
        tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);
        tx.onabort=()=>reject(tx.error);
      });
    } finally{db.close();}
  },dbName);
}
async function snapshot(page){
  return page.evaluate(async()=>{
    const names=(await indexedDB.databases()).map(x=>x.name).sort();
    const evidence=[];
    for(const name of names){
      const req=indexedDB.open(name);
      const db=await new Promise((res,rej)=>{
        req.onsuccess=()=>res(req.result);req.onerror=()=>rej(req.error);
      });
      try{
        if(!db.objectStoreNames.contains('synthetic'))continue;
        const tx=db.transaction('synthetic','readonly');
        const r=tx.objectStore('synthetic').get('sentinel');
        const value=await new Promise((res,rej)=>{
          r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);
        });
        evidence.push({name,version:db.version,value});
      }finally{db.close();}
    }
    return JSON.stringify(evidence);
  });
}
(async()=>{
  fs.mkdirSync(dir,{recursive:true});
  const browser=await chromium.launch({headless:true});
  const cases=[
    ['owned native awaiting human review',[dbA],attested,
      'J2_READY_FOR_EXTERNAL_SECURITY_REVIEW'],
    ['ambiguous global amina database',['amina'],attested,
      'J2_LEGACY_UNOWNED_AMBIGUOUS'],
    ['other owner in same browser',[dbA,dbB],attested,
      'J2_MULTIPLE_LEGACY_OWNERS'],
    ['wrong native account',[dbA],{...attested,nativeId:812},
      'J2_NATIVE_IDENTITY_SCOPE_MISMATCH'],
    ['missing identity proof',[dbA],
      {...attested,remoteAccountVerified:false},
      'J2_VERIFIED_REMOTE_ACCOUNT_REQUIRED'],
    ['missing source possession',[dbA],
      {...attested,sourcePossessionVerified:false},
      'J2_SOURCE_POSSESSION_REQUIRED'],
    ['no consent',[dbA],{...attested,explicitConsent:false},
      'J2_EXPLICIT_PATIENT_CONSENT_REQUIRED'],
    ['backup not independently verified',[dbA],
      {...attested,backupRestoreIndependentlyVerified:false},
      'J2_INDEPENDENT_BACKUP_RESTORE_PROOF_REQUIRED'],
    ['writer retirement not attested',[dbA],
      {...attested,writerRetirementAttested:false},
      'J2_WRITER_FENCING_PROOF_REQUIRED'],
    ['unknown legacy namespace',['amina_vault_v1_native_bad'],attested,
      'J2_LEGACY_NAMESPACE_UNTRUSTED'],
    ['no source found',[],attested,'J2_NO_MIGRATABLE_LEGACY_SOURCE'],
    ['device-only lacking possession',[device],
      {...attested,sourceName:device,ownerType:'device',
        deviceScopeId:device.slice('amina_vault_v1_device_'.length),
        deviceOwnershipVerified:false},
      'J2_VERIFIED_DEVICE_OWNER_REQUIRED']
  ];
  try{
    for(const [name,names,request,expected] of cases){
      const ctx=await browser.newContext({
        serviceWorkers:'allow',locale:'en-US'});
      try{
        const page=await ctx.newPage();await page.goto(origin);
        for(const dbName of names)await seed(page,dbName);
        const before=await snapshot(page);
        const result=await page.evaluate(async request=>
          IaminaD1J2PreflightCandidate.inspect(request),request);
        const after=await snapshot(page);
        check(result.code===expected,name+' code '+result.code+' expected '+expected);
        check(result.authorizedToMigrate===false,
          name+' must never grant migration');
        check(before===after,name+' modified legacy stores');
        proof.checks[name]='PASS';
      }finally{await ctx.close();}
    }
    // Real browser SW registration (still installed): migration is refused
    // even if all caller-supplied synthetic attestations are true.
    const worker=await browser.newContext({
      serviceWorkers:'allow',locale:'en-US'});
    try{
      const page=await worker.newPage();await page.goto(origin);
      await seed(page,dbA);
      const active=await page.evaluate(async()=>{
        const r=await navigator.serviceWorker.register('/j2-legacy-sw.js');
        await navigator.serviceWorker.ready;
        return !!r.active;
      });
      check(active,'synthetic installed worker missing');
      const r=await page.evaluate(req=>
        IaminaD1J2PreflightCandidate.inspect(req),attested);
      check(r.code==='J2_UNFENCED_INSTALLED_WORKER',
        'installed offline writer must block even with attestations');
      check(r.authorizedToMigrate===false,'installed writer bypass');
      proof.checks['installed service worker blocks']='PASS';
    }finally{await worker.close();}
    // Fail closed when inventory API is absent.
    const unsupported=await browser.newContext({locale:'en-US'});
    try{
      const page=await unsupported.newPage();await page.goto(origin);
      const c=await page.evaluate(async req=>{
        Object.defineProperty(indexedDB,'databases',{
          configurable:true,value:undefined});
        return IaminaD1J2PreflightCandidate.inspect(req);
      },attested);
      check(c.code==='J2_INDEXEDDB_INVENTORY_UNSUPPORTED',
        'unsupported inventory fell back to unsafe admission');
      proof.checks['unsupported IndexedDB inventory fails closed']='PASS';
    }finally{await unsupported.close();}
    proof.result='PASS_READ_ONLY_ADVISORY_ONLY';
  }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2200);
    throw e;}
  finally{
    fs.writeFileSync(dir+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_J2_MIGRATION_PREFLIGHT='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>{process.exitCode=1;});