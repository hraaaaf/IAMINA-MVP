'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createSessionFence } = require('../web/d1_research_session_fence.js');

const ORIGIN = 'https://iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app';
const CONTEXT_A = Object.freeze({
  authenticated: true, patientReady: false, origin: ORIGIN,
  accountId: '731', vaultOwner: 'amina_vault_v1_native_731',
  sessionStamp: 'a'.repeat(64), epoch: 3, credentialId: 'Y3JlZGVudGlhbC1B'
});
const CONTEXT_B = Object.freeze({
  ...CONTEXT_A, accountId: '812', vaultOwner: 'amina_vault_v1_native_812',
  sessionStamp: 'b'.repeat(64), credentialId: 'Y3JlZGVudGlhbC1C'
});
function key() { return Uint8Array.from({length: 32}, (_, i) => i + 1); }
function deferred() {
  let resolve, reject;
  const promise = new Promise((r, j) => { resolve = r; reject = j; });
  return {promise, resolve, reject};
}
function target() {
  const events = new Map();
  return {
    addEventListener(kind, fn) {
      if (!events.has(kind)) events.set(kind, new Set());
      events.get(kind).add(fn);
    },
    removeEventListener(kind, fn) { events.get(kind)?.delete(fn); },
    emit(kind, data) {
      for (const fn of events.get(kind) || []) fn(data);
    },
  };
}
function bus() {
  const peers = [];
  return () => {
    const peer = target();
    peer.postMessage = data => {
      for (const other of peers) if (other !== peer) other.emit('message', {data});
    };
    peers.push(peer);
    return peer;
  };
}
function setup({
  readServerSession = async () => CONTEXT_A,
  prfUnlock = async () => key(),
  channel = bus()(),
  lifecycle = target()
} = {}) {
  return createSessionFence({
    readServerSession, prfUnlock, expectedOrigin: ORIGIN, channel, lifecycle
  });
}

test('synthetic A: only server-supplied owner reaches PRF; key zeroed after use', async () => {
  let seenOwner, material, callbackCalled = false;
  const bridge = setup({prfUnlock: async owner => {
    seenOwner = owner; material = key(); return material;
  }});
  const status = await bridge.withUnlockedKey(async (dek, scope) => {
    callbackCalled = true;
    assert.equal(dek, material);
    assert.equal(scope.accountId, CONTEXT_A.accountId);
    assert.equal(scope.patientReady, false);
    assert.equal(dek[0], 1);
    return Uint8Array.from(dek); // result MUST NOT escape as a secret
  });
  assert.equal(seenOwner, CONTEXT_A.vaultOwner);
  assert.equal(callbackCalled, true);
  assert.deepEqual(status, {status: 'D1_RESEARCH_FIXTURE_COMPLETE', patientReady: false});
  assert.ok(material.every(n => n === 0));
});

test('foreign origin/invalid session/owner/credential rejected BEFORE PRF', async () => {
  for (const change of [
    {origin:'https://evil.example'},
    {authenticated:false},
    {patientReady:true},
    {vaultOwner:'amina_vault_v1_native_000'},
    {credentialId:'not valid base64'},
    {epoch:-1},
    {sessionStamp:'tampered'},
    {accountId:'000'},
  ]) {
    let called = 0;
    const bridge = setup({readServerSession:async()=>({...CONTEXT_A,...change}),
      prfUnlock:async()=>{called++;return key()}});
    await assert.rejects(bridge.withUnlockedKey(async()=>{}),/D1_RESEARCH_UNTRUSTED_SESSION/);
    assert.equal(called,0,JSON.stringify(change));
  }
});

test('missing authenticated session refuses before PRF', async () => {
  let calls=0;
  const bridge=setup({readServerSession:async()=>{throw Error('401')},
    prfUnlock:async()=>{calls++;return key()}});
  await assert.rejects(bridge.withUnlockedKey(async()=>{}),/D1_RESEARCH_SESSION_UNAVAILABLE/);
  assert.equal(calls,0);
});

test('A→B switch during Face ID: stale key wiped, callback forbidden', async () => {
  let context=CONTEXT_A;const pending=deferred();let called=false, held;
  const bridge=setup({readServerSession:async()=>context,
    prfUnlock:async()=>{held=await pending.promise;return held}});
  const operation=bridge.withUnlockedKey(async()=>{called=true});
  // Resolve the first authenticated read before switching the account.
  await Promise.resolve();await Promise.resolve();
  context=CONTEXT_B;
  held=key();pending.resolve(held);
  await assert.rejects(operation,/D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED|D1_RESEARCH_STALE_OPERATION/);
  assert.equal(called,false);assert.ok(held.every(n=>n===0));
});

