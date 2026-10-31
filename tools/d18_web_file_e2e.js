/* D18 UI-level download/import test: real Flutter widgets and real Chromium.
 * Synthetic owner A only; real file picker, native Blob download and AES-GCM.
 */
'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const out='d18-web-fue-proof';
fs.mkdirSync(out,{recursive:true});
const origin='http://127.0.0.1:7388/?mode=returning&ip=none&owner=a&locale=fr';
const secret='synthetic-d18-browser-phrase-2026';
const head=process.env.D18_CANDIDATE_SHA||'unknown';
const steps=[],shots=[],browserErrors=[];
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
 for(let i=0;i<80;i++){const x=await locate(page,label);if(x)return x;await sleep(200);}
 throw Error('Element not visible after verified Flutter bootstrap: '+label);
}
async function bootRealProfile(page){
 // The separate E2E browser was previously interrogated before the Flutter
 // bootstrap had run (default index title, no d5Stage); require the app itself
 // to attest readiness, not just DOMContentLoaded on an empty HTML shell.
 const network=[];
 page.on('pageerror',e=>network.push('pageerror '+String(e).slice(0,280)));
 page.on('requestfailed',r=>network.push('requestfailed '+r.url()+' '+r.failure()));
 page.on('response',r=>{if(r.status()>=400)network.push('HTTP '+r.status()+' '+r.url());});
 await page.goto(origin,{waitUntil:'domcontentloaded',timeout:60000});
 try{
  await page.waitForFunction(()=>
    document.documentElement.dataset.d5Stage==='runApp' ||
    !!document.documentElement.dataset.d5BootError ||
    document.title.startsWith('D5_FUE_BOOT_FAILURE'),
    null,{timeout:65000,polling:250});
 }catch(e){
  const state=await page.evaluate(()=>({
    title:document.title,
    stage:document.documentElement.dataset.d5Stage||null,
    bootError:document.documentElement.dataset.d5BootError||null,
    flutterError:document.documentElement.dataset.d5FlutterError||null,
    scriptCount:document.scripts.length,
  }));
  throw Error('Flutter bootstrap failed before UI actions: '+
    JSON.stringify({state,network:network.slice(-15)}));
 }
 await semantics(page);
 await get(page,'Informations personnelles facultatives');
}
async function click(page,label){
 const x=await get(page,label);await x.scrollIntoViewIfNeeded();
 await x.click({timeout:6000});await sleep(350);
}
// Flutter semantics only exposes objects in the actual scrolled viewport.
// Verify real weight history rows using user-like wheel scrolling, not a
// global DOM query that silently excludes off-screen Flutter canvas content.
async function getByScroll(page,label){
  const slug=label.replace(/[^a-z0-9]/gi,'-').slice(0,45);
  const travel=async(direction)=>{
    for(let i=0;i<42;i++){
      const found=await locate(page,label);
      if(found)return found;
      // Real screenshot from e87cde proved 450px wheel + PageDown
      // jumps past the row. Use small, observed wheel increments only
      // and check semantics after *every* movement.
      await page.mouse.move(175,655);
      await page.mouse.wheel(0,direction*135);
      await sleep(155);
      if(i===6||i===18)await snap(page,
        'scroll-'+(direction>0?'down':'up')+'-'+(i===6?'mid':'late')+'-'+slug);
    }
    return null;
  };
  const found=await travel(1)||await travel(-1);
  if(!found){
    await snap(page,'scroll-missing-'+slug);
    throw Error('Flutter history item not visible after user scrolling: '+label);
  }
  return found;
}
async function checkByScroll(page,label){
  const found=await getByScroll(page,label);
  await found.scrollIntoViewIfNeeded();
  steps.push({check:label,pass:true,source:'real-scrolled-Flutter-viewport'});
}
async function clickByScroll(page,label){
  const found=await getByScroll(page,label);
  await found.scrollIntoViewIfNeeded();
  await found.click({timeout:6000});
  await sleep(350);
}

