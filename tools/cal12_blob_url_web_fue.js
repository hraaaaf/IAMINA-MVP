/* CAL-12 real Chrome Web Blob URL lifecycle proof; test fixtures only.
 * The fixture code is injected by Playwright on loopback. Neither this file
 * nor the staging fixture JS is part of the shipped Flutter/PWA bundle.
 */
'use strict';

const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('node:assert/strict');

const origin = 'http://127.0.0.1:7394';
const outDir = 'cal12-blob-url-proof';
const stageSource = fs.readFileSync(
  'tools/cal12_blob_url_staging_fixture.js', 'utf8');
const viewports = [[390, 844], [768, 1024], [1280, 900]];
fs.mkdirSync(outDir, {recursive: true});

function makeOnePageFixture(owner) {
  const label = 'CAL12-SYNTHETIC-FIXTURE:fixture:vault:' + owner;
  const textStream = 'BT /F1 11 Tf 70 730 Td (' + label + ') Tj ET';
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] ' +
      '/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    '<< /Length ' + Buffer.byteLength(textStream, 'ascii') +
      ' >>\nstream\n' + textStream + '\nendstream',
  ];
  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  for (let i = 0; i < objects.length; i++) {
    offsets.push(Buffer.byteLength(pdf, 'latin1'));
    pdf += (i + 1) + ' 0 obj\n' + objects[i] + '\nendobj\n';
  }
  const xrefOffset = Buffer.byteLength(pdf, 'latin1');
  pdf += 'xref\n0 ' + (objects.length + 1) + '\n';
  pdf += '0000000000 65535 f \n';
  for (const offset of offsets.slice(1)) {
    pdf += String(offset).padStart(10, '0') + ' 00000 n \n';
  }
  pdf += 'trailer\n<< /Size ' + (objects.length + 1) +
    ' /Root 1 0 R >>\nstartxref\n' + xrefOffset + '\n%%EOF\n';
  return Buffer.from(pdf, 'latin1');
}

const fixtureA = makeOnePageFixture('alpha');
const fixtureB = makeOnePageFixture('beta');
const evidence = {
  status: 'INCOMPLETE',
  sha: process.env.CAL12_HEAD || 'unknown',
  scope: 'Loopback Chromium; staged fictional PDF via Blob URL (not patient export)',
  fixtureSha256: {
    alpha: crypto.createHash('sha256').update(fixtureA).digest('hex'),
    beta: crypto.createHash('sha256').update(fixtureB).digest('hex'),
  },
  exportEnabled: false,
  actualFileDeletionProven: false,
  cases: [],
};