test('same account with rotated Django session is refused and DEK zeroed', async () => {
  let n=0;const k=key();
  const bridge=setup({readServerSession:async()=>{
      n++;return n>=2?{...CONTEXT_A,sessionStamp:'f'.repeat(64)}:CONTEXT_A;
    },prfUnlock:async()=>k});
  await assert.rejects(bridge.withUnlockedKey(async()=>{throw Error('MUST_NOT_RUN')}),
    /D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED/);
  assert.ok(k.every(v=>v===0));
});

test('A→B→A: no reuse without explicit sessionChanged, each ceremony fresh', async () => {
  let current=CONTEXT_A,calls=0;
  const bridge=setup({readServerSession:async()=>current,
    prfUnlock:async owner=>{calls++;assert.equal(owner,current.vaultOwner);return key()}});
  await bridge.withUnlockedKey(async()=>{});
  current=CONTEXT_B;
  await assert.rejects(bridge.withUnlockedKey(async()=>{}),/D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED/);
  assert.equal(calls,1);
  bridge.sessionChanged();
  await bridge.withUnlockedKey(async()=>{});
  current=CONTEXT_A;
  await assert.rejects(bridge.withUnlockedKey(async()=>{}),/D1_RESEARCH_ACCOUNT_OR_SESSION_CHANGED/);
  assert.equal(calls,2);
  bridge.sessionChanged();
  await bridge.withUnlockedKey(async()=>{});
  assert.equal(calls,3);
});

test('logout event while Face ID is pending forbids late callback and wipes key', async () => {
  const pending=deferred();const reached=deferred();let called=false, held;
  const bridge=setup({prfUnlock:async()=>{reached.resolve();held=await pending.promise;return held}});
  const process=bridge.withUnlockedKey(async()=>{called=true});
  await reached.promise;
  bridge.sessionChanged();
  held=key();pending.resolve(held);
  await assert.rejects(process,/D1_RESEARCH_STALE_OPERATION/);
  assert.equal(called,false);assert.ok(held.every(n=>n===0));
});

test('logout event inside async fixture callback wipes DEK immediately', async () => {
  let held;const checkpoint=deferred();const done=deferred();
  const bridge=setup({prfUnlock:async()=>{held=key();return held}});
  const process=bridge.withUnlockedKey(async dek=>{
    assert.equal(dek,held);checkpoint.resolve();await done.promise;
  });
  await checkpoint.promise;
  bridge.sessionChanged();
  assert.ok(held.every(v=>v===0));
  done.resolve();
  await assert.rejects(process,/D1_RESEARCH_STALE_OPERATION/);
});

test('concurrent Face ID prompts fail closed, first operation cannot share a key', async () => {
  const reached=deferred(),slow=deferred();
  let calls=0,firstKey,firstUsed=false,secondUsed=false;
  const bridge=setup({prfUnlock:async()=>{
    calls++;reached.resolve();firstKey=await slow.promise;return firstKey;
  }});
  const first=bridge.withUnlockedKey(async()=>{firstUsed=true});
  await reached.promise;
  await assert.rejects(bridge.withUnlockedKey(async()=>{secondUsed=true}),
    /D1_RESEARCH_FENCE_BUSY/);
  firstKey=key();slow.resolve(firstKey);
  await first;
  assert.ok(firstKey.every(x=>x===0));
  assert.equal(calls,1);
  assert.equal(firstUsed,true);
  assert.equal(secondUsed,false);
});

test('invalid 16-byte or all-zero key material denied; bytes never retained', async () => {
  const k=new Uint8Array(16).fill(23);
  const bridge=setup({prfUnlock:async()=>k});
  await assert.rejects(bridge.withUnlockedKey(async()=>{}),/D1_RESEARCH_BAD_KEY_MATERIAL/);
  assert.ok(k.every(v=>v===0));
});

test('failed callback wipes key and never converts error into PASS', async () => {
  const k=key();const bridge=setup({prfUnlock:async()=>k});
  await assert.rejects(bridge.withUnlockedKey(async()=>{throw Error('fixture_failure')}),/fixture_failure/);
  assert.ok(k.every(v=>v===0));
});

