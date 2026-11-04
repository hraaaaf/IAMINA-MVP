// D18 CI-ONLY: cooperative source leases for legacy and scoped SQLite opens.
// This proof uses synthetic names; production AppDatabase is NOT instrumented.
// No clinical data, no migration or patient-facing entrypoints.
'use strict';
const {chromium, webkit} = require('playwright');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const http = require('node:http');
const engineName = process.env.D18_SOURCE_BARRIER_BROWSER || 'chromium';
if (!['chromium', 'webkit'].includes(engineName)) {
  throw Error('D18_BARRIER_UNSUPPORTED_ENGINE');
}
const engine = engineName === 'webkit' ? webkit : chromium;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'd18-source-barrier-'));
const a = 'amina_vault_v1_native_734', b = 'amina_vault_v1_native_812';
const report = [], keyPrefix = 'iamina:d18:precutover:source:v1:';

function isolatedFixture() {
  'use strict';
  const valid = /^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$/;
  const root = 'iamina:d18:precutover:source:v1:';
  const legacyKey = root + 'legacy', patientKey = name => root + 'patient:' + name;
  const held = new Map();
  async function acquire(slot, requests) {
    if (!navigator.locks || typeof navigator.locks.request !== 'function') {
      return 'UNSUPPORTED';
    }
    if (held.has(slot)) return 'SLOT_ALREADY_USED';
    let resolveGrant, resolveRelease;
    const granted = new Promise(resolve => { resolveGrant = resolve; });
    const untilRelease = new Promise(resolve => { resolveRelease = resolve; });
    let notified = false;
    const notify = ok => {
      if (!notified) { notified = true; resolveGrant(ok); }
    };
    async function nested(index) {
      if (index === requests.length) {
        notify(true);
        await untilRelease;
        return;
      }
      const [name, mode] = requests[index];
      await navigator.locks.request(name, {mode, ifAvailable: true}, async lock => {
        if (!lock) { notify(false); return; }
        await nested(index + 1);
      });
    }
    const running = nested(0).catch(() => notify(false));
    if (!await granted) {
      await running;
      return 'LOCK_UNAVAILABLE';
    }
    let released = false;
    held.set(slot, async () => {
      if (released) return;
      released = true;
      resolveRelease();
      await running;
      held.delete(slot);
    });
    return 'ACQUIRED';
  }
  const scopeOk = scope => typeof scope === 'string' && valid.test(scope);
  globalThis.D18SourceBarrierCI = Object.freeze({
    legacy: slot => acquire(slot, [[legacyKey, 'shared']]),
    patient: (scope, slot) => scopeOk(scope)
      ? acquire(slot, [[patientKey(scope), 'shared']])
      : Promise.resolve('INVALID_SCOPE'),
    migrate: (scope, slot) => scopeOk(scope)
      ? acquire(slot, [[legacyKey, 'exclusive'], [patientKey(scope), 'exclusive']])
      : Promise.resolve('INVALID_SCOPE'),
    release: async slot => {
      const close = held.get(slot);
      if (!close) return false;
      await close();
      return true;
    },
  });
}
const server = http.createServer((_req, res) => {
  res.writeHead(200, {
    'content-type': 'text/html; charset=utf-8',
    'cache-control': 'no-store',
  });
  res.end('<!doctype html><html lang="fr"><title>D18 source barrier</title></html>');
});
function assertPhase(phase, actual, expected) {
  const pass = actual === expected;
  report.push({phase, pass});
  if (!pass) throw Error('D18_BARRIER_' + phase + '_EXPECTED_' + expected);
}
async function createPage(ctx, withoutWebLocks = false) {
  const page = await ctx.newPage();
  await page.addInitScript({content: '(' + isolatedFixture.toString() + ')()'});
  if (withoutWebLocks) {
    await page.addInitScript({content:
      "Object.defineProperty(navigator,'locks',{value:undefined,configurable:true});"});
  }
  await page.goto('http://127.0.0.1:' + server.address().port + '/', {
    waitUntil: 'domcontentloaded', timeout: 30000,
  });
  return page;
}
async function enter(page, kind, slot, scope) {
  return await page.evaluate(async ({kind, slot, scope}) => {
    const gate = globalThis.D18SourceBarrierCI;
    return kind === 'legacy' ? gate.legacy(slot)
      : kind === 'patient' ? gate.patient(scope, slot)
      : gate.migrate(scope, slot);
  }, {kind, slot, scope});
}
async function release(page, slot) {
  return await page.evaluate(slot => globalThis.D18SourceBarrierCI.release(slot), slot);
}
async function run() {
  let ctx;
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  try {
    ctx = await engine.launchPersistentContext(profile, {
      headless: true, locale: 'fr-FR', viewport: {width: 390, height: 844},
      ...(engineName === 'chromium' ?
        {args: ['--no-sandbox', '--disable-dev-shm-usage']} : {}),
    });
    const legacy = await createPage(ctx);
    const patientA = await createPage(ctx);
    const patientB = await createPage(ctx);
    const migrator = await createPage(ctx);
    const observer = await createPage(ctx);
    const missingApi = await createPage(ctx, true);
    assertPhase('invalid_scope_denied',
      await enter(observer, 'migrate', 'invalid', 'amina'), 'INVALID_SCOPE');
    assertPhase('unsupported_web_locks_fail_closed',
      await enter(missingApi, 'patient', 'unsupported', a), 'UNSUPPORTED');
    assertPhase('legacy_shared_open',
      await enter(legacy, 'legacy', 'old'), 'ACQUIRED');
    assertPhase('patient_a_shared_with_legacy',
      await enter(patientA, 'patient', 'a', a), 'ACQUIRED');
    assertPhase('migration_a_blocked_by_legacy',
      await enter(migrator, 'migrate', 'm1', a), 'LOCK_UNAVAILABLE');
    assertPhase('legacy_release', await release(legacy, 'old'), true);
    assertPhase('migration_a_still_blocked_by_patient',
      await enter(migrator, 'migrate', 'm2', a), 'LOCK_UNAVAILABLE');
    assertPhase('patient_b_independent',
      await enter(patientB, 'patient', 'b', b), 'ACQUIRED');
    assertPhase('patient_a_release', await release(patientA, 'a'), true);
    assertPhase('migration_a_exclusive',
      await enter(migrator, 'migrate', 'm3', a), 'ACQUIRED');
    assertPhase('legacy_reopen_blocked_during_migration',
      await enter(legacy, 'legacy', 'old2'), 'LOCK_UNAVAILABLE');
    assertPhase('patient_a_reopen_blocked_during_migration',
      await enter(patientA, 'patient', 'a2', a), 'LOCK_UNAVAILABLE');
    assertPhase('patient_b_open_while_a_migrating',
      await enter(observer, 'patient', 'b2', b), 'ACQUIRED');
    assertPhase('second_migration_b_blocked_by_global_lock',
      await enter(observer, 'migrate', 'm4', b), 'LOCK_UNAVAILABLE');
    await migrator.close();
    await observer.waitForFunction(async key => {
      const state = await navigator.locks.query();
      return !state.held.some(lock => lock.name === key);
    }, keyPrefix + 'legacy', {timeout: 15000});
    assertPhase('crashed_migrator_releases_global_lock',
      await enter(legacy, 'legacy', 'old3'), 'ACQUIRED');
    assertPhase('legacy_blocks_other_scope_migration',
      await enter(patientA, 'migrate', 'm5', b), 'LOCK_UNAVAILABLE');
    assertPhase('legacy_release_again', await release(legacy, 'old3'), true);
    assertPhase('patient_b_release', await release(patientB, 'b'), true);
    assertPhase('patient_b_secondary_release', await release(observer, 'b2'), true);
    assertPhase('migration_b_after_all_source_leases_close',
      await enter(patientA, 'migrate', 'm6', b), 'ACQUIRED');
    assertPhase('migration_b_release', await release(patientA, 'm6'), true);
  } finally {
    await ctx?.close().catch(() => {});
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(profile, {recursive: true, force: true});
  }
}
(async () => {
  try { await run(); } catch (error) {
    report.push({phase: 'harness', pass: false,
      code: String(error.message || 'UNKNOWN').replace(/[^A-Za-z0-9_]/g, '_').slice(0, 140)});
    process.exitCode = 1;
  }
  fs.mkdirSync('d18-source-barrier-proof', {recursive: true});
  fs.writeFileSync('d18-source-barrier-proof/report-' + engineName + '.json',
    JSON.stringify({kind: 'D18_COOPERATIVE_SOURCE_LOCKS_TEST_ONLY',
      sha: process.env.GITHUB_SHA || null, engine: engineName, report}, null, 2));
  console.log(JSON.stringify(report));
  if (report.length !== 21 || report.some(item => !item.pass)) process.exitCode = 1;
})().catch(error => {console.error('D18_BARRIER_FATAL', error.name);process.exitCode = 1;});
