/* D11 real-user Flutter Web FUE against disposable native Django/PG16.
 * Real pointer + keyboard through production LoginScreen/MainShell/Profile.
 * The browser never calls AuthService or route handlers directly.
 * No real accounts, clinical demo data or external egress.
 */
'use strict';
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const origin = 'http://127.0.0.1:7383';
const api = 'http://127.0.0.1:8000';
const locale = process.env.D11_CI_LOCALE;
const password = process.env.D11_CI_PASS;
if (!['fr', 'ar'].includes(locale) || !password || password.length < 30)
  throw new Error('D11 local fixture configuration missing');
const dir = 'd11-real-ui-web-proof';
fs.mkdirSync(dir, {recursive:true});
const report = {scope:'real Flutter routed user clicks + native Django/PG16',
  locale, production_deployment:'NOT_RUN', patient_data:'synthetic', tests:[], failed:[]};

function norm(s) { return (s||'').replace(/\s+/g,' ').trim(); }
function labelMatches(got, expected) {
  const g=norm(got), e=norm(expected);
  return g===e || g===e+' '+e;
}
async function labelClick(page, label) {
  // Flutter CanvasKit renders visible, real clickable flt-semantics nodes.
  // Prefer the accessible button; retry after route/frame settlement, and
  // fall back to the innermost exact accessible semantics element.
  const exact=page.getByRole('button',{name:label,exact:true});
  const text=page.getByText(label,{exact:true});
  for (let n=0;n<18;n++) {
    if(await exact.count()){await exact.last().click({timeout:3500});return;}
    if(await text.count()){await text.last().click({timeout:3500});return;}
    const nodes=page.locator('flt-semantics');
    for(let i=(await nodes.count())-1;i>=0;i--){
      const el=nodes.nth(i);
      const a=await el.getAttribute('aria-label').catch(()=>null);
      const t=a||await el.textContent().catch(()=>null);
      if(!labelMatches(t,label))continue;
      if(!await el.isVisible().catch(()=>false))continue;
      // Real mouse hit-test, not a JS onTap invocation or forced click.
      await el.click({timeout:3500});
      return;
    }
    await page.waitForTimeout(200);
  }
  throw new Error('no visible accessible control: '+label);
}
async function typeField(page, index, value, inDialog=false) {
  // Flutter Web may keep two login text fields behind AlertDialog even when
  // the dialog itself has no DOM role. Select the LAST three visible input
  // controls for signup, not the underlying login's first two.
  const fields=page.getByRole('textbox');
  const count=await fields.count();
  const actual=inDialog ? count-3+index : index;
  if(count<=actual||actual<0)
    throw new Error('missing form field: '+index+' total '+count);
  const field=fields.nth(actual);
  await field.click({timeout:8000});
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.insertText(value);
}
async function awaitAuthResponse(page, path, click) {
  // A missing UI control must fail the stage and retain its screenshot/report,
  // not crash Node with an unhandled, later-rejected response waiter.
  const responsePromise=page.waitForResponse(r=>
    r.url().startsWith(api) && new URL(r.url()).pathname===path,
    {timeout:12000}).catch(e=>({waitError:String(e.message||e)}));
  await click();
  const response=await responsePromise;
  if(response.waitError)throw new Error('HTTP response not observed: '+path);
  return response;
}
async function screenshot(page, suffix) {
  const filename = locale+'-'+page.viewportSize().width+'-'+suffix+'.png';
  await page.screenshot({path:path.join(dir,filename),animations:'disabled'});
  return filename;
}
async function proof(page, width) {
  const external = [], errors = [], responses = [], requests = [];
  page.on('pageerror',e=>errors.push(e.message.slice(0,160)));
  page.on('console',m=>{if (m.type()==='error') errors.push('browser-console-error');});
  page.on('response',r=>{
    if (r.url().startsWith(api+'/api/v1/auth/'))
      responses.push({path:new URL(r.url()).pathname,status:r.status()});
  });
  page.on('request',r=>{
    if (r.url().includes('/api/v1/demo/seed')) requests.push('forbidden_demo_seed');
  });
  await page.route('**/*',route=>{
    const u=route.request().url();
    if(u.startsWith(origin)||u.startsWith(api)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
    external.push('blocked_external');return route.abort();
  });

  const stage={value:'page_ready'};
  const testEmail='d11-ui-'+locale+'-'+width+'@example.invalid';
  try {
    await page.goto(origin+'/?locale='+locale,{waitUntil:'load',timeout:60000});
    await page.waitForFunction(()=>document.title==='IAMINA_D11_UI_READY' ||
      document.title.startsWith('IAMINA_D11_UI_FAIL:'),{timeout:40000});
    if(await page.title()!=='IAMINA_D11_UI_READY')
      throw new Error('Flutter user-flow bootstrap failed');
    await screenshot(page,'01-entry');

    stage.value='choose_account';
    await labelClick(page, locale==='fr'?'Se connecter ou créer un compte':'تسجيل الدخول أو إنشاء حساب');
    await screenshot(page,'02-login');

    // First reject an invalid login through the production form.
    stage.value='negative_login';
    await typeField(page,0,testEmail);
    await typeField(page,1,'Wrong-2026!');
    const loginReject = await awaitAuthResponse(page,'/api/v1/auth/login',
      () => labelClick(page,locale==='fr'?'Se connecter':'الدخول'));
    if(loginReject.status()!==401)
      throw new Error('negative login must generate native HTTP 401');

    // Then invoke the actual recovery control; the backend is disposable.
    stage.value='password_recovery';
    await labelClick(page,locale==='fr'?'Mot de passe oublié ?':'نسيت كلمة المرور؟');
    await screenshot(page,'03-reset-dialog');
    // The dialog's text field is the last available textbox.
    const textboxes = page.getByRole('textbox');
    const n = await textboxes.count();
    if(n===0)throw new Error('password recovery dialog missing text field');
    await textboxes.last().click({timeout:8000});
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.insertText(testEmail);
    const reset = await awaitAuthResponse(page,'/api/v1/auth/password/reset/request',
      () => labelClick(page,locale==='fr'?'Envoyer':'إرسال'));
    if(reset.status()!==200)
      throw new Error('native password recovery POST 200 missing');

    stage.value='positive_signup';
    await labelClick(page,locale==='fr'?'Créer un compte':'إنشاء حساب');
    await screenshot(page,'04-signup-dialog');
    const f = page.getByRole('textbox');
    if(await f.count()<3)throw new Error('signup fields missing');
    await typeField(page,0,testEmail,true);
    await typeField(page,1,password,true);
    await typeField(page,2,password,true);
    const register = await awaitAuthResponse(page,'/api/v1/auth/register',
      () => labelClick(page,locale==='fr'?'Créer':'إنشاء'));
    if(register.status()!==200)
      throw new Error('native Django account registration HTTP 200 missing');
    await page.getByText('D11_UI_NATIVE_SIGNUP_DONE',{exact:true})
      .waitFor({state:'visible',timeout:12000});
    await screenshot(page,'05-signup-success');

    stage.value='onboarding';
    await labelClick(page,'D11_UI_CONTINUE');
    await screenshot(page,'06-dashboard');

    stage.value='logout_pointer';
    const logoutPromise=page.waitForResponse(r=>
      r.url().startsWith(api) && new URL(r.url()).pathname==='/api/v1/auth/logout',
      {timeout:12000}).catch(e=>({waitError:String(e.message||e)}));
    if(width>=700){
      await labelClick(page,locale==='fr'?'Déconnexion':'تسجيل الخروج');
    }else{
      await labelClick(page,locale==='fr'?'Profil':'الملف الشخصي');
      await labelClick(page,locale==='fr'?'Confidentialité & compte':'الخصوصية والحساب');
      await labelClick(page,locale==='fr'?'Se déconnecter':'تسجيل الخروج');
      await labelClick(page,locale==='fr'?'Déconnecter':'خروج');
    }
    const revoke=await logoutPromise;
    if(revoke.waitError)throw new Error('native logout HTTP response absent');
    if(revoke.status()!==200)
      throw new Error('real navigation logout did not revoke native token');
    await screenshot(page,'07-logged-out');

    stage.value='sign_in_existing_account';
    await labelClick(page,locale==='fr'?'Se connecter ou créer un compte':'تسجيل الدخول أو إنشاء حساب');
    await typeField(page,0,testEmail);
    await typeField(page,1,password);
    const loginAccept=await awaitAuthResponse(page,'/api/v1/auth/login',
      () => labelClick(page,locale==='fr'?'Se connecter':'الدخول'));
    if(loginAccept.status()!==200)
      throw new Error('native login HTTP 200 missing after logout');
    const filename=await screenshot(page,'08-returned');
    if(errors.length||external.length||requests.length)
      throw new Error('UI page error, blocked external egress, or forbidden demo seed request');
    return {locale,width,pass:true,requests:responses,errors:errors.length,
      blockedExternal:external.length,clinicalDemoRequests:requests.length,file:filename};
  } catch(e) {
    const filename=await screenshot(page,'failure').catch(()=>null);
    const labels=await page.locator('flt-semantics').evaluateAll(nodes=>
      nodes.slice(0,80).map(n=>(n.getAttribute('aria-label')||n.textContent||'').slice(0,90))
        .filter(Boolean)).catch(()=>[]);
    return {locale,width,pass:false,stage:stage.value,error:String(e.message||e).slice(0,250),
      visibleSemanticLabels:labels.slice(0,35),requests:responses,errors:errors.length,
      blockedExternal:external.length,clinicalDemoRequests:requests.length,file:filename};
  }
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const viewport of [{width:390,height:844},{width:768,height:1024},{width:1280,height:900}]){
    const context=await browser.newContext({viewport,locale:locale==='fr'?'fr-FR':'ar-MA',serviceWorkers:'block'});
    const page=await context.newPage();
    const result=await proof(page,viewport.width);
    report.tests.push(result);
    if(!result.pass)report.failed.push(result);
    await context.close();
  }
 } finally{await browser.close();}
 fs.writeFileSync(path.join(dir,'report.json'),JSON.stringify(report,null,2));
 console.log('D11_REAL_ROUTED_UI='+JSON.stringify({locale,passed:report.tests.length-report.failed.length,
    total:report.tests.length,failed:report.failed.map(x=>({width:x.width,stage:x.stage,error:x.error,
    visibleSemanticLabels:x.visibleSemanticLabels,requests:x.requests}))}));
 if(report.failed.length||report.tests.length!==3)process.exitCode=1;
})().catch(e=>{console.error('D11 UI FUE runner failed: '+e.constructor.name);process.exitCode=1;});
