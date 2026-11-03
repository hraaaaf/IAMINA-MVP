// D18 CANARY: exercise the actual web/d18_source_interlock.js across real
// browser tabs. This does not prove old cached tabs or clinical encryption.
'use strict';
const fs = require('node:fs'), http = require('node:http');
const os = require('node:os'), path = require('node:path');
const {chromium, webkit} = require('playwright');
const engineName = process.env.D18_SOURCE_INTERLOCK_BROWSER || 'chromium';
if (!['chromium', 'webkit'].includes(engineName)) throw Error('INVALID_BROWSER');
const root = 'iamina:d18:precutover:source:v1:';
const a = 'amina_vault_v1_native_734', b = 'amina_vault_v1_native_812';
const source = fs.readFileSync('frontend/web/d18_source_interlock.js');
const report = [];
const server = http.createServer((req, res) => {
  if (req.url === '/d18_source_interlock.js') {
    res.writeHead(200, {'content-type': 'application/javascript', 'cache-control': 'no-store'});
    res.end(source);
  } else {
    res.writeHead(200, {'content-type': 'text/html', 'cache-control': 'no-store'});
    res.end('<!doctype html><script src="/d18_source_interlock.js"></script>');
  }
});
function phase(name, actual, expected) {
  const pass = actual === expected;
  report.push({phase: name, pass});
  if (!pass) throw Error(name + '_FAILED');
}
async function run() {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'd18-source-live-'));
  let browser;
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    browser = await (engineName === 'chromium' ? chromium : webkit).launch({
      headless: true, ...(engineName === 'chromium' ? {args: ['--no-sandbox']} : {}),
    });
    const context = await browser.newContext({viewport: {width: 390, height: 844}});
    const url = 'http://127.0.0.1:' + server.address().port + '/';
    async function tab(noLocks = false) {
      const page = await context.newPage();
      if (noLocks) await page.addInitScript(() => {
        Object.defineProperty(navigator, 'locks', {value: undefined, configurable: true});
      });
      await page.goto(url, {waitUntil: 'load'});
      return page;
    }
    async function open(page, type, scope) {
      return page.evaluate(async ({type, scope}) => {
        const gate = globalThis.IAMINA_D18_SOURCE_BARRIER;
        return type === 'legacy' ? gate.acquireLegacy() : gate.acquirePatient(scope);
      }, {type, scope});
    }
    async function close(page, slot) {
      return page.evaluate(async slot => globalThis.IAMINA_D18_SOURCE_BARRIER.release(slot), slot);
    }
    async function attemptMigration(page, scope) {
      return page.evaluate(async ({scope, root}) =>
        navigator.locks.request(root + 'legacy', {mode: 'exclusive', ifAvailable: true},
          async first => first ? navigator.locks.request(
            root + 'patient:' + scope, {mode: 'exclusive', ifAvailable: true},
            second => !!second) : false), {scope, root});
    }
    const legacy = await tab(), pa = await tab(), pb = await tab();
    const migrator = await tab(), unsupported = await tab(true);
    phase('audit_scope_rejected', await pa.evaluate(async () => {
      try {
        await IAMINA_D18_SOURCE_BARRIER.acquirePatient('amina_vault_v1_audit');
        return false;
      } catch (_) { return true; }
    }), true);
    phase('missing_lock_api_denied', await unsupported.evaluate(async () => {
      try { await IAMINA_D18_SOURCE_BARRIER.acquireLegacy(); return false; }
      catch (_) { return true; }
    }), true);
    const l = await open(legacy, 'legacy');
    phase('legacy_real_script_acquired', typeof l, 'string');
    const aa = await open(pa, 'patient', a);
    phase('patient_a_real_script_acquired', typeof aa, 'string');
    const bb = await open(pb, 'patient', b);
    phase('patient_b_real_script_acquired', typeof bb, 'string');
    phase('legacy_blocks_migration', await attemptMigration(migrator, a), false);
    phase('close_legacy', await close(legacy, l), true);
    phase('patient_a_blocks_migration', await attemptMigration(migrator, a), false);
    phase('patient_b_independent', await attemptMigration(migrator, b), true);
    phase('close_patient_a', await close(pa, aa), true);
    phase('migration_a_available', await attemptMigration(migrator, a), true);
    phase('close_patient_b', await close(pb, bb), true);
    const again = await open(pa, 'patient', a);
    phase('reopen_patient_a', typeof again, 'string');
    phase('double_release_denied', await pa.evaluate(async slot => {
      await IAMINA_D18_SOURCE_BARRIER.release(slot);
      try { await IAMINA_D18_SOURCE_BARRIER.release(slot); return false; }
      catch (_) { return true; }
    }, again), true);
    phase('migration_after_release', await attemptMigration(migrator, a), true);
  } finally {
    await browser?.close().catch(() => {});
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(profile, {recursive: true, force: true});
  }
}
(async () => {
  try { await run(); }
  catch (error) {
    report.push({phase: 'harness', pass: false,
      code: String(error.message || 'UNKNOWN').replace(/[^A-Za-z0-9_]/g, '_').slice(0, 100)});
    process.exitCode = 1;
  }
  console.log(JSON.stringify({kind: 'D18_REAL_SCRIPT_COOPERATIVE_CANARY_NOT_CUTOVER',
    browser: engineName, sha: process.env.GITHUB_SHA || null, report}));
  if (report.length !== 14 || report.some(x => !x.pass)) process.exitCode = 1;
})().catch(e => {console.error('D18_CANARY_FATAL', e.name);process.exitCode = 1;});
