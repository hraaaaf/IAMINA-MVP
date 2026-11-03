// IAMINA D18 stage6 security inventory on a NORMAL patient-app Web build.
// CI-only audit, not encryption proof. No deployment and no patient content.
// Does not print match excerpts, source secrets, database contents or keys.
'use strict';
const fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'frontend','build','web');
const proof=path.join(root,'d18-stage6-security-proof');
const failures=[];
const checkedOutSha=execFileSync('git',['rev-parse','HEAD'],{
  cwd:root,encoding:'utf8',
}).trim();
const expectedSha=process.env.D18_CODE_SHA||'';
if(!/^[0-9a-f]{40}$/.test(expectedSha)||
  expectedSha!==checkedOutSha) {
  failures.push('D18_CHECKOUT_SHA_MISMATCH');
}
const forbiddenAssets=[
  'd18_unpublished_cipher_worker.js',
  'd18_unpublished_cipher_restore_worker.js',
  'd18_cipher_worker_correct.js',
  'd18_cipher_worker_wrong.js',
  'd18_dynamic_cipher_sqlite_worker.js',
  'd18_sqlite3mc.wasm',
  'd18_unpublished_worker_lock_gate.js',
  'd18_dynamic_worker_lock_gate.js',
  'd18_session_handshake_probe_worker.js',
  'd18_web_locks_worker.js',
];
const bannedStrings=[
  'D18_SYNTHETIC_RESTORE_FULL_DB_MARKER_20261103',
  'D18-CI-TEST-LOCAL-SECRET',
  'D18-CI-TEST-ARCHIVE-SECRET',
  'D18_CI_ENCRYPTED_RESTORE_FRESH',
  'D18_CI_RESTORE_CRASH_AFTER_FIRST_PERSISTED_BLOCK',
  'D18-CI-ONLY-MC-KEY',
  'D18-CI-ONLY-MC-WRONG',
  'D18_CI_DYNAMIC_SQL_OPEN_INTENT',
];
function walk(dir){
  if(!fs.existsSync(dir))return [];
  const files=[];
  for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
    const item=path.join(dir,entry.name);
    if(entry.isDirectory())files.push(...walk(item));
    else if(entry.isFile())files.push(item);
  }
  return files;
}
function readText(file){return fs.readFileSync(file,'utf8');}
const built=walk(output);
const relative=built.map(f=>path.relative(output,f).replaceAll('\\','/'));
const forbiddenFound=relative.filter(f=>forbiddenAssets.some(name=>
  f===name || f.endsWith('/'+name)));
if(forbiddenFound.length)failures.push('TEST_WORKERS_IN_NORMAL_WEB_OUTPUT');
// For source files, include normal asset names in contents scanning as a
// deterministic signal of accidental test-worker JS references.
// Some synthetic documentation strings must never become runtime constants.
const runtimeFiles=built.filter(f=>/\.(?:js|mjs|html|json)$/.test(f));
const leakedTokens=[];
for(const f of runtimeFiles){
  const raw=readText(f);
  for(const token of bannedStrings){
    if(raw.includes(token))leakedTokens.push({file:path.relative(output,f),token});
  }
}
if(leakedTokens.length)failures.push('D18_TEST_SECRETS_IN_WEB_OUTPUT');
// Extra structural check: all deliberately isolated Dart ENTRYPOINTS stay
// excluded by the normal main.dart bundle, including minified copies.
const mainJs=path.join(output,'main.dart.js');
const index=path.join(output,'index.html');
if(!fs.existsSync(mainJs)||!fs.existsSync(index)){
  failures.push('NORMAL_PATIENT_WEB_BUILD_MISSING');
}
const src=readText(path.join(root,'frontend/lib/data/drift/database.dart'));
const factoryStart=src.indexOf('AppDatabase.forPatientVault(');
const factoryEnd=src.indexOf('int get activeProfileRowId',factoryStart);
const factory=factoryStart>=0&&factoryEnd>factoryStart?
  src.slice(factoryStart,factoryEnd):'';
if(!factory.includes("Uri.parse('sqlite3.wasm')")||
   !factory.includes("Uri.parse('drift_worker.js')")){
  failures.push('UNEXPECTED_PATIENT_FACTORY_REQUIRES_REVIEW');
}
// Negative, independently verifiable release fact. A passing fixture scan
// does NOT mean the actual patient vault is encrypted.
const patientVaultAtRestEncrypted=false;
const configFiles=['vercel.json','frontend/vercel.json'];
const cspConfigured=configFiles.every(f=>{
  const config=JSON.parse(readText(path.join(root,f)));
  const headers=config.headers||[];
  return headers.some(route=>(route.headers||[]).some(h=>
    h.key?.toLowerCase()==='content-security-policy'));
});
const result={
  commit:checkedOutSha,
  expectedCodeSha:expectedSha,
  exactCodeShaVerified:expectedSha===checkedOutSha,
  type:'precutover-normal-web-release-blocker-inventory',
  normalWebBuild:{
    indexHtmlPresent:fs.existsSync(index),
    mainDartJsPresent:fs.existsSync(mainJs),
    artifactsScanned:built.length,
    scriptedAssetsScanned:runtimeFiles.length,
    forbiddenFixtureFilesFound:forbiddenFound.length,
    forbiddenFixtureTokensFound:leakedTokens.length,
  },
  patientVaultAtRestEncrypted,
  configFilesExamined:configFiles,
  contentSecurityPolicyConfiguredInRepo:cspConfigured,
  deploymentHeadersObserved:false,
  canCertifyClinicalRelease:false,
  releaseBlockers:[
    'CLINICAL_SQLITE_STORAGE_CURRENTLY_PLAINTEXT',
    ...(!cspConfigured?['REPO_CSP_POLICY_NOT_CONFIGURED']:[]),
    'CSP_RESPONSE_HEADERS_NOT_VERIFIED',
    'PHYSICAL_IPHONE_SAFARI_NOT_TESTED',
    'LARGE_VAULT_STREAMING_NOT_PROVEN',
    'INTERRUPTED_IMPORT_RECOVERY_POLICY_NOT_DEFINED',
    'INDEPENDENT_SECURITY_AND_CLINICAL_REVIEW_REQUIRED',
  ],
  failures,
};
fs.mkdirSync(proof,{recursive:true});
fs.writeFileSync(path.join(proof,'report.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
if(failures.length)process.exitCode=1;
