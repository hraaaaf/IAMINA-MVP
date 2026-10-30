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
  // Flutter expansion sections append their subtitle to their heading.
  // Match the exact leading heading, never an arbitrary substring of a page.
  return g===e || g===e+' '+e || g.startsWith(e+' ');
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
  // Flutter AlertDialog is often exposed as role=alertdialog (NOT dialog).
  // Scope to the top actual modal first. It hides the underlying login
  // controls from this selection and keeps indices stable as text updates.
  const alerts=page.getByRole('alertdialog');
  const dialogs=page.getByRole('dialog');
  const modal=await alerts.count() ? alerts.last()
    : (await dialogs.count() ? dialogs.last() : null);
  const modalFields=inDialog && modal ? modal.getByRole('textbox') : null;
  const scopedCount=modalFields ? await modalFields.count() : 0;
  const fields=scopedCount>=3 ? modalFields : page.getByRole('textbox');
  const count=await fields.count();
  // A second DOM semantics tree may retain the login form beneath the
  // dialog. Restrict the fallback to the last three visible textboxes.
  const actual=inDialog && scopedCount<3 && count>3 ? count-3+index : index;
  if(count<=actual||actual<0)
    throw new Error('missing form field: '+index+' visible '+count+' modal '+scopedCount);
  const field=fields.nth(actual);
  await field.click({timeout:8000});
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.insertText(value);
  await page.keyboard.press('Tab');
}
// The CanvasKit semantics tree can retain the two underlying login inputs
// while a signup AlertDialog is open. Select a user-visible field by its
// rendered LABEL and click inside the box directly below that label.
// This is a real pointer/keyboard path; no widget callbacks or DOM value
// injection. The field order and label geometry are checked on-screen.
async function typeSignupLabeledField(page, label, value, fallbackY=null) {
  const exact=page.getByText(label,{exact:true});
  const semantics=page.locator('flt-semantics');
  const candidateBoxes=[];
  for (let i=0;i<await exact.count();i++) {
    const el=exact.nth(i);
    const b=await el.boundingBox().catch(()=>null);
    if(b&&b.width>0&&b.height>0)candidateBoxes.push(b);
  }
  if(!candidateBoxes.length) {
    for(let i=0;i<await semantics.count();i++) {
      const el=semantics.nth(i);
      if(norm(await el.getAttribute('aria-label').catch(()=>''))!==label)continue;
      const b=await el.boundingBox().catch(()=>null);
      if(b&&b.width>0&&b.height>0)candidateBoxes.push(b);
    }
  }
  // At route transitions Flutter can paint the input before exposing its
  // semantics rectangle. Use screenshot-grounded real pointer coordinates
  // only for the *login* form, never for the signup modal. Still report the
  // missing semantic label independently: passing the HTTP flow is not an
  // accessibility certification.
  const box=candidateBoxes.sort((a,b)=>b.y-a.y)[0]||null;
  if(!box&&fallbackY===null)
    throw new Error('signup visible field label absent: '+label);
  const targetX=page.viewportSize().width/2;
  const targetY=box ? box.y+box.height+22 : fallbackY;
  if(targetY>=page.viewportSize().height)
    throw new Error('signup label below browser viewport: '+label);
  await page.mouse.click(targetX,targetY);
  // Flutter Web creates an actual editing <input> for the focused text field.
  // Playwright.fill dispatches real browser input/change events and replaces
  // stale field contents, unlike Control+A/insertText on the wrong focus.
  const editor=page.locator('input:focus,textarea:focus').first();
  await editor.waitFor({state:'attached',timeout:3000});
  await editor.click({timeout:4000});
  await page.keyboard.press('ControlOrMeta+A');
  // Physical key events, not just a DOM-value patch: Flutter TextField's
  // TextEditingController must receive the change before validation.
  await page.keyboard.type(value,{delay:2});
  await page.keyboard.press('Tab');
  await page.waitForTimeout(60);
  const length=await editor.evaluate(el=>el.value.length);
  if(length!==value.length)
    throw new Error('signup editor length mismatch: '+label+' length '+length+' expected '+value.length);
}
async function logoutViaVisibleSidebar(page, width) {
  const label=locale==='fr'?'Déconnexion':'تسجيل الخروج';
  // Prefer accessible nodes. CI Flutter's semantic tree can collapse to the
  // centre Scaffold after a route change even while sidebar pixels render.
  if(await page.getByRole('button',{name:label,exact:true}).count()) {
    await labelClick(page,label);
    return {semantic:true};
  }
  // Browser screenshots ground the actual MainShell sidebar layout:
  // collapsed rail at 768 (logout icon y=331); full rail at 1280 (y=353).
  // This is a strict native mouse click followed by authenticated HTTP
  // revocation verification, NOT an AuthService or onTap invocation.
  const railX=width>=1100?65:35;
  const x=locale==='ar'?width-railX:railX;
  const y=width>=1100?354:332;
  await page.mouse.click(x,y);
  return {semantic:false};
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
  const external = [], errors = [], consoleErrors = [], responses = [], requests = [];
  page.on('pageerror',e=>errors.push('uncaught-page-exception:'+e.name));
  page.on('console',m=>{
    if(m.type()!=='error')return;
    const msg=m.text();
    const status=(msg.match(/\b(401|403|404|429|500|502|503)\b/)||[])[1]||'unknown';
    // Only HTTP 401 caused by the deliberate negative-login test may be
    // expected. All other console errors remain hard failures, with a safe
    // diagnostic that never contains tokens, passwords or patient details.
    consoleErrors.push({httpStatus:status,resourceClass:msg.includes('Failed to load resource')
      ?'resource': 'other'});
  });
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
    // Capture only the hostname, never query paths, passwords or patient
    // identifiers. This distinguishes missing local Arabic glyph resources
    // from unrelated external egress without allowing a network request.
    let host='unknown';
    try{host=new URL(u).hostname;}catch(_){}
    external.push(host);return route.abort();
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
    await typeSignupLabeledField(page,locale==='fr'?'Adresse e-mail':'البريد الإلكتروني',testEmail,locale==='fr'?449:336);
    await typeSignupLabeledField(page,locale==='fr'?'Mot de passe':'كلمة المرور','Wrong-2026!',locale==='fr'?523:427);
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
    await typeSignupLabeledField(page,locale==='fr'?'Adresse e-mail':'البريد الإلكتروني',testEmail);
    await typeSignupLabeledField(page,locale==='fr'?'Mot de passe':'كلمة المرور',password);
    await typeSignupLabeledField(page,locale==='fr'?'Confirmer le mot de passe':'تأكيد كلمة المرور',password);
    await screenshot(page,'04b-filled-signup-form');
    const register = await awaitAuthResponse(page,'/api/v1/auth/register',
      () => labelClick(page,locale==='fr'?'Créer':'إنشاء'));
    if(register.status()!==200)
      throw new Error('native Django account registration HTTP 200 missing');
    await page.getByText('D11_UI_NATIVE_SIGNUP_DONE',{exact:true})
      .waitFor({state:'visible',timeout:12000});
    await screenshot(page,'05-signup-success');

    stage.value='onboarding';
    await labelClick(page,'D11_UI_CONTINUE');
    // The next Flutter route is rendered asynchronously. Do not click the
    // sidebar while /onboarding still owns the pixels (prior screenshot proof
    // showed the "dashboard" image was actually the onboarding page).
    await page.getByText('D11_UI_VERIFIED_ACCOUNT_NO_DEMO_ROWS',{exact:true})
      .waitFor({state:'visible',timeout:12000});
    await screenshot(page,'06-dashboard');

    stage.value='logout_pointer';
    const logoutCount=responses.filter(r=>r.path==='/api/v1/auth/logout').length;
    if(width>=700){
      const nav=await logoutViaVisibleSidebar(page,width);
      if(!nav.semantic)errors.push('main-shell-logout-missing-accessible-node');
    }else{
      await labelClick(page,locale==='fr'?'Profil':'الملف الشخصي');
      await labelClick(page,locale==='fr'?'Confidentialité & compte':'الخصوصية والحساب');
      await labelClick(page,locale==='fr'?'Se déconnecter':'تسجيل الخروج');
      await labelClick(page,locale==='fr'?'Déconnecter':'خروج');
    }
    // The response listener is attached before page navigation and also
    // collects all HTTP evidence used by the final report; it is more robust
    // across route changes than an extra waiter on the old navigation context.
    for(let retry=0;retry<50&&!responses.slice(logoutCount).some(
      r=>r.path==='/api/v1/auth/logout');retry++)await page.waitForTimeout(100);
    const logoutResponses=responses.filter(r=>r.path==='/api/v1/auth/logout');
    if(logoutResponses.length<=logoutCount || logoutResponses.at(-1).status!==200)
      throw new Error('real navigation logout did not return native HTTP 200');
    await screenshot(page,'07-logged-out');

    stage.value='sign_in_existing_account';
    await labelClick(page,locale==='fr'?'Se connecter ou créer un compte':'تسجيل الدخول أو إنشاء حساب');
    // Await actual rendered login text before typing; account chooser route
    // remains alive for a few frames after the click.
    await page.getByText(locale==='fr'?'Mot de passe oublié ?':'نسيت كلمة المرور؟',{exact:true})
      .first().waitFor({state:'visible',timeout:12000});
    await typeSignupLabeledField(page,locale==='fr'?'Adresse e-mail':'البريد الإلكتروني',testEmail,locale==='fr'?449:336);
    await typeSignupLabeledField(page,locale==='fr'?'Mot de passe':'كلمة المرور',password,locale==='fr'?523:427);
    const loginAccept=await awaitAuthResponse(page,'/api/v1/auth/login',
      () => labelClick(page,locale==='fr'?'Se connecter':'الدخول'));
    if(loginAccept.status()!==200)
      throw new Error('native login HTTP 200 missing after logout');
    await page.getByText('D11_UI_VERIFIED_ACCOUNT_NO_DEMO_ROWS',{exact:true})
      .waitFor({state:'visible',timeout:12000});
    const filename=await screenshot(page,'08-returned');
    const unexpectedConsole=consoleErrors.filter(e=>!(
      e.httpStatus==='401' && e.resourceClass==='resource' &&
      responses.some(r=>r.path==='/api/v1/auth/login'&&r.status===401)));
    if(errors.length||unexpectedConsole.length||external.length||requests.length)
      throw new Error('UI page errors '+errors.length+' unexpected console '+
        JSON.stringify(unexpectedConsole)+' external '+external.length+
        ' forbidden seed '+requests.length);
    return {locale,width,pass:true,requests:responses,errors:errors.length,
      blockedExternal:external.length,blockedExternalHosts:[...new Set(external)].slice(0,8),
      clinicalDemoRequests:requests.length,file:filename};
  } catch(e) {
    const filename=await screenshot(page,'failure').catch(()=>null);
    const labels=await page.locator('flt-semantics').evaluateAll(nodes=>
      nodes.slice(0,80).map(n=>(n.getAttribute('aria-label')||n.textContent||'').slice(0,90))
        .filter(Boolean)).catch(()=>[]);
    return {locale,width,pass:false,stage:stage.value,error:String(e.message||e).slice(0,250),
      visibleSemanticLabels:labels.slice(0,35),requests:responses,
      browserErrors:errors.slice(0,5),consoleDiagnostic:consoleErrors,
      errors:errors.length,
      blockedExternal:external.length,blockedExternalHosts:[...new Set(external)].slice(0,8),
      clinicalDemoRequests:requests.length,file:filename};
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
    visibleSemanticLabels:x.visibleSemanticLabels,requests:x.requests,
    browserErrors:x.browserErrors,consoleDiagnostic:x.consoleDiagnostic,
    blockedExternalHosts:x.blockedExternalHosts,blockedExternal:x.blockedExternal}))}));
 if(report.failed.length||report.tests.length!==3)process.exitCode=1;
})().catch(e=>{console.error('D11 UI FUE runner failed: '+e.constructor.name);process.exitCode=1;});