async function enter(page,label,value){
 const x=await get(page,label);await x.scrollIntoViewIfNeeded();
 await x.click({timeout:6000});await page.keyboard.press('ControlOrMeta+A');
 await page.keyboard.insertText(value);await sleep(180);
}
// Real Flutter canvas editor proof: a click/insertText alone may silently
// type into no field. Verify the actual user's Select All → Copy result before
// proceeding. Retry a coordinate-based field focus if semantics stole focus.
async function enterVerified(page,label,value){
 await page.context().grantPermissions(['clipboard-read','clipboard-write'],
   {origin:'http://127.0.0.1:7388'});
 const failures=[];
 for(let attempt=0;attempt<3;attempt++){
   const target=await get(page,label);
   await target.scrollIntoViewIfNeeded();
   if(attempt===1){
     const bounds=await target.boundingBox();
     if(!bounds)throw Error('Missing editable bounds for '+label);
     await page.mouse.click(bounds.x+bounds.width*0.50,
       bounds.y+bounds.height*0.50);
   }else if(attempt===2){
     const inputs=page.getByRole('textbox',{name:label,exact:false});
     if(await inputs.count()){
       await inputs.first().click({timeout:3000});
     }else{
       await target.click({timeout:3000});
     }
   }else{
     await target.click({timeout:3000});
   }
   await page.keyboard.press('ControlOrMeta+A');
   if(attempt===2){
     await page.keyboard.type(value,{delay:35});
   }else{
     await page.keyboard.insertText(value);
   }
   await sleep(120);
   await page.evaluate(()=>navigator.clipboard.writeText('d18-unfocused-sentinel'));
   await page.keyboard.press('ControlOrMeta+A');
   await page.keyboard.press('ControlOrMeta+C');
   const copied=await page.evaluate(()=>navigator.clipboard.readText());
   if(copied===value){
     steps.push({check:'User keyboard confirms '+label+' value',pass:true});
     return;
   }
   const state=await page.evaluate(()=>{
     const el=document.activeElement;
     return {tag:el?.tagName||null,role:el?.getAttribute('role')||null,
       inputLength:typeof el?.value==='string'?el.value.length:null};
   });
   failures.push({attempt,copyLength:copied.length,focus:state});
 }
 throw Error('Flutter editable entry not proved for '+label+': '+
   JSON.stringify(failures));
}