async function runCase(browser, locale, viewport) {
  const context = await browser.newContext({
    viewport: {width:viewport[0], height:viewport[1]},
    locale: locale === 'ar' ? 'ar-MA' : 'fr-FR',
    serviceWorkers: 'block',
    acceptDownloads: false,
  });
  const page = await context.newPage();
  const external = [], writes = [], downloads = [], popups = [], errors = [];
  page.on('pageerror', e => errors.push(String(e.message || e).slice(0,300)));
  page.on('download', d => downloads.push(d.suggestedFilename()));
  page.on('popup', () => popups.push('Unexpected new window'));
  await page.route('**/*', route => {
    const request = route.request();
    const url = request.url();
    if (request.method() !== 'GET') {
      writes.push(request.method());
      return route.abort();
    }
    if (url.startsWith(origin + '/') || url.startsWith('blob:') ||
        url.startsWith('data:')) return route.continue();
    external.push(url.split('?')[0]);
    return route.abort();
  });

  const record = {
    locale,
    viewport: viewport.join('x'),
    status:'FAIL',
    checks:[],
  };
  try {
    const response = await page.goto(origin + '/?lang=' + locale, {
      waitUntil: 'domcontentloaded',
      timeout:60000,
    });
    assert.equal(response.status(), 200);
    await page.waitForSelector('flutter-view', {timeout:60000});
    await page.addScriptTag({content: stageSource});
    const result = await page.evaluate(async ({a,b}) => {
      const stage = window.__cal12BlobStage;
      if (!stage) throw Error('No browser Blob stage');
      const alpha = new Uint8Array(a), beta = new Uint8Array(b);
      const audit = [];
      const ensure = (condition, why) => { if (!condition) throw Error(why); };
      let currentSession = {
        id:'fixture:session:alpha:1', generation:0,
      };
      const activate = (owner, id) => {
        currentSession = {
          id, generation:stage.beginSession('fixture:vault:' + owner, id),
        };
      };
      const make = (owner, bytes) => ({
        owner:'fixture:vault:' + owner,
        sessionId:currentSession.id,
        sessionGeneration:currentSession.generation,
        consentGeneration:currentSession.generation,
        recipientGeneration:currentSession.generation,
        reportOwner:'fixture:vault:' + owner,
        recipient:'fixture:doctor:one',
        confirmedRecipient:'fixture:doctor:one',
        channel:'local-preview', mime:'application/pdf',
        noticeVersion:'CAL12-DRAFT-2026-11-10.1',
        explicitConsent:true, expiresAtMs:Date.now()+10000,
        bytes,
      });
      const denied = (opts, label) => {
        let blocked = false;
        try { stage.open(opts); }
        catch (e) { blocked = /^CAL12_FIXTURE_/.test(String(e.message)); }
        ensure(blocked, 'Unsafe request accepted: ' + label);
        ensure(!stage.active, 'Unsafe request left open handle: ' + label);
        audit.push('DENY_' + label);
      };
      async function canFetch(url) {
        try { const res=await fetch(url); return res.ok; }
        catch (_) { return false; }
      }
      async function readPdf(url, marker) {
        const response = await fetch(url);
        ensure(response.ok, 'Blob unreadable while active');
        ensure(response.headers.get('content-type') === 'application/pdf',
          'Blob MIME wrong');
        const content = await response.text();
        ensure(content.startsWith('%PDF-1.4\n'), 'Not PDF');
        ensure(content.includes('CAL12-SYNTHETIC-FIXTURE:' + marker),
          'Wrong owner PDF read');
      }

      denied(make('alpha', alpha), 'NO_ACTIVE_SESSION');
      activate('alpha', 'fixture:session:alpha:1');
      let url = stage.open(make('alpha', alpha));
      ensure(url.startsWith('blob:'), 'Not Blob URL');
      await readPdf(url, 'fixture:vault:alpha');
      audit.push('PDF_BLOB_READ_ALPHA');
      stage.cancel();
      ensure(!await canFetch(url), 'Cancelled URL still works');
      audit.push('CANCEL_REVOKES_URL');

      const oldAConsent = make('alpha', alpha);
      url = stage.open(oldAConsent);
      activate('beta', 'fixture:session:beta:1');
      ensure(!await canFetch(url), 'A URL available after switching to B');
      ensure(!stage.active, 'A stage still active under B');
      denied(oldAConsent, 'STALE_A_CONSENT_IN_B');
      const oldBConsent = make('beta', beta);
      const bUrl = stage.open(oldBConsent);
      await readPdf(bUrl, 'fixture:vault:beta');
      ensure(!await canFetch(url), 'A URL resurrected under B');
      activate('alpha', 'fixture:session:alpha:2');
      ensure(!await canFetch(bUrl), 'B URL available under A');
      denied(oldAConsent, 'STALE_A_CONSENT_ON_RELOGIN');
      denied(oldBConsent, 'STALE_B_CONSENT_IN_A');
      audit.push('SESSION_A_B_A_REVOKES_OLD_GRANTS');

      // Rotating a session for the same fictional owner is not a consent.
      const sameOwnerConsent = make('alpha', alpha);
      const sameOwnerUrl = stage.open(sameOwnerConsent);
      activate('alpha', 'fixture:session:alpha:2');
      ensure(!await canFetch(sameOwnerUrl), 'Same-owner rotation kept PDF URL');
      denied(sameOwnerConsent, 'SAME_OWNER_OLD_SESSION');
      audit.push('SAME_OWNER_ROTATION_REVOKES');

      denied(Object.assign(make('alpha', alpha), {
        sessionId:'fixture:session:alpha:1',
      }), 'WRONG_SESSION_ID');
      denied(Object.assign(make('alpha', alpha), {
        consentGeneration:currentSession.generation - 1,
      }), 'STALE_CONSENT_GENERATION');
      denied(Object.assign(make('alpha', alpha), {
        recipientGeneration:currentSession.generation - 1,
      }), 'STALE_RECIPIENT_CONFIRMATION');
      denied(Object.assign(make('alpha', alpha), {
        owner:'real-patient-23',
      }), 'REAL_PATIENT_ID');
      denied(Object.assign(make('alpha', alpha), {
        reportOwner:'fixture:vault:beta',
      }), 'REPORT_OWNER_MISMATCH');
      denied(Object.assign(make('alpha', alpha), {
        recipient:'dr@hospital.example',
      }), 'REAL_DOCTOR_ID');
      denied(Object.assign(make('alpha', alpha), {
        confirmedRecipient:'fixture:doctor:two',
      }), 'RECIPIENT_MISMATCH');
      denied(Object.assign(make('alpha', alpha), {
        explicitConsent:false,
      }), 'NO_CONSENT');
      denied(Object.assign(make('alpha', alpha), {
        channel:'secure-recipient-delivery',
      }), 'NO_DELIVERY_CHANNEL');
      denied(Object.assign(make('alpha', alpha), {
        noticeVersion:'stale-notice',
      }), 'NOTICE_CHANGED');
      denied(Object.assign(make('alpha', alpha), {
        expiresAtMs:Date.now()-1,
      }), 'EXPIRED_CONSENT');
      denied(Object.assign(make('alpha', alpha), {
        mime:'text/plain',
      }), 'MIME_NOT_PDF');
      denied(Object.assign(make('alpha', beta), {}),
        'WRONG_PDF_PROVENANCE');
      denied(Object.assign(make('alpha', new Uint8Array(262145)), {}),
        'OVERSIZED_PDF');

      // Reject a forged owner/session pair before any new PDF can be read.
      const invalidSessionUrl = stage.open(make('alpha', alpha));
      let invalidPairRejected = false;
      try {
        stage.beginSession('fixture:vault:alpha', 'fixture:session:beta:1');
      } catch (e) {
        invalidPairRejected =
          String(e.message).includes('CAL12_FIXTURE_SESSION_SCOPE');
      }
      ensure(invalidPairRejected, 'Invalid owner/session pair accepted');
      ensure(!await canFetch(invalidSessionUrl),
        'Invalid session pair retained an old PDF URL');
      denied(make('alpha', alpha), 'INVALID_SESSION_PAIR_CLEARS_SESSION');
      activate('alpha', 'fixture:session:alpha:2');
      audit.push('INVALID_SESSION_PAIR_FAILS_CLOSED');

      const loggedOutConsent = make('alpha', alpha);
      const loggedOutUrl = stage.open(loggedOutConsent);
      stage.endSession('logout');
      ensure(!await canFetch(loggedOutUrl), 'Logout retained Blob URL');
      denied(loggedOutConsent, 'CONSENT_AFTER_LOGOUT');
      activate('alpha', 'fixture:session:alpha:2');
      denied(loggedOutConsent, 'CONSENT_AFTER_LOGIN');
      audit.push('LOGOUT_RELOGIN_FAIL_CLOSED');

      let inSuccess = null;
      await stage.useOnce(make('alpha', alpha), async localUrl => {
        inSuccess = localUrl;
        await readPdf(localUrl, 'fixture:vault:alpha');
      });
      ensure(!await canFetch(inSuccess), 'Success leaked URL');
      audit.push('SUCCESS_FINALLY_REVOKES');

      let failedUrl = null;
      let thrown = false;
      try {
        await stage.useOnce(make('alpha', alpha), async localUrl => {
          failedUrl = localUrl;
          throw Error('synthetic-operation-failed');
        });
      } catch (e) {
        thrown = String(e.message).includes('synthetic-operation-failed');
      }
      ensure(thrown, 'Failed callback not propagated');
      ensure(!await canFetch(failedUrl), 'Error leaked URL');
      audit.push('EXCEPTION_FINALLY_REVOKES');

      let revokedUrl = null;
      let revokeFailedClosed = false;
      try {
        await stage.useOnce(make('alpha', alpha), async localUrl => {
          revokedUrl = localUrl;
          stage.revoke();
        });
      } catch (e) {
        revokeFailedClosed = String(e.message).includes('REVOKED_DURING_USE');
      }
      ensure(revokeFailedClosed, 'Revocation during operation was accepted');
      ensure(!await canFetch(revokedUrl), 'Revoked in-flight URL still works');
      audit.push('REVOKE_IN_FLIGHT');

      // A timer expires the URL without requiring user interaction.
      const short = make('alpha', alpha);
      short.expiresAtMs = Date.now() + 300;
      const expiringUrl = stage.open(short);
      await new Promise(resolve => setTimeout(resolve, 550));
      ensure(!stage.active && !await canFetch(expiringUrl),
        'Expired URL still accessible');
      audit.push('TIMER_EXPIRY_REVOKES');

      const exitUrl = stage.open(make('alpha', alpha));
      window.dispatchEvent(new Event('pagehide'));
      ensure(!await canFetch(exitUrl), 'pagehide did not revoke URL');
      audit.push('PAGEHIDE_REVOKES');

      const m = stage.metrics;
      ensure(!m.sessionActive, 'pagehide left synthetic session active');
      ensure(!m.active && m.created === m.revoked,
        'Object URLs leaked; created=' + m.created + ' revoked=' + m.revoked);
      ensure(m.created >= 7, 'Insufficient positive fixture operations');
      ensure(alpha.length > 100 && beta.length > 100, 'Fixture bytes invalid');
      return {checks:audit,metrics:m};
    }, {a:[...fixtureA],b:[...fixtureB]});
    assert.ok(result.checks.length >= 26);
    for (const mandatory of [
      'DENY_NO_ACTIVE_SESSION',
      'DENY_STALE_A_CONSENT_ON_RELOGIN',
      'DENY_SAME_OWNER_OLD_SESSION',
      'DENY_CONSENT_AFTER_LOGOUT',
      'DENY_STALE_CONSENT_GENERATION',
      'DENY_STALE_RECIPIENT_CONFIRMATION',
      'SESSION_A_B_A_REVOKES_OLD_GRANTS',
      'SAME_OWNER_ROTATION_REVOKES',
      'LOGOUT_RELOGIN_FAIL_CLOSED',
    ]) {
      assert.ok(result.checks.includes(mandatory),
        'Missing synthetic session proof: ' + mandatory);
    }
    assert.equal(result.metrics.active,false);
    assert.equal(result.metrics.created,result.metrics.revoked);
    assert.deepEqual(external,[]);
    assert.deepEqual(writes,[]);
    assert.deepEqual(downloads,[]);
    assert.deepEqual(popups,[]);
    assert.deepEqual(errors,[]);
    record.checks = result.checks;
    record.metrics = result.metrics;
    record.status='PASS';
  } catch (err) {
    record.error = String(err.stack||err).slice(0,1900);
  } finally {
    evidence.cases.push(record);
    await context.close();
  }
}

async function main() {
  const browser = await chromium.launch({headless:true});
  try {
    for (const locale of ['fr','ar']) {
      for (const viewport of viewports) {
        await runCase(browser, locale, viewport);
      }
    }
  } finally {
    await browser.close();
    evidence.status = evidence.cases.length === 6 &&
      evidence.cases.every(x=>x.status==='PASS')
      ? 'PASS_SYNTHETIC_BLOB_URL_LIFECYCLE_ONLY'
      : 'FAIL';
    fs.writeFileSync(path.join(outDir, 'proof.json'),
      JSON.stringify(evidence,null,2)+'\n');
  }
  assert.equal(evidence.status,'PASS_SYNTHETIC_BLOB_URL_LIFECYCLE_ONLY',
    'CAL12 Web Blob URL proof failed: '+
      JSON.stringify(evidence.cases.filter(c=>c.status!=='PASS')));
}
main().catch(err=>{ console.error(err); process.exitCode=1; });
