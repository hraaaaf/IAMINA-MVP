// QA read-only: actual Chrome on hosted Ubuntu / protected Vercel Preview.
// No clinical writes, no consent action, no credential/cookie/token/PHI in artifacts.
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import path from 'node:path';

export const ORIGIN = 'https://iamina-review-git-cert-d7-we-5e65d5-achraf-benmoussa-s-projects.vercel.app';
export const DEPLOY_SHA = 'c10e6e69acb322820227b630a1efaf5c834e2f74';
export const VIEWPORTS = [[390,844], [768,1024], [1280,900]];
// Exact localized actions; do not bind an English Chrome session to French UI.
export const ACCOUNT_CHOICE_LABEL =
  /^(?:Sign in or create an account|Se connecter ou créer un compte|تسجيل الدخول أو إنشاء حساب)$/;
export const LOGIN_SUBMIT_LABEL = /^(?:Sign in|Se connecter|الدخول)$/;

function fail(code) { throw new Error('D7_CHROME_' + code); }

// Flutter Web semantics are opt-in. The invisible activation placeholder may
// be offscreen: Playwright's click({force:true}) can fail and must not be
// silently ignored. Dispatch only on that exact placeholder, not on the UI.
export async function activateFlutterAccountSemantics(page) {
  const placeholder=page.locator('flt-semantics-placeholder').first();
  if(!await placeholder.count())fail('ACCESSIBILITY_PLACEHOLDER_MISSING');
  try {
    await placeholder.evaluate(element => {
      const bounds=element.getBoundingClientRect();
      element.dispatchEvent(new MouseEvent('click',{
        bubbles:true,cancelable:true,
        clientX:Math.round(bounds.left+bounds.width/2),
        clientY:Math.round(bounds.top+bounds.height/2),
      }));
    });
  } catch { fail('ACCESSIBILITY_ACTIVATION_FAILED'); }
  const button=page.getByRole('button',{name:ACCOUNT_CHOICE_LABEL}).first();
  try {
    await button.waitFor({state:'visible',timeout:12000});
  } catch { fail('ACCOUNT_BUTTON_INACCESSIBLE'); }
  return button;
}
// Only bounded stage codes may leave the private QA runner.
export const D7_QA_STAGES = Object.freeze([
  'INIT','BROWSER_LAUNCH','SHARE_ACCESS','FLUTTER_BOOT',
  'PUBLIC_CAPTURE','ACCOUNT_SEMANTICS','ACCOUNT_CLICK',
  'INPUT_DISCOVERY','EMAIL_FILL','PASSWORD_FILL',
  'SUBMIT_DISCOVERY','SUBMIT_CLICK','LOGIN_REDIRECT','PROFILE_READ',
]);
export function safeBrowserErrorCode(error,stage) {
  const message=String(error?.message||'');
  if (/^D7_CHROME_[A-Z0-9_]+$/.test(message)) return message;
  return D7_QA_STAGES.includes(stage)
    ? 'D7_CHROME_' + stage + '_FAILED' : 'D7_CHROME_BROWSER_ERROR';
}

// Classify only the HTTP status observed by the QA browser; never emit
// response body, URL, credentials, cookies or session tokens.
export function loginRedirectFailureCode(status) {
  if(status===undefined || status===null) return 'D7_CHROME_LOGIN_NO_HTTP_RESPONSE';
  if(status===401) return 'D7_CHROME_LOGIN_HTTP_401';
  if(status===403) return 'D7_CHROME_LOGIN_HTTP_403';
  if(status>=500 && status<600) return 'D7_CHROME_LOGIN_HTTP_5XX';
  if(status>=400 && status<500) return 'D7_CHROME_LOGIN_HTTP_4XX';
  if(status>=200 && status<300) return 'D7_CHROME_LOGIN_HTTP_2XX_NO_REDIRECT';
  return 'D7_CHROME_LOGIN_HTTP_OTHER_NO_REDIRECT';
}

