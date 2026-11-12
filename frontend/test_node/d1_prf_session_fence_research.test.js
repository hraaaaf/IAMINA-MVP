'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {create} = require('../web/d1_prf_session_fence_research.js');

const origin='https://fixture.example';
const bytes=Array.from({length:32},(_,i)=>i+1);
const principal=(extra={})=>({
  authenticated:true,accountId:'731',owner:'amina_vault_v1_native_731',
  sessionBinding:'a'.repeat(64),accountEpoch:1,credentialId:'YQ',origin,...extra,
});
function target(){
  const events=new Map();
  return {
    addEventListener(k,f){if(!events.has(k))events.set(k,new Set());events.get(k).add(f);},
    removeEventListener(k,f){events.get(k)?.delete(f);},
    emit(k,data){for(const f of events.get(k)||[])f(data);},
  };
}
function bus(){
  const peers=[];
  return ()=>{
    const x=target();
    x.postMessage=data=>{for(const p of peers)if(p!==x)p.emit('message',{data});};
    peers.push(x);return x;
  };
}
function setup(options={}){
  const life=target(),channel=(options.channelFactory||bus())();
  let current=principal(),key,reads=0;
  const gate={unlock:async owner=>{
    assert.equal(owner,'amina_vault_v1_native_731');
    if(options.unlock)return options.unlock();
    key=Uint8Array.from(bytes);return key;
  }};
  const fence=create({origin,lifecycle:life,channel,gate,
    getVerifiedScope:async()=>{
      reads++;
      if(options.read)return options.read();
      return current;
    },
  });
  return {fence,life,key:()=>key,reads:()=>reads,scope:s=>{current=s;}};
}
const wiped=key=>assert.deepEqual([...key],Array(32).fill(0));

test('positive synthetic scope before/after/callback, zeroize',async()=>{
  const h=setup();
  assert.equal(await h.fence.readOnly(async(key,scope)=>{
    assert.deepEqual([...key],bytes);
    assert.equal(scope.accountId,'731');
    return 'SYNTHETIC_MATCH';
  }),'SYNTHETIC_MATCH');
  assert.equal(h.reads(),3);wiped(h.key());h.fence.close();
});

test('Face ID result after logout is rejected and zeroed',async()=>{
  let resolve;
  const key=Uint8Array.from(bytes);
  const h=setup({unlock:()=>new Promise(r=>{resolve=r;})});
  let ran=false;
  const task=h.fence.readOnly(()=>{ran=true;return 'UNSAFE';});
  await new Promise(setImmediate);
  h.fence.invalidate();resolve(key);
  await assert.rejects(task,/D1_RESEARCH_SESSION_FENCE_DENIED/);
  assert.equal(ran,false);wiped(key);h.fence.close();
});

test('A to B after WebAuthn before callback fails without broadcast',async()=>{
  const life=target(),channel=bus()();
  let current=principal(),key,ran=false;
  const gate={unlock:async()=>{
    key=Uint8Array.from(bytes);
    current=principal({accountId:'812',owner:'amina_vault_v1_native_812',sessionBinding:'b'.repeat(64)});
    return key;
  }};
  const fence=create({getVerifiedScope:async()=>current,gate,origin,channel,lifecycle:life});
  await assert.rejects(fence.readOnly(()=>{ran=true;}),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  assert.equal(ran,false);wiped(key);fence.close();
});

test('account epoch change during work denies result',async()=>{
  const h=setup();
  await assert.rejects(h.fence.readOnly(async()=>{
    h.scope(principal({accountEpoch:2}));
    return 'STALE';
  }),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  wiped(h.key());h.fence.close();
});

test('another tab broadcasts logout and aborts active key',async()=>{
  const channelFactory=bus(),a=setup({channelFactory}),b=setup({channelFactory});
  let borrowed;
  await assert.rejects(a.fence.readOnly(async key=>{
    borrowed=key;b.fence.invalidate();return 'STALE';
  }),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  wiped(borrowed);a.fence.close();b.fence.close();
});

test('pagehide and restored BFCache deny delayed PRF result',async()=>{
  for(const kind of ['pagehide','pageshow']){
    let resolve;const key=Uint8Array.from(bytes);
    const h=setup({unlock:()=>new Promise(r=>{resolve=r;})});
    let ran=false;
    const promise=h.fence.readOnly(()=>{ran=true;});
    await new Promise(setImmediate);
    h.life.emit(kind,kind==='pageshow'?{persisted:true}:{});
    resolve(key);
    await assert.rejects(promise,/D1_RESEARCH_SESSION_FENCE_DENIED/);
    assert.equal(ran,false);wiped(key);h.fence.close();
  }
});

test('anonymous/foreign origin/bad epoch/invalid scope and offline deny',async()=>{
  for(const invalid of [
    {authenticated:false},{origin:'https://foreign.example'},
    {credentialId:''},{sessionBinding:'wrong'},{accountEpoch:-1},
  ]){
    let called=false;
    const h=setup({read:async()=>principal(invalid),unlock:async()=>{called=true;return Uint8Array.from(bytes);}});
    await assert.rejects(h.fence.readOnly(()=>null),/D1_RESEARCH_SESSION_FENCE_DENIED/);
    assert.equal(called,false);h.fence.close();
  }
  const offline=setup({read:async()=>{throw Error('offline');}});
  await assert.rejects(offline.fence.readOnly(()=>null),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  offline.fence.close();
});

test('concurrent Face ID prompts denied, cancellation does not release key',async()=>{
  let resolve;const h=setup({unlock:()=>new Promise(r=>{resolve=r;})});
  const promise=h.fence.readOnly(()=> 'OK');
  await new Promise(setImmediate);
  await assert.rejects(h.fence.readOnly(()=> 'CONCURRENT'),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  resolve(Uint8Array.from(bytes));
  assert.equal(await promise,'OK');h.fence.close();
  let ran=false;
  const cancel=setup({unlock:async()=>{throw Error('NotAllowedError');}});
  await assert.rejects(cancel.fence.readOnly(()=>{ran=true;}),/NotAllowedError/);
  assert.equal(ran,false);cancel.fence.close();
});

test('raw byte-array returns blocked and actual gate key zeroed',async()=>{
  const h=setup();
  await assert.rejects(h.fence.readOnly(key=>key.slice()),/D1_RESEARCH_SESSION_FENCE_DENIED/);
  wiped(h.key());h.fence.close();
});

test('absent cross-tab channel fails closed',()=>{
  assert.throws(()=>create({
    getVerifiedScope:async()=>principal(),gate:{unlock(){return null;}},
    origin,channel:null,lifecycle:target(),
  }),/D1_RESEARCH_SESSION_FENCE_DENIED/);
});
