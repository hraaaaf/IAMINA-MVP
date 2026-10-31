// IAMINA D7 FUE04: hosted real Flutter Chrome A -> logout -> B -> logout -> A.
// Clinical reads only. Secrets and patient content never leave RAM or enter proof.
import fs from 'node:fs';
import {chromium} from 'playwright';

const ORIGIN = 'https://iamina-review-git-cert-d7-we-5e65d5-achraf-benmoussa-s-projects.vercel.app';
const DEPLOY_SHA = '027f5caf189adc951182a328526163dfd6270d27';
const LOGIN = /^(?:Sign in|Se connecter|الدخول)$/;
const PICK = /^(?:Sign in or create an account|Se connecter ou créer un compte|تسجيل الدخول أو إنشاء حساب)$/;
const SIGNOUT = /^(?:Sign out|Se déconnecter|تسجيل الخروج)$/;
const CONFIRM = /^(?:Sign out|Déconnecter|خروج)$/;
const proof = {
  gate: 'D7_FUE04_HOSTED_REAL_FLUTTER_CHROME_ABA_READ_ONLY',
  deployed_app_sha: DEPLOY_SHA, workflow_ref_sha: process.env.GITHUB_SHA || null,
  result: 'NOT_RUN', stages: [], clinical_mutations: 0, profile_data_exported: false,
  account_credentials_exported: false, screenshots_after_login: 0,
  clinical_approval: 'NOT_RUN', visual_language_review: 'NOT_RUN',
};
let stage = 'INIT';
const fail = code => { throw new Error('D7_BROWSER_' + code); };
function record(name, state = 'PASS') { proof.stages.push({name, state}); }
function activateSemantics(page) {
  return page.locator('flt-semantics-placeholder').first().evaluate(el => {
    const r=el.getBoundingClientRect();
    el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,
      clientX:r.left+r.width/2,clientY:r.top+r.height/2}));
  });
}
function isLogin(page) { return page.getByRole('button',{name:PICK}).count(); }
async function enterLogin(page) {
  stage='ACCOUNT_CHOICE';
  await page.goto(ORIGIN+'/login',{waitUntil:'domcontentloaded',timeout:35000});
  await page.waitForSelector('flutter-view,flt-glass-pane',{timeout:45000});
  await activateSemantics(page);
  const pick=page.getByRole('button',{name:PICK}).first();
  await pick.waitFor({state:'visible',timeout:20000});
  await pick.click({timeout:18000});
  const input=page.locator('input:not([type="hidden"])');
  await input.first().waitFor({state:'visible',timeout:20000});
  if(await input.count()<2)fail('INPUT_FIELDS_ABSENT');
}
async function fetchJson(context,token,path) {
  const res=await context.request.get(ORIGIN+path,{headers:{
    'Authorization':'Bearer '+token,'Accept':'application/json','Origin':ORIGIN,
  },timeout:20000,failOnStatusCode:false});
  if(res.status()!==200)fail(path.includes('profile')?'PROFILE_READ_HTTP_NOT_200':'IDENTITY_READ_HTTP_NOT_200');
  const type=res.headers()['content-type']||'';
  if(!type.includes('application/json'))fail('NON_JSON_API_RESPONSE');
  return res.json();
}
async function login(page,context,email,password,round) {
  await enterLogin(page);
  const inputs=page.locator('input:not([type="hidden"])');
  const emailField=page.locator('input[type="email"],input[type="text"]').first();
  const pwd=page.locator('input[type="password"]').first();
  stage=round+'_EMAIL_FILL';
  await (await emailField.count()?emailField:inputs.first())
    .fill(email,{timeout:15000});
  stage=round+'_PASSWORD_FILL';
  await (await pwd.count()?pwd:inputs.nth(1))
    .fill(password,{timeout:15000});
  stage=round+'_SUBMIT_DISCOVERY';
  const submit=page.getByRole('button',{name:LOGIN}).last();
  await submit.waitFor({state:'visible',timeout:15000});
  stage=round+'_SUBMIT_CLICK';
  const responsePromise=page.waitForResponse(r=>
    r.url().split('?')[0]===ORIGIN+'/api/v1/auth/login' &&
    r.request().method()==='POST',{timeout:35000});
  await submit.click({timeout:20000});
  stage=round+'_LOGIN_HTTP_RESPONSE';
  const res=await responsePromise;
  if(res.status()!==200)fail(round+'_LOGIN_HTTP_NOT_200');
  const data=await res.json();
  stage=round+'_LOGIN_NAVIGATION';
  // HTTP 200 precedes secure-storage persistence and GoRouter navigation.
  await page.waitForURL(url=>{
    const u=new URL(url);
    const path=u.hash.startsWith('#/')?u.hash.slice(1):u.pathname;
    return path!=='/login';
  },{timeout:30000}).catch(()=>fail(round+'_LOGIN_NAVIGATION_TIMEOUT'));
  stage=round+'_LOGIN_CONTRACT';
  if(!Number.isSafeInteger(data?.user?.id) || data.user.id<=0 ||
    data?.user?.email?.toLowerCase()!==email.toLowerCase() ||
    data.token_type!=='Bearer' ||
    typeof data.access_token!=='string' ||
    !data.access_token.startsWith('iamina.'))
    fail(round+'_LOGIN_CONTRACT');
  record(round+'_LOGIN_200');
  stage=round+'_IDENTITY';
  const me=await fetchJson(context,data.access_token,'/api/v1/auth/me');
  if(me?.id!==data.user.id)fail(round+'_IDENTITY_OWNER_MISMATCH');
  record(round+'_ME_OWNER');
  stage=round+'_PROFILE_API';
  const profile=await fetchJson(context,data.access_token,'/api/v1/profile');
  if(typeof profile?.treatment_declaration_state!=='string')
    fail(round+'_PROFILE_CONTRACT');
  record(round+'_PROFILE_GET_200');
  stage=round+'_PROFILE_FLUTTER';
  await page.goto(ORIGIN+'/profile',{waitUntil:'domcontentloaded',timeout:35000});
  await page.waitForSelector('flutter-view,flt-glass-pane',{timeout:45000});
  await activateSemantics(page);
  const signout=page.getByRole('button',{name:SIGNOUT}).first();
  let visible=false;
  for(let tries=0;tries<12;tries++) {
    if(await signout.count()>0 && await signout.isVisible()) {visible=true;break;}
    await page.mouse.wheel(0,650);
    await page.waitForTimeout(160);
  }
  if(!visible)fail(round+'_PROFILE_OR_CONSENT_GATE');
  record(round+'_FLUTTER_PROFILE_SIGNOUT_VISIBLE');
  return {id:data.user.id,profile,signout};
}
async function logout(page,account,round) {
  stage=round+'_LOGOUT_UI';
  await account.signout.click({timeout:18000});
  const confirm=page.getByRole('button',{name:CONFIRM}).last();
  await confirm.waitFor({state:'visible',timeout:12000});
  const logoutResponse=page.waitForResponse(r=>
    r.url().split('?')[0]===ORIGIN+'/api/v1/auth/logout' &&
    r.request().method()==='POST',{timeout:20000}).catch(()=>null);
  await confirm.click({timeout:15000});
  await page.waitForURL(url=>new URL(url).pathname==='/login'||
    new URL(url).hash==='#/login',{timeout:24000});
  const response=await logoutResponse;
  if(!response || response.status()!==200)fail('NATIVE_LOGOUT_NOT_CONFIRMED');
  record('NATIVE_LOGOUT_200');
  stage='AFTER_LOGOUT';
  await page.reload({waitUntil:'domcontentloaded',timeout:35000});
  await page.waitForSelector('flutter-view,flt-glass-pane',{timeout:35000});
  await activateSemantics(page);
  await page.getByRole('button',{name:PICK}).first().waitFor({state:'visible',timeout:20000});
  record('LOGIN_GATE_AFTER_LOGOUT');
}
async function main() {
  let browser;
  try {
    if(process.env.D7_PREVIEW_SHA!==DEPLOY_SHA)fail('DEPLOY_SHA_MISMATCH');
    if(process.env.GITHUB_REF!=='refs/heads/cert/d7-web-fue-preview-20261029')
      fail('BRANCH_MISMATCH');
    for(const k of ['D7_QA_A_EMAIL','D7_QA_B_EMAIL','D7_QA_A_PASSWORD',
                     'D7_QA_B_PASSWORD','D7_QA_SSO_ACCESS']) {
      if(typeof process.env[k]!=='string'||!process.env[k])fail('QA_SECRET_ABSENT');
    }
    const a=process.env.D7_QA_A_EMAIL,b=process.env.D7_QA_B_EMAIL;
    if(!a.endsWith('@example.invalid')||!b.endsWith('@example.invalid')||a===b)
      fail('SYNTHETIC_ACCOUNT_SCOPE');
    stage='CHROME_LAUNCH';
    browser=await chromium.launch({channel:'chrome',headless:true,
      args:['--no-sandbox','--disable-dev-shm-usage']});
    const context=await browser.newContext({
      viewport:{width:390,height:844},locale:'en-US',
      serviceWorkers:'block',acceptDownloads:false});
    let blockedClinical=0;
    const host=new URL(ORIGIN).hostname;
    await context.route('**/*',route=>{
      let u;
      try{u=new URL(route.request().url());}catch{return route.abort();}
      if(u.protocol==='data:'||u.protocol==='blob:')return route.continue();
      if(u.protocol!=='https:'||u.hostname!==host)return route.abort();
      const m=route.request().method();
      if(!['GET','HEAD','OPTIONS'].includes(m) &&
        !['/api/v1/auth/login','/api/v1/auth/logout'].includes(u.pathname)){
        blockedClinical++;return route.abort();
      }
      return route.continue();
    });
    const page=await context.newPage();
    stage='VERCEL_SHARE';
    await page.goto(ORIGIN+'/?_vercel_share='+
      encodeURIComponent(process.env.D7_QA_SSO_ACCESS),
      {waitUntil:'domcontentloaded',timeout:35000});
    await page.goto(ORIGIN+'/login',{waitUntil:'domcontentloaded',timeout:35000});
    await page.waitForSelector('flutter-view,flt-glass-pane',{timeout:45000});
    record('VERCEL_PROTECTED_FLUTTER_BOOT');
    const a1=await login(page,context,a,process.env.D7_QA_A_PASSWORD,'A1');
    await logout(page,a1,'A1');
    const b1=await login(page,context,b,process.env.D7_QA_B_PASSWORD,'B');
    if(a1.id===b1.id)fail('SAME_SERVER_OWNER');
    record('DISTINCT_SERVER_OWNERS');
    await logout(page,b1,'B');
    const a2=await login(page,context,a,process.env.D7_QA_A_PASSWORD,'A2');
    if(a1.id!==a2.id)fail('A_OWNER_CHANGED');
    if(JSON.stringify(a1.profile)!==JSON.stringify(a2.profile))
      fail('A_PROFILE_CHANGED_AFTER_B');
    record('A_PROFILE_STABLE_AFTER_B');
    if(blockedClinical!==0)fail('UNEXPECTED_CLINICAL_WRITE_ATTEMPT');
    proof.clinical_mutations=0;
    proof.distinct_server_owners=true;
    proof.stable_a_owner=true;
    proof.stable_a_profile=true;
    proof.profiles_have_distinguishable_values=
      JSON.stringify(a1.profile)!==JSON.stringify(b1.profile);
    proof.result='BROWSER_ABA_READ_ONLY_PASS_FUE_CLINICAL_NOT_CERTIFIED';
    await context.close();
  }catch {
    proof.result='FAIL_CLOSED';
    proof.error_code='D7_BROWSER_'+stage.replace(/[^A-Z0-9_]/g,'')+'_FAILED';
    process.exitCode=1;
  }finally {
    if(browser)await browser.close();
    fs.mkdirSync('d7-hosted-browser-aba-proof',{recursive:true});
    fs.writeFileSync('d7-hosted-browser-aba-proof/result.json',JSON.stringify(proof,null,2));
    console.log(JSON.stringify(proof));
  }
}
await main();