// A 401 on the login URL may be returned by Django or an upstream gate.
// Inspect only the exact Django error contract in RAM; never log bodies,
// request URLs, tokens, credential data, or received headers.
export async function classifyLogin401Response(response) {
  if (!response || response.status()!==401) return null;
  let type;
  try { type = await response.headerValue('content-type'); }
  catch { return 'D7_CHROME_LOGIN_HTTP_401_OTHER'; }
  if (!type?.toLowerCase().includes('application/json'))
    return 'D7_CHROME_LOGIN_HTTP_401_OTHER';
  try {
    const body = await response.json();
    if (body && typeof body==='object' && !Array.isArray(body) &&
        Object.keys(body).length===1 &&
        body.detail==='Invalid authentication credential')
      return 'D7_CHROME_LOGIN_DJANGO_CREDENTIAL_REJECTED';
  } catch { /* Never expose the untrusted response. */ }
  return 'D7_CHROME_LOGIN_HTTP_401_OTHER';
}

export function guard({origin,sha,token,email,password}) {
  if (origin !== ORIGIN || sha !== DEPLOY_SHA) fail('UNEXPECTED_DEPLOYMENT');
  if (typeof token !== 'string' || !/^[a-zA-Z0-9._~-]{10,512}$/.test(token))
    fail('TEMPORARY_SSO_SECRET_REQUIRED');
  if (typeof email !== 'string' ||
      !/^[^@\s]+@example\.(invalid|test)$/.test(email.toLowerCase()))
    fail('SYNTHETIC_ACCOUNT_REQUIRED');
  if (typeof password !== 'string' || !password) fail('ACCOUNT_SECRET_REQUIRED');
  return true;
}
export const emptyProof = () => ({
  preview_sha: DEPLOY_SHA,
  browser: 'remote GitHub Ubuntu Chrome',
  result: 'NOT_RUN',
  steps: {boot:'NOT_RUN',login_capture:'NOT_RUN',native_login:'NOT_RUN',
    profile_read_only:'NOT_RUN',treatment_change_and_persistence:'NOT_RUN',
    clinical_privacy_review:'NOT_RUN'},
  screenshots: [], private_data: 'NOT_COLLECTED'
});
async function main() {
  const result = emptyProof();
  fs.mkdirSync('d7-qa-chrome-proof', {recursive:true});
  const save = () => fs.writeFileSync('d7-qa-chrome-proof/result.json',
    JSON.stringify(result,null,2));
  let browser;
  let stage='INIT';
  try {
    guard({origin:ORIGIN,sha:process.env.D7_PREVIEW_SHA,
      token:process.env.D7_QA_SSO_ACCESS,email:process.env.D7_QA_A_EMAIL,
      password:process.env.D7_QA_A_PASSWORD});
    const {chromium} = await import('playwright');
    stage='BROWSER_LAUNCH';
    browser = await chromium.launch({channel:'chrome', headless:true,
      args:['--no-sandbox','--disable-dev-shm-usage']});
    const context = await browser.newContext({
      viewport:{width:390,height:844},acceptDownloads:false,serviceWorkers:'block'
    });
    const page = await context.newPage();
    const host = new URL(ORIGIN).hostname;
    await context.route('**/*', route => {
      const u = new URL(route.request().url());
      return u.protocol === 'https:' && u.hostname === host
        ? route.continue() : route.abort();
    });
    // Share URL never written, printed or captured. Browser cookies stay in RAM.
    const share = ORIGIN + '/?_vercel_share=' +
      encodeURIComponent(process.env.D7_QA_SSO_ACCESS);
    stage='SHARE_ACCESS';
    await page.goto(share,{waitUntil:'domcontentloaded',timeout:30000});
    stage='FLUTTER_BOOT';
    await page.goto(ORIGIN+'/login',{waitUntil:'domcontentloaded',timeout:30000});
    await page.waitForFunction(() => document.title.toLowerCase()==='iamina'
      && !!document.querySelector('flutter-view,flt-glass-pane,flt-scene-host'),
      null,{timeout:60000});
    if (new URL(page.url()).origin !== ORIGIN) fail('SSO_OR_FLUTTER_FAILED');
    result.steps.boot='PASS';
    // Flutter Web paints pixels on CanvasKit. Its text enters the DOM only
    // after web accessibility is enabled; do not swallow an activation error.
    // Public login screenshots only: no account information entered yet.
    stage='PUBLIC_CAPTURE';
    for(const [width,height] of VIEWPORTS){
      await page.setViewportSize({width,height});
      await page.waitForTimeout(900);
      if (new URL(page.url()).pathname!=='/login') fail('NOT_LOGIN_SCREEN');
      const name='login-'+width+'x'+height+'.png';
      await page.screenshot({path:'d7-qa-chrome-proof/'+name});
      if(fs.statSync('d7-qa-chrome-proof/'+name).size<1000)
        fail('EMPTY_CAPTURE');
      result.screenshots.push(name);
    }
    result.steps.login_capture='CAPTURED_NOT_VISUALLY_CERTIFIED';
    await page.setViewportSize({width:390,height:844});
    stage='ACCOUNT_SEMANTICS';
    const choose=await activateFlutterAccountSemantics(page);
    stage='ACCOUNT_CLICK';
    await choose.click({timeout:15000});
    stage='INPUT_DISCOVERY';
    const inputs=page.locator('input:not([type="hidden"])');
    if(await inputs.count()<2)fail('LOGIN_INPUTS_INACCESSIBLE');
    const email=page.locator('input[type="email"]').first();
    const pass=page.locator('input[type="password"]').first();
    stage='EMAIL_FILL';
    await (await email.count()?email:inputs.first())
      .fill(process.env.D7_QA_A_EMAIL,{timeout:10000});
    stage='PASSWORD_FILL';
    await (await pass.count()?pass:inputs.nth(1))
      .fill(process.env.D7_QA_A_PASSWORD,{timeout:10000});
    let status,loginResponse;
    page.on('response',r=>{
      if(r.url().split('?')[0]===ORIGIN+'/api/v1/auth/login') {
        status=r.status();
        loginResponse=r;
      }
    });
    stage='SUBMIT_DISCOVERY';
    const submit=page.getByRole('button',{name:LOGIN_SUBMIT_LABEL}).last();
    if(!await submit.count())fail('SUBMIT_INACCESSIBLE');
    stage='SUBMIT_CLICK';
    await submit.click({timeout:15000});
    stage='LOGIN_REDIRECT';
    await page.waitForURL(url=>new URL(url).pathname!=='/login',
      {timeout:30000}).catch(async()=>{
        const classified=await classifyLogin401Response(loginResponse);
        throw new Error(classified||loginRedirectFailureCode(status));
      });
    if(status!==200)fail('NATIVE_LOGIN_NOT_CONFIRMED');
    result.steps.native_login='PASS';
    // Never click any consent dialog. The QA owner must approve consent.
    stage='PROFILE_READ';
    await page.goto(ORIGIN+'/profile',{waitUntil:'domcontentloaded'});
    await page.waitForTimeout(3000);
    if(new URL(page.url()).pathname!=='/profile')
      fail('PROFILE_OR_CONSENT_GATE');
    await page.waitForFunction(()=>!!document.querySelector(
      'flutter-view,flt-glass-pane,flt-scene-host'),null,{timeout:20000});
    result.steps.profile_read_only='PASS';
    result.result='READ_ONLY_HOSTED_PREFLIGHT_PASS_FUE_NOT_CERTIFIED';
    await context.close();
  } catch(error) {
    result.result='FAIL';
    result.error_code=safeBrowserErrorCode(error,stage);
    process.exitCode=1;
    process.stderr.write(result.error_code+'\n');
  } finally {
    if(browser)await browser.close();
    save();
  }
}
if(process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)
  await main();
