'use strict';
/* All tests use generated synthetic WebCrypto ECDSA assertions and a simulated
 * Django route. Real Django py_webauthn checks run in the separate Python job.
 * No actual browser/Face ID, patient vault or Vercel endpoint is invoked. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
const {createSignedPrfBridge,sealSyntheticFixture,openSyntheticFixture} =
  require('../web/d1_signed_prf_synthetic_research.js');
const subtle = webcrypto.subtle;
const ORIGIN='https://iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app';
const HOST=new URL(ORIGIN).hostname;
const CID=encode(new TextEncoder().encode('d1-generated-credential-a'));
const CSRF='x'.repeat(32);
function encode(bytes) {
  return Buffer.from(bytes).toString('base64url');
}
function decode(s) {return new Uint8Array(Buffer.from(s,'base64url'))}
function cloneBuf(bytes) {
  return Uint8Array.from(bytes).buffer;
}
function scoped(account='731') {
  return {
    authenticated:true,patientReady:false,accountId:account,
    vaultOwner:'amina_vault_v1_native_'+account,epoch:1,
    sessionStamp:(account==='731'?'a':'b').repeat(64),
    credentialId:CID,origin:ORIGIN,
  };
}
function resp(status,body) {
  return {status,redirected:false,json:async()=>body};
}
async function fixture(options={}) {
  const signing=await subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},
    true,['sign','verify']);
  const prfHmac=await subtle.importKey('raw',Uint8Array.from({length:32},(_,i)=>i+1),
    {name:'HMAC',hash:'SHA-256'},false,['sign']);
  const state={account:'731',cookieValid:true,epoch:1,requests:[],prompts:0,
    finishCount:0,issued:null,cancel:false,badOrigin:false,signatureInvalid:false,
    uvMissing:false,noPrf:false,wrongCredential:false,finishDenied:false,
    offline:false,changeAccountOnFinish:false,afterCallback:null};
  const server=async(path,req)=>{
    if(state.offline) throw Error('offline');
    assert.equal(req.credentials,'same-origin');
    assert.equal(req.mode,'same-origin');
    assert.equal(req.redirect,'error');
    assert.equal(req.headers['X-CSRFToken'],CSRF);
    assert.equal(req.headers['Content-Type'],'application/json');
    assert.ok(path.startsWith('/api/v1/d1-research/passkey/'));
    const body=JSON.parse(req.body);
    state.requests.push({path,body});
    if(!state.cookieValid) return resp(401,{detail:'unauthorized'});
    if(state.account!=='731') return resp(403,{detail:'foreign credential'});
    if(path.endsWith('/session-context'))
      return resp(body.credential_id===CID?200:403,scoped(state.account));
    if(path.endsWith('/verify/start')){
      if(body.credential_id!==CID) return resp(403,{});
      const challenge=webcrypto.getRandomValues(new Uint8Array(32));
      state.issued={id:'d1-synthetic-'+(state.finishCount+1),challenge,used:false};
      return resp(200,{ceremony_id:state.issued.id,options:{
        rpId:HOST,challenge:encode(challenge),
        userVerification:'required',timeout:120000,
        allowCredentials:[{type:'public-key',id:CID}]
      }});
    }
    if(path.endsWith('/verify/finish')){
      state.finishCount++;
      if(state.finishDenied || state.changeAccountOnFinish) return resp(403,{});
      const issued=state.issued;
      if(!issued || issued.used || issued.id!==body.ceremony_id ||
          body.credential?.id!==CID) return resp(403,{});
      issued.used=true;
      const {response}=body.credential;
      const cd=decode(response.clientDataJSON);
      let details;
      try{details=JSON.parse(Buffer.from(cd).toString('utf8'))}catch{return resp(403,{})}
      if(details.type!=='webauthn.get' || details.origin!==ORIGIN ||
          details.challenge!==encode(issued.challenge)) return resp(403,{});
      const ad=decode(response.authenticatorData);
      if(ad.length!==37 || (ad[32]&5)!==5) return resp(403,{});
      const hash=await subtle.digest('SHA-256',new TextEncoder().encode(HOST));
      if(!Buffer.from(hash).equals(Buffer.from(ad.subarray(0,32))))return resp(403,{});
      const cdHash=new Uint8Array(await subtle.digest('SHA-256',cd));
      const message=Buffer.concat([Buffer.from(ad),Buffer.from(cdHash)]);
      const isValid=await subtle.verify({name:'ECDSA',hash:'SHA-256'},
        signing.publicKey,decode(response.signature),message);
      if(!isValid)return resp(403,{});
      return resp(200,{status:'ASSERTION_VERIFIED_RESEARCH_ONLY',patient_ready:false});
    }
    throw Error('unrecognized route');
  };
  const get=async({publicKey,signal})=>{
    state.prompts++;
    if(state.cancel)throw Error('NotAllowedError');
    if(signal?.aborted)throw Error('AbortError');
    assert.equal(publicKey.rpId,HOST);
    assert.equal(publicKey.userVerification,'required');
    assert.equal(encode(publicKey.challenge),encode(state.issued.challenge));
    assert.equal(encode(publicKey.allowCredentials[0].id),CID);
    const ad=new Uint8Array(37),rpHash=await subtle.digest('SHA-256',
      new TextEncoder().encode(HOST));
    ad.set(new Uint8Array(rpHash),0);
    ad[32]=state.uvMissing?1:5;ad[36]=state.finishCount+1;
    const clientData=new TextEncoder().encode(JSON.stringify({
      type:'webauthn.get',challenge:encode(publicKey.challenge),
      origin:state.badOrigin?'https://evil.invalid':ORIGIN,crossOrigin:false
    }));
    const hashed=new Uint8Array(await subtle.digest('SHA-256',clientData));
    const message=Buffer.concat([Buffer.from(ad),Buffer.from(hashed)]);
    let signature=new Uint8Array(await subtle.sign({name:'ECDSA',hash:'SHA-256'},
      signing.privateKey,message));
    if(state.signatureInvalid)signature[0]^=0x80;
    const prfOut=new Uint8Array(await subtle.sign('HMAC',prfHmac,
      publicKey.extensions.prf.eval.first));
    state.lastPrf=prfOut;
    return {
      id:CID,type:'public-key',
      rawId:cloneBuf(state.wrongCredential?new TextEncoder().encode('B'):decode(CID)),
      response:{authenticatorData:cloneBuf(ad),clientDataJSON:cloneBuf(clientData),
        signature:cloneBuf(signature),userHandle:null},
      getClientExtensionResults:()=>state.noPrf?{}:
        {prf:{results:{first:prfOut.buffer}}}
    };
  };
  const bridge=createSignedPrfBridge({fetchImpl:server,credentialsGet:get,
    cryptoImpl:webcrypto,csrfToken:()=>CSRF,origin:ORIGIN});
  const salt=webcrypto.getRandomValues(new Uint8Array(16));
  const input=webcrypto.getRandomValues(new Uint8Array(32));
  return {bridge,state,salt,input};
}

test('same signed assertion verifies server, derives nonextractable KEK and opens synthetic AES-GCM vault',async()=>{
  const {bridge,state,salt,input}=await fixture();
  let envelope;
  const first=await bridge.withVerifiedPrf({credentialId:CID,prfInput:input,salt,
    callback:async({kek,scope})=>{
      assert.equal(kek.extractable,false);
      envelope=await sealSyntheticFixture({cryptoImpl:webcrypto,kek,scope,prfInput:input,salt});
    }});
  assert.deepEqual(first,{status:'D1_SIGNED_PRF_SYNTHETIC_COMPLETE',patientReady:false});
  assert.equal(state.prompts,1);
  assert.equal(state.finishCount,1);
  assert.ok(state.lastPrf.every(x=>x===0),'the browser output view is wiped');
  assert.ok(envelope.wrappedDEK && envelope.ciphertext);
  assert.ok(!JSON.stringify(envelope).includes('IAMINA_D1_SYNTHETIC_VAULT_ONLY'));
  let opened;
  const second=await bridge.withVerifiedPrf({credentialId:CID,prfInput:decode(envelope.prfInput),
    salt:decode(envelope.salt),callback:async({kek,scope})=>{
      opened=await openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,envelope});
    }});
  assert.equal(second.patientReady,false);
  assert.deepEqual(opened,{status:'SYNTHETIC_VAULT_OPENED',patientReady:false});
  assert.equal(state.finishCount,2);
  assert.equal(state.prompts,2); // exactly one assertion per ceremony, no local challenge
  for(const record of state.requests){
    const wire=JSON.stringify(record.body);
    assert.ok(!wire.includes('"prf"'),'PRF extension never on Django wire');
    assert.ok(!wire.includes('prfInput'),'PRF input only local');
    assert.ok(!wire.includes('wrappedDEK'),'encrypted envelope never on Django wire');
    assert.ok(!wire.includes('"kek"') && !wire.includes('"dek"'));
  }
});

test('real ECDSA simulator: altered signature is refused by server before KEK callback',async()=>{
  const f=await fixture();f.state.signatureInvalid=true;
  let called=false;
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{called=true}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
  assert.equal(called,false);assert.equal(f.state.finishCount,1);
});

test('Face ID cancellation never calls verify/finish or unlock callback',async()=>{
  const f=await fixture();f.state.cancel=true;
  let called=false;
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{called=true}}),/NotAllowedError/);
  assert.equal(called,false);assert.equal(f.state.finishCount,0);
});

test('missing PRF output refuses even a signed user-verifying assertion',async()=>{
  const f=await fixture();f.state.noPrf=true;
  let called=false;
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{called=true}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
  assert.equal(called,false);assert.equal(f.state.finishCount,0);
});

test('bad origin, missing UV and wrong credential refuse before HTTP verification',async()=>{
  for(const flag of ['badOrigin','uvMissing','wrongCredential']){
    const f=await fixture();f.state[flag]=true;
    await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
      salt:f.salt,callback:async()=>{throw Error('NEVER')}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
    assert.equal(f.state.finishCount,0,flag);
  }
});

test('server denial, session A→B and offline fail closed before KEK creation',async()=>{
  for(const flag of ['finishDenied','changeAccountOnFinish','offline']){
    const f=await fixture();f.state[flag]=true;let called=false;
    await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
      salt:f.salt,callback:async()=>{called=true}}));
    assert.equal(called,false,flag);
  }
  const f=await fixture();f.state.account='812';
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{throw Error('NEVER')}}),
    /D1_SIGNED_PRF_RESEARCH_DENIED/);
  assert.equal(f.state.prompts,0);
});

test('post-signature account rotation prevents successful completion',async()=>{
  const f=await fixture();
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{f.state.account='812'}}),
    /D1_SIGNED_PRF_RESEARCH_DENIED/);
});

test('tampered synthetic vault, wrong owner, and foreign credential cannot decrypt',async()=>{
  const f=await fixture();let envelope,scopeAtSeal;
  await f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,salt:f.salt,
    callback:async({kek,scope})=>{
      scopeAtSeal=scope;
      envelope=await sealSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        prfInput:f.input,salt:f.salt});
    }});
  await f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,salt:f.salt,
    callback:async({kek,scope})=>{
      await assert.rejects(openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        envelope:{...envelope,accountId:'812'}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
      await assert.rejects(openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        envelope:{...envelope,credentialId:'Yg'}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
      await assert.rejects(openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        envelope:{...envelope,ciphertext:'YQ'}}));
    }});
  assert.equal(scopeAtSeal.accountId,'731');
});

test('missing CSRF token and malformed configuration fail closed',async()=>{
  assert.throws(()=>createSignedPrfBridge({}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
  const f=await fixture();
  const bad=createSignedPrfBridge({fetchImpl:async()=>{throw Error('SHOULD_NOT_SEND')},
    credentialsGet:async()=>{throw Error('NEVER')},cryptoImpl:webcrypto,
    csrfToken:()=>'',origin:ORIGIN});
  await assert.rejects(bad.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
});

test('wrong proof status or missing patientReady=false is not authorization',async()=>{
  const f=await fixture();f.state.finishDenied=true;
  await assert.rejects(f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,
    salt:f.salt,callback:async()=>{throw Error('NEVER')}}),
    /D1_SIGNED_PRF_RESEARCH_DENIED/);
});

function eventTarget(){
  const subscriptions=new Map();
  return {
    addEventListener(event,handler){
      if(!subscriptions.has(event))subscriptions.set(event,new Set());
      subscriptions.get(event).add(handler);
    },
    removeEventListener(event,handler){subscriptions.get(event)?.delete(handler)},
    dispatch(event,data){
      for(const handler of subscriptions.get(event)||[]) handler(data);
    }
  };
}
function fakeChannel(){
  const target=eventTarget();
  return {...target,postMessage(){ /* Single-tab fixture; no external traffic */ }};
}