test('destroy invalidates future sessions and destroys in-memory key', async () => {
  const b=setup();b.destroy();
  await assert.rejects(b.withUnlockedKey(async()=>{}),/D1_RESEARCH_FENCE_UNAVAILABLE/);
  b.sessionChanged(); // idempotent, no resurrection
  await assert.rejects(b.withUnlockedKey(async()=>{}),/D1_RESEARCH_FENCE_UNAVAILABLE/);
});

test('fails closed on missing mandatory client boundary implementations', () => {
  assert.throws(()=>createSessionFence({}),/D1_RESEARCH_FENCE_BAD_CONFIG/);
  assert.throws(()=>createSessionFence({
    readServerSession:async()=>CONTEXT_A,prfUnlock:async()=>key(),
    expectedOrigin:'http://localhost:3000'
  }),/D1_RESEARCH_FENCE_BAD_CONFIG/);
});

test('cross-tab logout invalidates an active DEK and aborts pending callback', async () => {
  const peers=bus();
  const aKey=key(), started=deferred(), release=deferred();
  const a=setup({channel:peers(),prfUnlock:async()=>aKey});
  const b=setup({channel:peers()});
  const operation=a.withUnlockedKey(async (dek, scope)=>{
    assert.equal(scope.patientReady,false);
    started.resolve();
    await release.promise;
    return dek.slice();
  });
  await started.promise;
  b.sessionChanged(); // explicit logout in separate same-origin tab
  assert.ok(aKey.every(x=>x===0));
  release.resolve();
  await assert.rejects(operation,/D1_RESEARCH_STALE_OPERATION/);
  a.destroy();b.destroy();
});

test('pagehide or BFCache restore invalidates delayed Face ID results', async () => {
  for (const [kind, metadata] of [
    ['pagehide',{}], ['pageshow',{persisted:true}]
  ]) {
    const life=target(), entered=deferred(), release=deferred();
    const dek=key();let invoked=false;
    const f=setup({
      lifecycle:life,
      prfUnlock:async()=>{entered.resolve();return release.promise}
    });
    const inFlight=f.withUnlockedKey(async()=>{invoked=true});
    await entered.promise;
    life.emit(kind, metadata);
    release.resolve(dek);
    await assert.rejects(inFlight,/D1_RESEARCH_STALE_OPERATION/);
    assert.equal(invoked,false);
    assert.ok(dek.every(x=>x===0));
    f.destroy();
  }
});

test('cross-tab foreign origin events cannot impersonate a logout', async () => {
  const peers=bus(), sender=peers(), recipient=peers();
  let calls=0;
  const f=setup({channel:recipient,prfUnlock:async()=>{calls++;return key()}});
  sender.postMessage({
    type:'IAMINA_D1_RESEARCH_INVALIDATE_V1',origin:'https://foreign.invalid'
  });
  await f.withUnlockedKey(async()=>{});
  assert.equal(calls,1);
  f.destroy();
});

test('offline identity check fails closed without attempting PRF', async () => {
  let calls=0;
  const f=setup({
    readServerSession:async()=>{throw Error('network offline')},
    prfUnlock:async()=>{calls++;return key()}
  });
  await assert.rejects(f.withUnlockedKey(async()=>{}),
    /D1_RESEARCH_SESSION_UNAVAILABLE/);
  assert.equal(calls,0);
  f.destroy();
});

test('invalid channel or lifecycle fails closed', () => {
  assert.throws(()=>createSessionFence({
    readServerSession:async()=>CONTEXT_A,
    prfUnlock:async()=>key(),expectedOrigin:ORIGIN,
    channel:null,lifecycle:target()
  }),/D1_RESEARCH_FENCE_BAD_CONFIG/);
  assert.throws(()=>createSessionFence({
    readServerSession:async()=>CONTEXT_A,
    prfUnlock:async()=>key(),expectedOrigin:ORIGIN,
    channel:bus()(),lifecycle:null
  }),/D1_RESEARCH_FENCE_BAD_CONFIG/);
});

test('destroy unregisters lifecycle callbacks and never allows resurrection', async () => {
  const life=target(), b=setup({lifecycle:life});
  b.destroy();
  life.emit('pagehide',{});
  life.emit('pageshow',{persisted:true});
  await assert.rejects(b.withUnlockedKey(async()=>{}),
    /D1_RESEARCH_FENCE_UNAVAILABLE/);
});
