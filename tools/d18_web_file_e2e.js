/* D18 UI-level download/import test: real Flutter widgets and real Chromium.
 * Synthetic owner A only; real file picker, native Blob download and AES-GCM.
 */
'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const out='d18-web-fue-proof';
fs.mkdirSync(out,{recursive:true});
const origin='http://127.0.0.1:7386/?mode=returning&owner=a&locale=fr';
const secret='synthetic-d18-browser-phrase-2026';
const head=process.env.D18_CANDIDATE_SHA||'unknown';
const steps=[],shots=[];
const sleep=n=>new Promise(r=>setTimeout(r,n));
async function semantics(page){
 const t=page.locator('flt-semantics-placeholder');
 if(await t.count()){await t.first().focus();await page.keyboard.press('Enter');await sleep(300);}
}
async function locate(page,label){
 const options=[
  page.getByRole('textbox',{name:label,exact:false}),
  page.getByRole('button',{name:label,exact:true}),
  page.getByRole('checkbox',{name:label,exact:false}),
  page.getByText(label,{exact:true}),
  page.getByText(label,{exact:false}),
 ];
 for(const q of options)for(let k=0;k<await q.count();k++){
  const x=q.nth(k);if(await x.isVisible().catch(()=>false))return x;
 }
 return null;
}
async function get(page,label){
 for(let i=0;i<55;i++){const x=await locate(page,label);if(x)return x;await sleep(200);}
 throw Error('Element not visible: '+label);
}
async function click(page,label){
 const x=await get(page,label);await x.scrollIntoViewIfNeeded();
 await x.click({timeout:6000});await sleep(350);
}
async function enter(page,label,value){
 const x=await get(page,label);await x.scrollIntoViewIfNeeded();
 await x.click({timeout:6000});await page.keyboard.press('ControlOrMeta+A');
 await page.keyboard.insertText(value);await sleep(180);
}
async function snap(page,name){
 const file='file-e2e-'+name+'.png';
 await page.screenshot({path:path.join(out,file),fullPage:false,animations:'disabled'});
 shots.push(file);
}
async function check(page,label){
 await get(page,label);steps.push({check:label,pass:true});
}
(async()=>{
 let browser,context,second;
 try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});
  let page=await context.newPage();
  await page.goto(origin,{waitUntil:'domcontentloaded',timeout:60000});await sleep(2800);await semantics(page);
  await click(page,'Informations personnelles facultatives');
  await enter(page,'Année de naissance (facultative)','1994');
  await click(page,'Enregistrer');
  await check(page,'Informations enregistrées localement uniquement.');
  await snap(page,'birth-year-saved');
  await click(page,'Données & appareils');
  await click(page,'Créer une sauvegarde chiffrée');
  await enter(page,'Phrase secrète (12 caractères minimum)',secret);
  await enter(page,'Confirmer la phrase secrète',secret);
  await click(page,'Chiffrer le fichier');
  await check(page,'Télécharger le fichier');
  const downloadPromise=page.waitForEvent('download',{timeout:20000});
  await click(page,'Télécharger le fichier');
  const download=await downloadPromise;
  const saved=await download.path(),payload=fs.readFileSync(saved);
  const envelope=JSON.parse(payload.toString('utf8'));
  if(envelope.format!=='iamina-d18-encrypted' ||
     !envelope.sealed || 'vault' in envelope || 'owner' in envelope)
    throw Error('Downloaded plaintext or malformed D18 backup');
  steps.push({check:'Real browser Blob download encrypted file',pass:true,
    bytes:payload.length,filename:download.suggestedFilename()});
  await snap(page,'encrypted-file-downloaded');
  await context.close();context=null;
  second=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});
  page=await second.newPage();
  await page.goto(origin,{waitUntil:'domcontentloaded',timeout:60000});await sleep(2800);await semantics(page);
  await click(page,'Données & appareils');
  await click(page,'Restaurer une sauvegarde');
  const chooserPromise=page.waitForEvent('filechooser',{timeout:20000});
  await click(page,'Choisir un fichier .iamina');
  const chooser=await chooserPromise;
  await chooser.setFiles({name:'iamina-d18-backup.iamina',
    mimeType:'application/octet-stream',buffer:payload});
  await sleep(450);
  await enter(page,'Phrase secrète',secret);
  await click(page,'Déchiffrer et examiner');
  await check(page,'Aperçu vérifié du fichier');
  await check(page,'Informations personnelles : présentes');
  await snap(page,'restoration-preview');
  await click(page,'Je confirme restaurer ces informations dans mon coffre D18 vide.');
  await click(page,'Restaurer');
  await check(page,'Données D18 restaurées et vérifiées.');
  await snap(page,'restored-success');
  await page.reload({waitUntil:'domcontentloaded'});await sleep(2700);await semantics(page);
  await click(page,'Informations personnelles facultatives');
  const year=await get(page,'Année de naissance (facultative)');
  await year.click();
  const values=await page.evaluate(()=>
    [...document.querySelectorAll('input,textarea')].map(x=>x.value||'').filter(Boolean));
  if(!values.includes('1994'))throw Error('Restored birth year missing in actual Flutter input '+JSON.stringify(values));
  steps.push({check:'Fresh Chromium profile file restoration persists after reload',pass:true});
  await snap(page,'reloaded-restored-year');
 }catch(err){
  steps.push({check:'e2e',pass:false,error:String(err.message||err).slice(0,700)});
  console.error(err);
 }finally{
  if(context)await context.close();
  if(second)await second.close();
  if(browser)await browser.close();
 }
 const report={head,kind:'Real IAMINA Flutter UI click → AES encryption → Blob download → fresh Chromium UI file chooser → authenticated preview → restoration → reload',
  steps,shots,passed:steps.every(s=>s.pass)};
 fs.writeFileSync(path.join(out,'ui-file-roundtrip-report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({head,passed:report.passed,steps:steps.length,shots,error:steps.filter(s=>!s.pass)},null,2));
 if(!report.passed)process.exitCode=1;
})().catch(err=>{console.error(err);process.exitCode=1;});
