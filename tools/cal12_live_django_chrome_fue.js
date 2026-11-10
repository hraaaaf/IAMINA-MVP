/* CAL-12: real Chromium clicks -> disposable Django Ninja bearer -> PG16
 * fixture-only consent ledger. This is NOT production Flutter UI.
 * Never captures bearer or passwords in artifacts.
 */
'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');

const ROOT='http://127.0.0.1:8000';
const PASSWORD=process.env.CAL12_FUE_PASSWORD;
const OUT=path.resolve('cal12-live-web-fue-proof');
const matrix=[
  ['fr',390,844],['ar',390,844],
  ['fr',768,1024],['ar',768,1024],
  ['fr',1280,900],['ar',1280,900],
];
if(!PASSWORD||PASSWORD.length<30||process.env.CAL12_FUE_TEST_ONLY!=='1')
  throw Error('Synthetic browser FUE guard not configured');
fs.mkdirSync(OUT,{recursive:true});

const proof={
  status:'INCOMPLETE',
  commit:process.env.CAL12_HEAD||'unknown',
  topology:'real Chromium -> Django native HTTP -> PostgreSQL16 disposable',
  surface:'isolated fixture-only HTML; NOT production Flutter UI',
  realPatientExportEnabled:false,
  actualRecipientVerification:false,
  actualFileDelivery:false,
  legalConsentApproval:false,
  noClinicalData:true,
  cases:[],captures:[],errors:[],
};
const digest=buf=>crypto.createHash('sha256').update(buf).digest('hex');
const pause=ms=>new Promise(r=>setTimeout(r,ms));

