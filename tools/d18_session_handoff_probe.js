// D18 CI-only dynamic-key MessagePort handoff: no clinical DB and no secrets logged.
// This proves a transport primitive, NOT integration with Drift's worker protocol.
'use strict';
const {chromium} = require('playwright');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'd18-keyport-'));
const steps = [];

async function visit(ctx) {
  const page = await ctx.newPage();
  await page.goto('http://127.0.0.1:7396/', {waitUntil: 'domcontentloaded'});
  return page;
}
(async () => {
  let browser;
  try {
    browser = await chromium.launchPersistentContext(userData, {
      headless: true, locale: 'fr-FR',
      args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    const page = await visit(browser);
    const first = await page.evaluate(async () => {
      const seen = [];
      const insist = (phase, ok) => {
        seen.push({phase, pass: !!ok});
        if (!ok) throw Error('D18_KEYPORT_CHECK_' + phase);
      };
      const scopeA = 'amina_vault_v1_device_' + 'a'.repeat(32);
      const scopeB = 'amina_vault_v1_device_' + 'b'.repeat(32);
      const sessionA = '11111111-1111-4111-8111-111111111111';
      const sessionB = '22222222-2222-4222-8222-222222222222';
      const worker = new Worker('/d18_session_handshake_probe_worker.js');
      function attach(w) {
        const channel = new MessageChannel();
        w.postMessage({type: 'D18_ATTACH'}, [channel.port2]);
        channel.port1.start();
        return channel.port1;
      }
      function request(port, payload, transfer = []) {
        return new Promise((resolve, reject) => {
          const id = crypto.randomUUID();
          const timeout = setTimeout(() => reject(Error('D18_KEYPORT_TIMEOUT')), 8000);
          function onMessage(event) {
            if (event.data?.id !== id) return;
            clearTimeout(timeout);
            port.removeEventListener('message', onMessage);
            resolve(event.data);
          }
          port.addEventListener('message', onMessage);
          port.postMessage({...payload, id}, transfer);
        });
      }
      const a = attach(worker);
      const challenge = 'D18-SYNTHETIC-CHALLENGE-20261102';
      let r = await request(a, {op:'proof',scope:scopeA,session:sessionA,challenge});
      insist('locked_before_unlock', r.code === 'LOCKED');
      const short = crypto.getRandomValues(new Uint8Array(16));
      r = await request(a, {
        op:'unlock',scope:scopeA,session:sessionA,key:short.buffer
      }, [short.buffer]);
      insist('reject_short_key', r.code === 'KEY_LENGTH');
      const raw = crypto.getRandomValues(new Uint8Array(32));
      const expectedKey = await crypto.subtle.importKey(
        'raw', raw, {name:'HMAC', hash:'SHA-256'}, false, ['sign']
      );
      r = await request(a, {
        op:'unlock',scope:scopeA,session:sessionA,key:raw.buffer
      }, [raw.buffer]);
      insist('unlock_dynamic_key', r.code === 'UNLOCKED');
      insist('sender_buffer_detached', raw.byteLength === 0);
      const expected = Array.from(new Uint8Array(
        await crypto.subtle.sign('HMAC', expectedKey,
          new TextEncoder().encode(challenge))
      ), b => b.toString(16).padStart(2,'0')).join('');
      r = await request(a, {op:'proof',scope:scopeA,session:sessionA,challenge});
      insist('worker_received_true_key', r.code === 'PROOF' && r.mac === expected);
      r = await request(a, {op:'proof',scope:scopeB,session:sessionA,challenge});
      insist('wrong_scope_denied', r.code === 'WRONG_SCOPE');
      r = await request(a, {op:'proof',scope:scopeA,session:sessionB,challenge});
      insist('wrong_session_denied', r.code === 'WRONG_SESSION');
      const b = attach(worker);
      r = await request(b, {op:'proof',scope:scopeA,session:sessionA,challenge});
      insist('other_port_denied', r.code === 'UNAUTHORIZED_PORT');
      const replay = crypto.getRandomValues(new Uint8Array(32));
      r = await request(a, {
        op:'unlock',scope:scopeA,session:sessionA,key:replay.buffer
      }, [replay.buffer]);
      insist('reunlock_denied', r.code === 'SESSION_ACTIVE');
      r = await request(a, {op:'lock',scope:scopeA,session:sessionA});
      insist('explicit_lock', r.code === 'LOCKED');
      r = await request(a, {op:'proof',scope:scopeA,session:sessionA,challenge});
      insist('locked_port_denied', r.code === 'LOCKED');
      const rawB = crypto.getRandomValues(new Uint8Array(32));
      const keyB = await crypto.subtle.importKey(
        'raw', rawB, {name:'HMAC',hash:'SHA-256'},false,['sign']
      );
      r = await request(b, {
        op:'unlock',scope:scopeB,session:sessionB,key:rawB.buffer
      }, [rawB.buffer]);
      insist('second_patient_unlock', r.code === 'UNLOCKED');
      r = await request(b, {op:'proof',scope:scopeB,session:sessionB,challenge});
      const expectedB = Array.from(new Uint8Array(
        await crypto.subtle.sign('HMAC',keyB,
          new TextEncoder().encode(challenge))
      ), byte => byte.toString(16).padStart(2,'0')).join('');
      insist('second_patient_key_distinct',
        r.code === 'PROOF' && r.mac === expectedB && r.mac !== expected);
      r = await request(a, {op:'proof',scope:scopeA,session:sessionA,challenge});
      insist('first_patient_cannot_reuse', r.code === 'UNAUTHORIZED_PORT');
      a.close(); b.close(); worker.terminate();
      const fresh = new Worker('/d18_session_handshake_probe_worker.js');
      const c = attach(fresh);
      r = await request(c, {op:'proof',scope:scopeB,session:sessionB,challenge});
      insist('new_worker_starts_locked', r.code === 'LOCKED');
      c.close(); fresh.terminate();
      return seen;
    });
    steps.push(...first);
    await page.close();
    await browser.close(); browser = null;
    browser = await chromium.launchPersistentContext(userData, {
      headless: true,locale:'fr-FR',
      args: ['--no-sandbox','--disable-dev-shm-usage']
    });
    const secondPage = await visit(browser);
    const afterRestart = await secondPage.evaluate(async () => {
      const worker = new Worker('/d18_session_handshake_probe_worker.js');
      const channel = new MessageChannel();
      worker.postMessage({type:'D18_ATTACH'},[channel.port2]);
      channel.port1.start();
      const id = crypto.randomUUID();
      const code = await new Promise((resolve,reject) => {
        const timeout = setTimeout(() => reject(Error('D18_RESTART_TIMEOUT')),8000);
        channel.port1.onmessage = event => {
          if (event.data?.id !== id) return;
          clearTimeout(timeout);
          resolve(event.data.code);
        };
        channel.port1.postMessage({
          id, op:'proof',
          scope:'amina_vault_v1_device_' + 'b'.repeat(32),
          session:'22222222-2222-4222-8222-222222222222',
          challenge:'D18-SYNTHETIC-CHALLENGE-20261102'
        });
      });
      channel.port1.close(); worker.terminate();
      return code;
    });
    steps.push({phase:'new_process_starts_locked',pass:afterRestart === 'LOCKED'});
  } catch (error) {
    // Explicitly never log keys, ports, or browser state.
    steps.push({phase:'harness',pass:false,error:String(error.message).slice(0,180)});
  } finally {
    if (browser) await browser.close();
    fs.rmSync(userData,{recursive:true,force:true});
  }
  const required = [
    'locked_before_unlock','reject_short_key','unlock_dynamic_key',
    'sender_buffer_detached','worker_received_true_key','wrong_scope_denied',
    'wrong_session_denied','other_port_denied','reunlock_denied',
    'explicit_lock','locked_port_denied','second_patient_unlock',
    'second_patient_key_distinct','first_patient_cannot_reuse',
    'new_worker_starts_locked','new_process_starts_locked'
  ];
  fs.mkdirSync('d18-keyport-proof',{recursive:true});
  fs.writeFileSync('d18-keyport-proof/report.json',JSON.stringify({
    head:process.env.GITHUB_SHA || null,steps
  },null,2));
  console.log(JSON.stringify(steps));
  if(steps.length !== required.length ||
     steps.some((s,i) => !s.pass || s.phase !== required[i])) process.exitCode = 1;
})().catch(error => {
  console.error('D18_KEYPORT_FATAL',error.name);
  process.exitCode = 1;
});