async function enterSecret(page,label,value){
 // Obscured Flutter TextFields are password controls, NOT accessible-role
 // textboxes; a click on their label may never focus the actual editor.
 // Exercise the real editable input and verify only its LENGTH, never log secrets.
 const labelNode=await get(page,label);
 await labelNode.scrollIntoViewIfNeeded();
 await labelNode.click({timeout:6000});
 await sleep(130);
 const candidates=[
   page.locator('input[type="password"]:focus'),
   page.locator('input[type="password"]'),
   page.locator('input[autocomplete="new-password"]'),
 ];
 let typed=false;
 for(const group of candidates){
   for(let i=0;i<await group.count();i++){
     const input=group.nth(i);
     if(!await input.isVisible().catch(()=>false))continue;
     if(!await input.isEditable().catch(()=>false))continue;
     try {
       await input.fill(value,{timeout:3000});
       if((await input.inputValue()).length===value.length) {
         typed=true;break;
       }
     }catch(_){}
   }
   if(typed)break;
 }
 if(!typed){
   await labelNode.click({timeout:6000});
   await page.keyboard.press('ControlOrMeta+A');
   await page.keyboard.type(value,{delay:15});
   await sleep(220);
   const active=await page.evaluate(()=>{
     const el=document.activeElement;
     return {tag:el?.tagName||null,type:el?.getAttribute('type')||null,
       length:typeof el?.value==='string'?el.value.length:null};
   });
   if(active.length!==value.length){
     const count=await page.locator('input[type="password"]').count();
     throw Error('Secure Flutter field not populated: '+label+
       ' active='+JSON.stringify(active)+' passwordInputs='+count);
   }
 }
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
  context=await browser.newContext({viewport:{width:390,height:844},locale:'fr-FR',acceptDownloads:true});
  let page=await context.newPage();
   page.on('pageerror',e=>browserErrors.push('pageerror: '+String(e).slice(0,450)));
   page.on('requestfailed',r=>browserErrors.push('failed '+r.url()+' '+String(r.failure()?.errorText||'')));
  await bootRealProfile(page);
  await check(page,'Informations personnelles facultatives');
  await click(page,'Informations personnelles facultatives');
  await enter(page,'Année de naissance (facultative)','1994');
  await click(page,'Enregistrer');
  await check(page,'Informations enregistrées localement uniquement.');
  await snap(page,'birth-year-saved');
  // Real optional demographic selection, not just a Dart widget test.
  // Flutter DropdownButton draws its open menu into the canvas. The option
  // is visibly present (failure screenshot) but not exposed by Web semantics
  // while the popup is open. Use the actual keyboard selection path instead
  // of a DOM locator for an inaccessible canvas item.
  await click(page,'Non renseignée');
  for(let item=0;item<5;item++)await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await check(page,'Préfère ne pas répondre');
  await click(page,'Enregistrer');
  await check(page,'Informations enregistrées localement uniquement.');
  steps.push({check:'Optional self-declared identity saved through real Web UI',pass:true});

  // Exercise dated weight entry and append-only correction before exporting.
  // A timestamp must be chosen explicitly; opening the form is insufficient.
  // Reset focus after DropdownButton overlay, preserving the saved
  // profile. Then insist on a real keyboard copy proof of the weight editor.
  await bootRealProfile(page);
  await click(page,'Informations personnelles facultatives');
  await enterVerified(page,'Poids mesuré','72,50');
  await snap(page,'weight-entry-verified');
  await click(page,'Choisir la date et l’heure de la pesée');
  await click(page,'OK'); // explicit date confirmation
  await click(page,'OK'); // explicit time confirmation
  if(await locate(page,'Choisir la date et l’heure de la pesée')){
    await snap(page,'weight-time-not-set');
    throw Error('Date/time picker did not commit a real measuredAt value');
  }
  await snap(page,'weight-date-time-verified');
  const saveWeight=await get(page,'Ajouter cette pesée');
  if(!await saveWeight.isEnabled()){
    throw Error('Add weight disabled despite confirmed editor and picker');
  }
  await saveWeight.click({timeout:6000});
  await sleep(450);
  await snap(page,'weight-after-save-before-scroll');
  await checkByScroll(page,'72.50 kg');
  steps.push({check:'Dated weight added through real Web date/time pickers',pass:true});
  await snap(page,'dated-weight-added');
  await clickByScroll(page,'Corriger la pesée');
  await enterVerified(page,'Poids mesuré','73,00');
  await click(page,'Enregistrer la correction');
  await checkByScroll(page,'73.00 kg');
  if((await page.getByText('72.50 kg',{exact:true}).count())>0)
    throw Error('Superseded weight still visible after append-only correction');
  steps.push({check:'Corrected weight is current and superseded weight hidden',pass:true});
  await snap(page,'corrected-weight');
  await clickByScroll(page,'Données & appareils');
  await click(page,'Créer une sauvegarde chiffrée');
  await enterSecret(page,'Phrase secrète (12 caractères minimum)',secret);
  await enterSecret(page,'Confirmer la phrase secrète',secret);
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
  second=await browser.newContext({viewport:{width:390,height:844},locale:'fr-FR',acceptDownloads:true});
  page=await second.newPage();
   page.on('pageerror',e=>browserErrors.push('pageerror: '+String(e).slice(0,450)));
   page.on('requestfailed',r=>browserErrors.push('failed '+r.url()+' '+String(r.failure()?.errorText||'')));
  await bootRealProfile(page);
  await clickByScroll(page,'Données & appareils');
  await click(page,'Restaurer une sauvegarde');
  const chooserPromise=page.waitForEvent('filechooser',{timeout:20000});
  await click(page,'Choisir un fichier .iamina');
  const chooser=await chooserPromise;
  await chooser.setFiles({name:'iamina-d18-backup.iamina',
    mimeType:'application/octet-stream',buffer:payload});
  await sleep(450);
  await enterSecret(page,'Phrase secrète',secret);
  await click(page,'Déchiffrer et examiner');
  await check(page,'Aperçu vérifié du fichier');
  await check(page,'Informations personnelles : présentes');
  await snap(page,'restoration-preview');
  await click(page,'Je confirme restaurer ces informations dans mon coffre D18 vide.');
  await click(page,'Restaurer');
  await check(page,'Données D18 restaurées et vérifiées.');
  await snap(page,'restored-success');
  await bootRealProfile(page);
  await click(page,'Informations personnelles facultatives');
  const year=await get(page,'Année de naissance (facultative)');
  await year.click();
  // Flutter Web keeps the editable text node inside a Shadow DOM root.
  // document.querySelectorAll('input') on the light DOM returns [] even when
  // the patient sees 1994 (confirmed by the real failure screenshot).
  // Playwright locator pierces open shadow roots and reads the real editor.
  const values=await page.locator('input,textarea').evaluateAll(els=>
    els.map(x=>typeof x.value==='string'?x.value:'').filter(Boolean));
  const ariaYear=page.getByRole('textbox',{name:'Année de naissance (facultative)'});
  let accessibleYear='';
  if(await ariaYear.count()){
    accessibleYear=await ariaYear.first().inputValue().catch(()=>'');
  }
  const visibleYear=page.getByText('1994',{exact:true});
  const renderedYear=await visibleYear.count()>0 &&
    await visibleYear.first().isVisible().catch(()=>false);
  // Flutter's canvas-rendered TextField can show its value without exposing
  // an HTML input or visible DOM text. Assert the *real editable value* through
  // the user's keyboard copy action rather than weakening this to screenshot
  // presence or treating a missing HTML <input> as data loss.
  // A sentinel proves the copy actually replaced clipboard content.
  let copiedYear='';
  let clipboardDiagnostic='';
  try{
    await second.grantPermissions(['clipboard-read','clipboard-write'],
      {origin:'http://127.0.0.1:7388'});
    await page.evaluate(()=>navigator.clipboard.writeText('d18-copy-sentinel'));
    await year.click();
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.press('ControlOrMeta+C');
    copiedYear=await page.evaluate(()=>navigator.clipboard.readText());
  }catch(error){
    clipboardDiagnostic=String(error.message||error).slice(0,180);
  }
  const restored=values.includes('1994')||accessibleYear==='1994'||
    renderedYear||copiedYear==='1994';
  if(!restored){
    throw Error('Restored birth year not readable through actual text field; '+
      'editableInputLengths='+JSON.stringify(values.map(x=>x.length))+
      ' renderedTextVisible='+renderedYear+
      ' clipboardLength='+copiedYear.length+
      (clipboardDiagnostic?' clipboardError='+clipboardDiagnostic:''));
  }
  steps.push({check:'Reloaded birth year 1994 read from actual Flutter editable value',
    pass:true,source:copiedYear==='1994'?'keyboard clipboard':
      values.includes('1994')?'browser editor':
      accessibleYear==='1994'?'accessibility':'visible text'});
  await check(page,'Préfère ne pas répondre');
  await checkByScroll(page,'73.00 kg');
  steps.push({check:'Identity and corrected weight survive encrypted file restoration',pass:true});
  await snap(page,'restored-weight-and-identity');
  await clickByScroll(page,'Supprimer la pesée');
  await click(page,'Supprimer');
  await check(page,'Pesée supprimée localement.');
  await checkByScroll(page,'Aucune pesée enregistrée.');
  await bootRealProfile(page);
  await click(page,'Informations personnelles facultatives');
  await checkByScroll(page,'Aucune pesée enregistrée.');
  steps.push({check:'Deletion of restored weight persists across browser reload',pass:true});
  await snap(page,'reloaded-weight-deleted');
  steps.push({check:'Fresh Chromium profile file restoration persists after reload',pass:true});
  await snap(page,'reloaded-restored-year');
 }catch(err){
  const current=second||context;
  if(current){
    const pages=current.pages();
    const p=pages.length?pages[pages.length-1]:null;
    if(p){
      try{
        const state=await p.evaluate(()=>({title:document.title,
          bootError:document.documentElement.dataset.d5BootError||null,
          flutterError:document.documentElement.dataset.d5FlutterError||null,
          stage:document.documentElement.dataset.d5Stage||null}));
        steps.push({check:'browser diagnostic',pass:false,...state});
        await snap(p,'failure-debug');
      }catch(_){}
    }
  }
  steps.push({check:'e2e',pass:false,error:String(err.message||err).slice(0,700),browserErrors:browserErrors.slice(-15)});
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