async function statusClick(page,testid,expected,checks){
  await page.getByTestId(testid).click({timeout:10000});
  await page.waitForFunction((text)=>{
    const target=document.querySelector('[data-testid="status"]');
    return target&&target.textContent===text;
  },expected,{timeout:12000});
  assert.equal(await page.getByTestId('status').textContent(),expected);
  checks.push({action:testid,result:expected,status:'PASS'});
}
async function screenshot(page,label,name,record){
  const file=label+'-'+name+'.png';
  const filePath=path.join(OUT,file);
  await page.screenshot({path:filePath,animations:'disabled'});
  const bytes=fs.readFileSync(filePath);
  assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
  assert(bytes.length>9000,'Blank image '+file);
  const actualWidth=bytes.readUInt32BE(16),actualHeight=bytes.readUInt32BE(20);
  assert.equal(actualWidth,record.width);assert.equal(actualHeight,record.height);
  proof.captures.push({name:file,sha256:digest(bytes),width:actualWidth,height:actualHeight});
  record.captures.push(file);
}
async function login(page,locale,width,actor,checks){
  const address='cal12-fixture-'+actor+'-'+locale+'-'+String(width)+'@example.invalid';
  await page.getByTestId('email').fill(address);
  await page.getByTestId('password').fill(PASSWORD);
  const responseSeen=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/auth/login');
  await statusClick(page,'login','LOGIN_OK',checks);
  const res=await responseSeen;
  assert.equal(res.status(),200,'Real Django login returned 200');
  assert.equal(await page.getByTestId('session').textContent(),address);
  await page.getByTestId('password').fill('');
}
async function choose(page,recipient,proofRef,clock,notice){
  await page.getByTestId('recipient').selectOption(recipient);
  await page.getByTestId('proof').selectOption(proofRef);
  await page.getByTestId('offset').selectOption(String(clock));
  await page.getByTestId('notice').fill(notice);
}
async function scenario(browser,locale,width,height){
  const label=locale+'-'+String(width);
  const context=await browser.newContext({
    viewport:{width,height},
    locale:locale==='fr'?'fr-FR':'ar-MA',
    serviceWorkers:'block',
  });
  const record={label,width,height,checks:[],captures:[],http:{}};
  const page=await context.newPage();
  const external=[];
  try{
    await context.route('**/*',async route=>{
      const url=route.request().url();
      const u=new URL(url);
      if(u.protocol!=='http:'||u.hostname!=='127.0.0.1'||u.port!=='8000'){
        external.push({scheme:u.protocol,host:u.hostname});
        await route.abort();return;
      }
      await route.continue();
    });
    page.on('response',response=>{
      if(!response.url().startsWith(ROOT))return;
      const route=new URL(response.url()).pathname;
      const key=route+' #'+String(response.status());
      record.http[key]=(record.http[key]||0)+1;
    });
    await page.goto(ROOT+'/_cal12_fixture/?locale='+locale,{waitUntil:'domcontentloaded'});
    await page.getByTestId('status').waitFor({state:'visible'});
    assert.equal(await page.locator('html').getAttribute('dir'),locale==='ar'?'rtl':'ltr');
    assert.equal(await page.locator('html').getAttribute('lang'),locale);
    assert.match(await page.getByTestId('no-export').textContent(),/AUCUN PDF|أي/);
    await screenshot(page,label,'01-before',record);
    await statusClick(page,'no-bearer','NO_BEARER_DENIED',record.checks);
    await login(page,locale,width,'a',record.checks);
    await page.getByTestId('agree').check();
    await choose(page,'fixture:doctor:one','fixture:preview:doctor-one',0,'CAL12-DRAFT-2026-11-10.1');
    await statusClick(page,'grant','CONSENT_SAVED',record.checks);
    await statusClick(page,'check','READY_YES',record.checks);
    await screenshot(page,label,'02-a-consent-valid',record);

    await statusClick(page,'logout','LOGOUT_OK',record.checks);
    await statusClick(page,'old-token','OLD_TOKEN_DENIED',record.checks);
    await login(page,locale,width,'b',record.checks);
    await statusClick(page,'check','CLIENT_STALE_DENIED',record.checks);
    await statusClick(page,'stale','SERVER_STALE_DENIED',record.checks);
    await screenshot(page,label,'03-b-owner-denied',record);

    await statusClick(page,'logout','LOGOUT_OK',record.checks);
    await login(page,locale,width,'a',record.checks);
    await statusClick(page,'stale','SERVER_STALE_DENIED',record.checks);
    await screenshot(page,label,'04-a-new-session-old-consent-denied',record);

    await statusClick(page,'grant','CONSENT_SAVED',record.checks);
    await statusClick(page,'check','READY_YES',record.checks);
    await choose(page,'fixture:doctor:two','fixture:preview:doctor-one',0,'CAL12-DRAFT-2026-11-10.1');
    await statusClick(page,'check','READY_NO',record.checks);
    await choose(page,'fixture:doctor:two','fixture:preview:doctor-two',0,'CAL12-DRAFT-2026-11-10.1');
    await statusClick(page,'check','READY_NO',record.checks);
    await choose(page,'fixture:doctor:one','fixture:preview:doctor-one',0,'CAL12-DRAFT-OLD');
    await statusClick(page,'check','READY_NO',record.checks);
    await choose(page,'fixture:doctor:one','fixture:preview:doctor-one',0,'CAL12-DRAFT-2026-11-10.1');
    await statusClick(page,'check','READY_YES',record.checks);

    await statusClick(page,'revoke','REVOKED',record.checks);
    await statusClick(page,'check','READY_NO',record.checks);
    await screenshot(page,label,'05-withdrawn-denied',record);
    await statusClick(page,'grant','CONSENT_SAVED',record.checks);
    await statusClick(page,'check','READY_YES',record.checks);
    await page.getByTestId('offset').selectOption('20');
    await statusClick(page,'check','READY_NO',record.checks);
    await screenshot(page,label,'06-expired-simulated-denied',record);
    // The simulated +20 minute clock is only a test fixture. No actual
    // passage of twenty minutes or real retention/purge is claimed.
    assert.deepEqual(external,[], 'Unexpected external egress');
    assert((record.http['/api/v1/auth/login #200']||0)>=3);
    assert((record.http['/api/v1/auth/logout #200']||0)>=2);
    assert((record.http['/api/v1/auth/session/verify #200']||0)>=3);
    assert((record.http['/api/v1/auth/session/verify #401']||0)>=2);
    assert((record.http['/_cal12_fixture/check #200']||0)>=9);
    record.result='PASS';
  }catch(err){
    record.result='FAIL';
    const message=String(err.message||err).slice(0,500);
    proof.errors.push({case:label,message});
    await screenshot(page,label,'FAIL',record).catch(()=>{});
  }finally{
    proof.cases.push(record);
    await context.close();
  }
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  try{
    for(const [locale,width,height] of matrix)await scenario(browser,locale,width,height);
    proof.status=proof.errors.length===0?'PASS_REAL_CHROME_DJANGO_FIXTURE_ONLY':'FAIL';
    proof.matrix=matrix.length;
    proof.checkCount=proof.cases.reduce((a,c)=>a+c.checks.length,0);
    fs.writeFileSync(path.join(OUT,'proof.json'),JSON.stringify(proof,null,2)+'\n');
    assert.equal(proof.status,'PASS_REAL_CHROME_DJANGO_FIXTURE_ONLY',JSON.stringify(proof.errors));
    assert.equal(proof.cases.length,6);
    assert.equal(proof.captures.length,36);
    assert(proof.cases.every(c=>c.result==='PASS'));
    console.log('CAL12_WEB_FUE_PASS cases='+proof.cases.length+
      ' checks='+proof.checkCount+' screenshots='+proof.captures.length+
      ' real_patient_export=false');
  }finally{
    await browser.close();
  }
})().catch(err=>{console.error('CAL12_WEB_FUE_FAILED '+String(err.message||err));process.exitCode=1;});