test('single session fence wraps signed Django proof + PRF-encrypted fixture before synthetic operation',async()=>{
  const {createSessionFence}=require('../web/d1_research_session_fence.js');
  const f=await fixture();
  let envelope;
  await f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,salt:f.salt,
    callback:async({kek,scope})=>{
      envelope=await sealSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        prfInput:f.input,salt:f.salt});
    }});
  let opened=false, grant;
  const fence=createSessionFence({
    readServerSession:()=>f.bridge.context(CID),
    expectedOrigin:ORIGIN,
    channel:fakeChannel(),lifecycle:eventTarget(),
    prfUnlock:async(owner,{signal})=>{
      await f.bridge.withVerifiedPrf({credentialId:CID,
        prfInput:decode(envelope.prfInput),salt:decode(envelope.salt),signal,
        callback:async({kek,scope})=>{
          assert.equal(scope.vaultOwner,owner);
          const check=await openSyntheticFixture({
            cryptoImpl:webcrypto,kek,scope,envelope
          });
          opened=check.status==='SYNTHETIC_VAULT_OPENED';
        }});
      // A random 32-byte TEST GRANT, deliberately not the DEK. The single
      // fence contract is tested; no patient key is exposed to the callback.
      if(!opened)throw Error('RESEARCH_FIXTURE_NOT_OPENED');
      grant=webcrypto.getRandomValues(new Uint8Array(32));
      return grant;
    }
  });
  let invoked=false;
  const result=await fence.withUnlockedKey(async(bytes,scope)=>{
    invoked=true;
    assert.equal(scope.accountId,'731');
    assert.equal(bytes,grant);
  });
  assert.equal(result.status,'D1_RESEARCH_FIXTURE_COMPLETE');
  assert.equal(opened,true);
  assert.equal(invoked,true);
  assert.equal(f.state.prompts,2); // enrollment + one unlock assertion
  assert.ok(grant.every(x=>x===0));
  fence.destroy();
});

