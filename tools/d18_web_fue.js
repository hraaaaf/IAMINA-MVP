/* D18 true Flutter Web Profile UX FUE, synthetic owner A/B. No production data. */
'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const out='d18-web-fue-proof',origin='http://127.0.0.1:7386';
fs.mkdirSync(out,{recursive:true});
const viewports=[[390,844],[768,1024],[1280,900]];
const head=process.env.D18_CANDIDATE_SHA||'unknown';
const copy={
  fr:{page:'Mon Profil',section:'Informations personnelles facultatives',data:'Données & appareils',export:'Créer une sauvegarde chiffrée',restore:'Restaurer une sauvegarde',exportDialog:'Phrase secrète (12 caractères minimum)',restoreDialog:'Choisir un fichier .iamina',year:'Année de naissance (facultative)',weight:'Poids mesuré'},
  ar:{page:'ملفي الشخصي',section:'معلومات شخصية اختيارية',data:'البيانات والأجهزة',export:'إنشاء نسخة احتياطية مشفرة',restore:'استعادة نسخة احتياطية',exportDialog:'العبارة السرية (12 حرفًا على الأقل)',restoreDialog:'اختر ملف .iamina',year:'سنة الميلاد (اختياري)',weight:'الوزن المقاس'},
};
const report={head,kind:'real Chrome, production Flutter Profile + patient scoped IndexedDB, synthetic owner',cases:[],errors:[],notProven:['hosted authentication','clinical patient release','cryptographic penetration testing','download restoration after clearing storage']};
function url(owner,locale){return origin+'/?mode=returning&ip=none&owner='+owner+'&locale='+locale;}
function sleep(n){return new Promise(r=>setTimeout(r,n));}
async function semantics(page){
 const t=page.locator('flt-semantics-placeholder');
 if(await t.count()){await t.first().focus();await page.keyboard.press('Enter');await sleep(300);}
}
async function find(page,label){
 const candidates=[
  page.getByRole('button',{name:label,exact:true}),
  page.getByRole('textbox',{name:label,exact:false}),
  page.getByText(label,{exact:true}),
  page.getByRole('button',{name:label,exact:false}),
  page.getByText(label,{exact:false}),
 ];
 for(const locator of candidates)for(let i=0;i<await locator.count();i++){
  const x=locator.nth(i);
  if(await x.isVisible().catch(()=>false))return x;
 }
 return null;
}
async function required(page,label){
 for(let n=0;n<55;n++){const x=await find(page,label);if(x)return x;await sleep(180);}
 throw Error('Missing visible UI: '+label);
}
async function click(page,label){const x=await required(page,label);await x.scrollIntoViewIfNeeded();await x.click({timeout:7000});await sleep(500);}
async function screenshot(page,locale,size,phase){
 const file=[locale,size.join('x'),phase].join('-')+'.png';
 await page.screenshot({path:path.join(out,file),animations:'disabled',fullPage:false});
 return file;
}
async function inspectLayout(page,width){
 const m=await page.evaluate(()=>({
  width:document.documentElement.clientWidth,
  scrollWidth:document.documentElement.scrollWidth,
  flutterError:document.documentElement.dataset.d5FlutterError||null,
  bootError:document.documentElement.dataset.d5BootError||null,
  title:document.title,
 }));
 if(m.scrollWidth>width+4 || m.flutterError || m.bootError)throw Error('Layout/Flutter boot issue '+JSON.stringify(m));
 return m;
}
async function run(browser,locale,size){
 const name=locale+'-'+size.join('x');
 const record={name,pass:false,images:[],errors:[]};
 let context;
 try{
  context=await browser.newContext({viewport:{width:size[0],height:size[1]},locale:locale==='ar'?'ar-MA':'fr-FR',deviceScaleFactor:1});
  const page=await context.newPage();
  page.on('pageerror',err=>record.errors.push('pageerror: '+String(err).slice(0,240)));
  await page.goto(url('a',locale),{waitUntil:'domcontentloaded',timeout:50000});
  await sleep(3200);await semantics(page);
  await required(page,copy[locale].section);
  record.images.push(await screenshot(page,locale,size,'profile-collapsed'));
  await click(page,copy[locale].section);
  await required(page,copy[locale].year);
  await required(page,copy[locale].weight);
  record.images.push(await screenshot(page,locale,size,'profile-progressive-open'));
  await inspectLayout(page,size[0]);
  await click(page,copy[locale].data);
  await required(page,copy[locale].export);
  await required(page,copy[locale].restore);
  await click(page,copy[locale].export);
  await required(page,copy[locale].exportDialog);
  record.images.push(await screenshot(page,locale,size,'encrypted-export-dialog'));
  // Close via Escape to avoid language-specific buttons.
  await page.keyboard.press('Escape');await sleep(350);
  await click(page,copy[locale].restore);
  await required(page,copy[locale].restoreDialog);
  record.images.push(await screenshot(page,locale,size,'restore-dialog'));
  await inspectLayout(page,size[0]);
  if(record.errors.length)throw Error('Browser page errors: '+record.errors.join('; '));
  record.pass=true;
 }catch(e){record.error=String(e.message||e).slice(0,800);report.errors.push(name+': '+record.error);}
 finally{if(context)await context.close();}
 report.cases.push(record);
}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  for(const locale of ['fr','ar'])for(const size of viewports)await run(browser,locale,size);
 }finally{await browser.close();}
 report.passed=report.cases.filter(x=>x.pass).length;
 report.total=report.cases.length;
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({head,passed:report.passed,total:report.total,errors:report.errors},null,2));
 if(report.passed!==report.total)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
