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
  try {
    guard({origin:ORIGIN,sha:process.env.D7_PREVIEW_SHA,
      token:process.env.D7_QA_SSO_ACCESS,email:process.env.D7_QA_A_EMAIL,
      password:process.env.D7_QA_A_PASSWORD});
    const {chromium} = await import('playwright');
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
    await page.goto(share,{waitUntil:'domcontentloaded',timeout:30000});
    await page.goto(ORIGIN+'/login',{waitUntil:'domcontentloaded',timeout:30000});
    await page.waitForFunction(() => document.title.toLowerCase()==='iamina'
      && !!document.querySelector('flutter-view,flt-glass-pane,flt-scene-host'),
      null,{timeout:60000});
    if (new URL(page.url()).origin !== ORIGIN) fail('SSO_OR_FLUTTER_FAILED');
    result.steps.boot='PASS';
    // Flutter Web paints pixels on CanvasKit. Its text enters the DOM only
    // after web accessibility is enabled; do not swallow an activation error.
    // Public login screenshots only: no account information entered yet.
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
    const choose=await activateFlutterAccountSemantics(page);
    await choose.click({timeout:15000});
    const inputs=page.locator('input:not([type="hidden"])');
    if(await inputs.count()<2)fail('LOGIN_INPUTS_INACCESSIBLE');
    const email=page.locator('input[type="email"]').first();
    const pass=page.locator('input[type="password"]').first();
    await (await email.count()?email:inputs.first())
      .fill(process.env.D7_QA_A_EMAIL,{timeout:10000});
    await (await pass.count()?pass:inputs.nth(1))
      .fill(process.env.D7_QA_A_PASSWORD,{timeout:10000});
    let status;
    page.on('response',r=>{
      if(r.url().split('?')[0]===ORIGIN+'/api/v1/auth/login')
        status=r.status();
    });
    const submit=page.getByRole('button',{name:LOGIN_SUBMIT_LABEL}).last();
    if(!await submit.count())fail('SUBMIT_INACCESSIBLE');
    await submit.click({timeout:15000});
    await page.waitForURL(url=>new URL(url).pathname!=='/login',
      {timeout:30000});
    if(status!==200)fail('NATIVE_LOGIN_NOT_CONFIRMED');
    result.steps.native_login='PASS';
    // Never click any consent dialog. The QA owner must approve consent.
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
    const m=String(error?.message||'');
    result.result='FAIL';
    result.error_code=/^D7_CHROME_[A-Z0-9_]+$/.test(m)?m:'D7_CHROME_BROWSER_ERROR';
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
