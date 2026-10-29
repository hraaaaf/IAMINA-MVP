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

async function labelClick(page, label) {
  // Flutter Web's actual semantics nodes, not a test driver invocation.
  const byRole = page.getByRole('button', {name:label, exact:true});
  const byText = page.getByText(label, {exact:true});
  const bySemantic = page.locator('flt-semantics[aria-label="' +
    label.replaceAll('"','\\\"') + '"]');
  if (await byRole.count()) return byRole.first().click({timeout:8000});
  if (await byText.count()) return byText.first().click({timeout:8000});
  if (await bySemantic.count()) return bySemantic.first().click({timeout:8000});
  throw new Error('no user-visible control: ' + label);
}
async function typeField(page, index, value, inDialog=false) {
  // Search only the top modal for signup inputs; the underlying login form
  // remains mounted and must not receive the typed secret.
  const modal = page.getByRole('dialog');
  const fields = inDialog && await modal.count()
    ? modal.last().getByRole('textbox')
    : page.getByRole('textbox');
  if (await fields.count() > index) {
    await fields.nth(index).click({timeout:8000});
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.insertText(value);
    return;
  }
  const semantics = page.locator('flt-semantics[role="textField"], flt-semantics[role="textbox"]');
  if (await semantics.count() > index) {
    await semantics.nth(index).click({timeout:8000});
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.insertText(value);
    return;
  }
  throw new Error('missing user-visible text field ' + index);
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
    await labelClick(page,locale==='fr'?'Se connecter':'الدخول');
    await page.waitForTimeout(750);
    if(!responses.some(x=>x.path.endsWith('/auth/login')&&x.status===401))
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
    await labelClick(page,locale==='fr'?'Envoyer':'إرسال');
    await page.waitForTimeout(750);
    if(!responses.some(x=>x.path.endsWith('/password/reset/request')&&x.status===200))
      throw new Error('native password recovery POST 200 missing');

    stage.value='positive_signup';
    await labelClick(page,locale==='fr'?'Créer un compte':'إنشاء حساب');
    await screenshot(page,'04-signup-dialog');
    const modal = page.getByRole('dialog');
    const f = await modal.count() ? modal.last().getByRole('textbox') : page.getByRole('textbox');
    if(await f.count()<3)throw new Error('signup fields missing');
    await typeField(page,0,testEmail,true);
    await typeField(page,1,password,true);
    await typeField(page,2,password,true);
    await labelClick(page,locale==='fr'?'Créer':'إنشاء');
    await page.waitForTimeout(750);
    if(!responses.some(x=>x.path.endsWith('/auth/register')&&x.status===200))
      throw new Error('native Django account registration HTTP 200 missing');
    await screenshot(page,'05-signup-success');

    stage.value='onboarding';
    await labelClick(page,'D11_UI_CONTINUE');
    await screenshot(page,'06-dashboard');

    stage.value='logout_pointer';
    if(width>=700){
      await labelClick(page,locale==='fr'?'Déconnexion':'تسجيل الخروج');
    }else{
      await labelClick(page,locale==='fr'?'Profil':'الملف الشخصي');
      await labelClick(page,locale==='fr'?'Confidentialité & compte':'الخصوصية والحساب');
      await labelClick(page,locale==='fr'?'Se déconnecter':'تسجيل الخروج');
      await labelClick(page,locale==='fr'?'Déconnecter':'خروج');
    }
    await page.waitForTimeout(750);
    if(!responses.some(x=>x.path.endsWith('/auth/logout')&&x.status===200))
      throw new Error('real navigation logout did not revoke native token');
    await screenshot(page,'07-logged-out');

    stage.value='sign_in_existing_account';
    await labelClick(page,locale==='fr'?'Se connecter ou créer un compte':'تسجيل الدخول أو إنشاء حساب');
    await typeField(page,0,testEmail);
    await typeField(page,1,password);
    await labelClick(page,locale==='fr'?'Se connecter':'الدخول');
    await page.waitForTimeout(750);
    if(!responses.some(x=>x.path.endsWith('/auth/login')&&x.status===200))
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