test('fence + signed PRF bridge never reassigns A envelope to B or restores old session',async()=>{
  const {createSessionFence}=require('../web/d1_research_session_fence.js');
  const f=await fixture();let envelope;
  await f.bridge.withVerifiedPrf({credentialId:CID,prfInput:f.input,salt:f.salt,
    callback:async({kek,scope})=>{
      envelope=await sealSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        prfInput:f.input,salt:f.salt});
    }});
  let unlocked=0;
  const fence=createSessionFence({
    readServerSession:()=>f.bridge.context(CID),
    expectedOrigin:ORIGIN,channel:fakeChannel(),lifecycle:eventTarget(),
    prfUnlock:async(owner,{signal})=>{
      await f.bridge.withVerifiedPrf({credentialId:CID,
        prfInput:decode(envelope.prfInput),salt:decode(envelope.salt),signal,
        callback:async({kek,scope})=>{
          assert.equal(scope.vaultOwner,owner);
          const ok=await openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,envelope});
          assert.equal(ok.status,'SYNTHETIC_VAULT_OPENED');
        }});
      return webcrypto.getRandomValues(new Uint8Array(32));
    }
  });
  await fence.withUnlockedKey(async()=>{unlocked++});
  f.state.account='812';
  await assert.rejects(fence.withUnlockedKey(async()=>{unlocked++}));
  fence.sessionChanged();
  await assert.rejects(fence.withUnlockedKey(async()=>{unlocked++}));
  f.state.account='731';
  // An explicit new operation after account restoration requires a fresh,
  // separately signed challenge; previous grant is zeroized.
  await fence.withUnlockedKey(async()=>{unlocked++});
  assert.equal(unlocked,2);
  assert.equal(f.state.prompts,3); // initial sealed + two valid fresh unlocks
  fence.destroy();
});
