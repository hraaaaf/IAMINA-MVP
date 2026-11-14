// D1-P0 synthetic Chromium cross-tab exclusion; NO CLINICAL GO.
// Tests actual Web Locks in two pages of ONE same-origin browser context,
// then proves that the real encrypted AppDatabase candidate refuses admission
// while the other tab holds its owner's exclusive lease.
const { chromium } = require('playwright');
const fs = require('fs');

const folder = 'd1-multitab-encrypted-lease-proof';
const origin = 'http://127.0.0.1:7474';
const owner = 'amina_vault_v1_native_735';
const ownerB = 'amina_vault_v1_native_736';
const proof = {
  head: process.env.D1_CANDIDATE_SHA || 'unknown',
  clinicalGo: false,
  scope: 'two-tab owner-scoped Web Locks + real encrypted schema candidate',
  ownerConflictRejected: false,
  differentOwnerIndependent: false,
  unsupportedApiDenied: false,
  actualCipherEnrollmentRejectedWhileLocked: false,
  noMetadataCreatedWhileLocked: false,
  ownerReacquiredAfterRelease: false,
  actualCipherPassAfterRelease: false,
  result: 'NOT_RUN',
};

function assure(value, label) {
  if (!value) throw Error('D1 multitab check failed: ' + label);
}

async function lease(page, scope) {
  return page.evaluate(async id =>
    globalThis.IaminaD1CryptoCandidate.acquireExclusiveLease(id), scope);
}
async function release(page, scope, token) {
  return page.evaluate(async ({id, token}) =>
    globalThis.IaminaD1CryptoCandidate.releaseExclusiveLease(id, token),
    {id: scope, token});
}
async function expectDenied(page, scope, reason) {
  return page.evaluate(async ({id, reason}) => {
    try {
      const t = await globalThis.IaminaD1CryptoCandidate.acquireExclusiveLease(id);
      await globalThis.IaminaD1CryptoCandidate.releaseExclusiveLease(id, t);
      return false;
    } catch (e) {
      return String(e).includes(reason);
    }
  }, {id:scope, reason});
}
async function awaitProbe(page) {
  await page.waitForFunction(() => {
    const text = document.body?.textContent || '';
    return text.includes('"scope":"synthetic AppDatabase schema + WebCrypto + sqlite3mc"') &&
      (text.includes('"ok":') || text.includes('"error":'));
  }, null, {timeout:60000});
  const body = await page.locator('body').innerText();
  return JSON.parse(body.slice(body.indexOf('{"scope"')));
}
(async () => {
  fs.mkdirSync(folder, {recursive:true});
  const browser = await chromium.launch({headless:true});
  try {
    const ctx = await browser.newContext({serviceWorkers:'block'});
    const first = await ctx.newPage();
    const second = await ctx.newPage();
    await Promise.all([
      first.goto(origin+'/d1-lease-fixture.html', {waitUntil:'load'}),
      second.goto(origin+'/d1-lease-fixture.html', {waitUntil:'load'}),
    ]);
    const tokenA = await lease(first,owner);
    try {
      proof.ownerConflictRejected =
          await expectDenied(second, owner, 'D1_VAULT_TAB_BUSY');
      assure(proof.ownerConflictRejected, 'same owner must deny tab B');

      const tokenB = await lease(second, ownerB);
      proof.differentOwnerIndependent = true;
      await release(second, ownerB, tokenB);

      proof.unsupportedApiDenied = await second.evaluate(async scope => {
        const original = Object.getOwnPropertyDescriptor(navigator, 'locks');
        try {
          Object.defineProperty(navigator, 'locks', {
            configurable:true, value: undefined,
          });
          try {
            await globalThis.IaminaD1CryptoCandidate.acquireExclusiveLease(scope);
            return false;
          } catch (e) {
            return String(e).includes('D1_VAULT_WEB_LOCKS_UNSUPPORTED');
          }
        } finally {
          if (original) Object.defineProperty(navigator, 'locks', original);
          else delete navigator.locks;
        }
      },owner);
      assure(proof.unsupportedApiDenied, 'missing Web Locks must fail closed');

      const probePage = await ctx.newPage();
      await probePage.goto(origin+'/', {waitUntil:'domcontentloaded'});
      const rejected = await awaitProbe(probePage);
      proof.actualCipherEnrollmentRejectedWhileLocked =
          rejected.ok === false &&
          String(rejected.error).includes('D1_VAULT_TAB_BUSY');
      assure(proof.actualCipherEnrollmentRejectedWhileLocked,
          'real encrypted candidate must reject while other tab holds owner');
      proof.noMetadataCreatedWhileLocked = await probePage.evaluate(owner =>
        !localStorage.getItem('iamina_d1_wrapped_vault_v1_'+owner), owner);
      assure(proof.noMetadataCreatedWhileLocked,
          'busy owner must not enroll or overwrite metadata');

      await release(first, owner, tokenA);
      const reopened = await lease(second,owner);
      proof.ownerReacquiredAfterRelease = Boolean(reopened);
      assure(proof.ownerReacquiredAfterRelease,'released owner lease available');
      await release(second, owner,reopened);

      await probePage.goto(origin+'/', {waitUntil:'domcontentloaded'});
      const admitted = await awaitProbe(probePage);
      proof.actualCipherPassAfterRelease = admitted.ok === true;
      assure(proof.actualCipherPassAfterRelease,
          'real encrypted candidate must recover after release: '+JSON.stringify(admitted).slice(0,800));
      await ctx.close();
    } finally {
      // If a test fails, context.close() releases browser-owned locks. No
      // real patient stores or localStorage are ever deleted by this script.
    }
    proof.result='PASS';
  } catch (e) {
    proof.result='FAIL';
    proof.error=String(e.stack||e).slice(0,1800);
    throw e;
  } finally {
    fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_MULTITAB_ENCRYPTED_LEASE='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>{process.exitCode=1;});
