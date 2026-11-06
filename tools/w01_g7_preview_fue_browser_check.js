/* W01/G7: actual Flutter Web pointer/keyboard FUE against disposable PG16.
 * Never uses real accounts, Production, Neon, direct Flutter callbacks, or UI mocks.
 * Synthetic tokens stay in process memory; reports contain only status/counts.
 */
'use strict';
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const WEB = 'http://127.0.0.1:7383';
const API = 'http://127.0.0.1:8000';
const locale = process.env.G7_FUE_LOCALE;
const password = process.env.G7_FUE_PASSWORD;
if (!['fr', 'ar'].includes(locale) || !password || password.length < 30)
  throw Error('Invalid isolated W01/G7 FUE fixture');
const output = path.resolve('w01-g7-fue-proof');
const fixtures = JSON.parse(fs.readFileSync(path.join(output, 'fixtures.json'), 'utf8'));
assert.equal(fixtures.synthetic, true);
assert.equal(fixtures.patients.length, 2);
const [patientA, patientB] = fixtures.patients;
const report = {
  goal:'W01/G7 synthetic Web FUE', locale,
  branch:'PR-only / ephemeral PG16', production:'NOT_RUN',
  no_real_patients:true, tests:[], failures:[]
};
function norm(s) { return (s||'').replace(/\s+/g,' ').trim(); }
async function clickLabel(page,label) {
  const role=page.getByRole('button',{name:label,exact:true});
  const text=page.getByText(label,{exact:true});
  for(let attempt=0;attempt<20;attempt++){
    if(await role.count()){await role.last().click({timeout:4000});return;}
    if(await text.count()){await text.last().click({timeout:4000});return;}
    const nodes=page.locator('flt-semantics');
    for(let i=(await nodes.count())-1;i>=0;i--){
      const el=nodes.nth(i);
      const labelText=(await el.getAttribute('aria-label').catch(()=>null)) ||
        (await el.textContent().catch(()=>null));
      if(norm(labelText)!==norm(label)) continue;
      if(!await el.isVisible().catch(()=>false)) continue;
      await el.click({timeout:4000});return;
    }
    await page.waitForTimeout(180);
  }
  throw Error('Missing real visible control: '+label);
}
async function inputByLabel(page,label,value,fallbackY){
  const matches=page.getByText(label,{exact:true});
  const boxes=[];
  for(let i=0;i<await matches.count();i++){
    const box=await matches.nth(i).boundingBox().catch(()=>null);
    if(box&&box.width>0&&box.height>0)boxes.push(box);
  }
  if(!boxes.length){
    const nodes=page.locator('flt-semantics');
    for(let i=0;i<await nodes.count();i++){
      const el=nodes.nth(i);
      if(norm(await el.getAttribute('aria-label').catch(()=>''))!==label)continue;
      const box=await el.boundingBox().catch(()=>null);
      if(box&&box.width>0&&box.height>0)boxes.push(box);
    }
  }
  const box=boxes.sort((a,b)=>b.y-a.y)[0]||null;
  const targetY=box?box.y+box.height+22:fallbackY;
  assert(targetY>0 && targetY<page.viewportSize().height,'Input outside viewport');
  await page.mouse.click(page.viewportSize().width/2,targetY);
  const editor=page.locator('input:focus,textarea:focus').first();
  await editor.waitFor({state:'attached',timeout:4500});
  await page.waitForTimeout(80);
  await page.keyboard.press('ControlOrMeta+A');
  const selected=await editor.evaluate(e=>({
    start:e.selectionStart,end:e.selectionEnd,length:e.value.length
  }));
  assert.equal(selected.start,0,'Text selection start');
  assert.equal(selected.end,selected.length,'Text selection end');
  await page.keyboard.type(value,{delay:20});
  await page.waitForTimeout(100);
  const identical=await editor.evaluate((e,expected)=>e.value===expected,value);
  await page.keyboard.press('Tab');
  assert.equal(identical,true,'User keyboard input must match intended value');
}
async function authResponse(page,endpoint,action){
  const responsePromise=page.waitForResponse(r=>
    r.url().startsWith(API) && new URL(r.url()).pathname===endpoint,
    {timeout:16000}).catch(()=>null);
  await action();
  const response=await responsePromise;
  assert(response!==null,'Real API HTTP response absent: '+endpoint);
  return response;
}
async function screenshot(page,width,name,record){
  const filename=locale+'-'+width+'-'+name+'.png';
  await page.screenshot({path:path.join(output,filename),animations:'disabled'});
  record.captures.push(filename);
}
async function apiCheck(token,method,endpoint,status,body){
  const headers={'Authorization':'Bearer '+token};
  if(body!==undefined)headers['Content-Type']='application/json';
  const response=await fetch(API+endpoint,{
    method,headers,body:body!==undefined?JSON.stringify(body):undefined,
    redirect:'manual'
  });
  assert.equal(response.status,status,method+' '+endpoint+' must return '+status);
  if(status===200)return response.json();
  return null;
}
async function assertOwnLogs(token,mine){
  const payload=await apiCheck(token,'GET','/api/v1/logs',200);
  assert.equal(payload.total,1,'Patient sees exactly their own log');
  assert.equal(payload.items.length,1,'Patient owns one log');
  assert.equal(payload.items[0].id,mine.log_id,'Cross-patient log ID leaked');
  assert.equal(payload.items[0].blood_sugar,mine.blood_sugar,'Incorrect patient value');
}
async function testPreviewNegatives(){
  const anon=await fetch(API+'/api/v1/logs',{redirect:'manual'});
  assert([401,403].includes(anon.status),'Anonymous logs must not be accessible');
  const denied=await fetch(API+'/api/v1/auth/register',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      email:'g7-forbidden@example.invalid',
      password:'Synthetic-Strong-Password-2026-For-G7!',
      first_name:'No',last_name:'Create'
    }),redirect:'manual'
  });
  assert.equal(denied.status,403,'Preview must block direct registration');
}
async function enterLogin(page,width,record,stage){
  const chooser=locale==='fr'
    ?'Se connecter avec un compte existant':'تسجيل الدخول بحساب موجود';
  await clickLabel(page,chooser);
  if(await page.getByText(locale==='fr'?'Créer un compte':'إنشاء حساب',{exact:true}).count())
    throw Error('Preview signup action is visible');
  if(await page.getByText(locale==='fr'?'Mot de passe oublié ?':'نسيت كلمة المرور؟',{exact:true}).count())
    throw Error('Preview reset action is visible');
  if(await page.getByText(locale==='fr'?'Accès démo':'الوصول التجريبي',{exact:true}).count())
    throw Error('Preview demo action is visible');
  await screenshot(page,width,stage+'-preview-login-only',record);
}
async function login(page,row){
  const emailLabel=locale==='fr'?'Adresse e-mail':'البريد الإلكتروني';
  const passwordLabel=locale==='fr'?'Mot de passe':'كلمة المرور';
  await inputByLabel(page,emailLabel,row.email,locale==='fr'?449:336);
  await inputByLabel(page,passwordLabel,password,locale==='fr'?523:427);
  const res=await authResponse(page,'/api/v1/auth/login',()=>
    clickLabel(page,locale==='fr'?'Se connecter':'الدخول'));
  assert.equal(res.status(),200,'Real Web login must reach native Django 200');
  const payload=await res.json();
  assert.equal(payload.user.id,row.user_id,'Web login must bind correct patient');
  assert(typeof payload.access_token==='string'&&payload.access_token.startsWith('iamina.'),
    'Server did not provide signed native bearer');
  await page.getByText('W01_G7_UI_VERIFIED_ACCOUNT_NO_DEMO_ROWS',{exact:true})
    .waitFor({state:'visible',timeout:14000});
  return payload.access_token;
}
async function logoutByUI(page,width){
  if(width>=700){
    const label=locale==='fr'?'Déconnexion':'تسجيل الخروج';
    const node=page.getByRole('button',{name:label,exact:true});
    if(await node.count())return node.last().click({timeout:8000});
    // Same pointer fallback as previously verified D11 real-Web FUE.
    await page.mouse.click(locale==='ar'?width-65:65,width>=1100?354:300);
    return;
  }
  // Real 390x844 screenshots show Profile in the bottom nav even when
  // CanvasKit omits its semantics node. Use a real physical pointer fallback,
  // never an invoked Flutter callback or direct route navigation.
  const profileLabel=locale==='fr'?'Profil':'الملف الشخصي';
  const profileSection=locale==='fr'?'Confidentialité & compte':'الخصوصية والحساب';
  const navButton=page.getByRole('button',{name:profileLabel,exact:true});
  if(await navButton.count() && await navButton.last().isVisible()){
    await navButton.last().click({timeout:5000});
  }else{
    // MainShell._BottomNav: 18px side margins, 4 equal items.
    // Profile is at slot 3 (FR) or slot 0 (AR/RTL).
    const margin=18,slot=(width-2*margin)/4,index=locale==='ar'?0:3;
    await page.mouse.click(margin+(index+0.5)*slot,page.viewportSize().height-36);
  }
  // The FR/AR failure screenshots at 390x844 prove the Profile screen
  // DID open. Flutter CanvasKit paints its headings without a matching
  // getByText() DOM node. Assert the router URL, then interact with the
  // exact, visible account accordion via a real pointer (never GoRouter).
  await page.waitForFunction(()=>
    location.pathname.endsWith('/profile') ||
    location.hash.includes('/profile'),null,{timeout:12000});
  const beforeAccount=await page.screenshot({animations:'disabled'});
  // Screenshot-grounded account card center: FR y~695, Arabic y~670.
  await page.mouse.click(width/2,locale==='ar'?670:695);
  await page.waitForTimeout(500);
  const afterAccount=await page.screenshot({animations:'disabled'});
  assert(!beforeAccount.equals(afterAccount),
    'Account accordion must visually respond to real pointer input');
  const label=locale==='fr'?'Se déconnecter':'تسجيل الخروج';
  const nodes=page.locator('flt-semantics');
  let visible=false;
  const h=page.viewportSize().height;
  for(let step=0;step<8&&!visible;step++){
    await page.mouse.move(width/2,Math.min(500,h-150));
    await page.mouse.wheel(0,440);
    await page.waitForTimeout(200);
    for(let i=(await nodes.count())-1;i>=0;i--){
      const el=nodes.nth(i);
      const value=(await el.getAttribute('aria-label').catch(()=>null))||
        (await el.textContent().catch(()=>null));
      if(norm(value)!==norm(label))continue;
      const box=await el.boundingBox().catch(()=>null);
      if(box&&box.width>0&&box.height>0&&box.y>=0&&box.y+box.height<=h-62){
        visible=true;break;
      }
    }
  }
  assert(visible,'Logout must be visibly reachable by real scrolling');
  await clickLabel(page,label);
  await clickLabel(page,locale==='fr'?'Déconnecter':'خروج');
}
async function logoutAndRevoke(page,width,token){
  const res=await authResponse(page,'/api/v1/auth/logout',()=>
    logoutByUI(page,width));
  assert.equal(res.status(),200,'Real logout HTTP 200 absent');
  await apiCheck(token,'GET','/api/v1/logs',401);
}
async function runViewport(browser,viewport){
  const width=viewport.width;
  const context=await browser.newContext({
    viewport,locale:locale==='fr'?'fr-FR':'ar-MA',serviceWorkers:'block'
  });
  const page=await context.newPage();
  const record={width,height:viewport.height,result:'FAIL',captured:false,captures:[],checks:[]};
  const forbiddenHosts=[],pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(e.name||'unknown'));
  await page.route('**/*',route=>{
    const url=route.request().url();
    if(url.startsWith(WEB)||url.startsWith(API)||url.startsWith('data:')||url.startsWith('blob:'))
      return route.continue();
    let host='unknown';try{host=new URL(url).hostname;}catch(_){}
    forbiddenHosts.push(host);
    return route.abort();
  });
  try{
    await page.goto(WEB+'/?locale='+locale,{waitUntil:'load',timeout:60000});
    await page.waitForFunction(()=>
      document.title==='W01_G7_UI_READY'||
      document.title.startsWith('W01_G7_UI_FAIL:'),{timeout:40000});
    assert.equal(await page.title(),'W01_G7_UI_READY','Real Flutter entrypoint');
    await screenshot(page,width,'01-local-choice',record);
    await enterLogin(page,width,record,'02');
    await testPreviewNegatives();
    record.checks.push('anonymous-denied','registration-403','preview-actions-hidden');
    let tokenA=await login(page,patientA);
    await assertOwnLogs(tokenA,patientA);
    await screenshot(page,width,'03-signed-in-a',record);
    record.checks.push('real-login-a','a-sees-only-a');
    await logoutAndRevoke(page,width,tokenA);
    await screenshot(page,width,'04-a-logout',record);
    record.checks.push('a-token-revoked');
    await enterLogin(page,width,record,'04b');
    let tokenB=await login(page,patientB);
    await assertOwnLogs(tokenB,patientB);
    for(const method of ['GET','PATCH','DELETE']){
      await apiCheck(tokenB,method,'/api/v1/logs/'+patientA.log_id,404,
        method==='PATCH'?{blood_sugar:450}:undefined);
    }
    await screenshot(page,width,'05-signed-in-b',record);
    record.checks.push('real-login-b','b-sees-only-b','idor-get-patch-delete-404');
    await logoutAndRevoke(page,width,tokenB);
    await screenshot(page,width,'06-b-logout',record);
    record.checks.push('b-token-revoked');
    await enterLogin(page,width,record,'06b');
    const newA=await login(page,patientA);
    await assertOwnLogs(newA,patientA);
    await apiCheck(newA,'GET','/api/v1/logs/'+patientB.log_id,404);
    await apiCheck(tokenA,'GET','/api/v1/logs',401);
    await apiCheck(tokenB,'GET','/api/v1/logs',401);
    await screenshot(page,width,'07-a-returned',record);
    record.checks.push('real-relogin-a','a-cannot-read-b','old-tokens-still-revoked');
    assert.equal(forbiddenHosts.length,0,'External browser egress detected');
    assert.equal(pageErrors.length,0,'Uncaught browser errors detected');
    assert.equal(record.captures.length,9,'Nine real UI screenshots required');
    assert.equal(new Set(record.captures).size,9,'Every screenshot must have a unique file');
    record.result='PASS';
    record.captured=true;
  }catch(e){
    record.error=String(e.message||e).slice(0,200);
    await screenshot(page,width,'failure',record).catch(()=>{});
  }finally{
    record.external_request_count=forbiddenHosts.length;
    record.browser_error_count=pageErrors.length;
    await context.close();
  }
  return record;
}
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
      const r=await runViewport(browser,viewport);
      report.tests.push(r);
      if(r.result!=='PASS')report.failures.push({
        width:r.width,failed_checks:r.checks,error:r.error||'unknown'
      });
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(output,'report-'+locale+'.json'),
    JSON.stringify(report,null,2)+'\n');
  console.log('W01_G7_FUE_VERDICT='+JSON.stringify({
    locale,passed:report.tests.filter(x=>x.result==='PASS').length,
    total:report.tests.length,failed:report.failures
  }));
  if(report.failures.length||report.tests.length!==2)process.exitCode=1;
})().catch(e=>{
  console.error('W01_G7_FUE_SETUP_FAILURE='+String(e.name||'Error'));
  process.exitCode=1;
});
