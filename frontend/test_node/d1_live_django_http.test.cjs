'use strict';
/* LIVE Django localhost interop: Node-generated ES256 assertions, simulated PRF,
 * real Django session cookies, CSRF, challenges and py_webauthn signature checks.
 * No physical authenticator, browser, Face ID, patient data or deployment.
 * Runner-only fixture files contain synthetic secrets; never log their content.
 */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {webcrypto,createPrivateKey,sign,createHmac}=require('node:crypto');
const {
  createSignedPrfBridge,sealSyntheticFixture,openSyntheticFixture
}=require('../web/d1_signed_prf_synthetic_research.js');
const fixtures=JSON.parse(fs.readFileSync(process.env.D1_SESSIONS_JSON,'utf8'));
const keys=JSON.parse(fs.readFileSync(process.env.D1_KEYS_JSON,'utf8'));
const signingKey=createPrivateKey({key:keys.key,format:'jwk'});
const ORIGIN=fixtures.origin;
const HOST=new URL(ORIGIN).hostname;
const CID=fixtures.credential_id;
const CSRF_NAME='X-CSRFToken';
const encoder=new TextEncoder();
const BASE='http://127.0.0.1:8765';
const b64=bytes=>Buffer.from(bytes).toString('base64url');
const rand=n=>webcrypto.getRandomValues(new Uint8Array(n));
const localPrfSecret=rand(32);
let counter=0;
let cookieSession='a';
let tamperSignature=false;
let forceCancel=false;
let prompts=0;
const recorded=[];

function credentialsGet({publicKey,signal}) {
  prompts++;
  if(forceCancel)throw new Error('NotAllowedError');
  if(signal?.aborted)throw new Error('AbortError');
  assert.equal(publicKey.rpId,HOST);
  assert.equal(publicKey.userVerification,'required');
  const ad=new Uint8Array(37);
  const authenticatorHash=require('node:crypto').createHash('sha256').update(HOST).digest();
  ad.set(authenticatorHash,0);
  ad[32]=0x05;
  const n=++counter;
  ad[33]=(n>>>24)&255;ad[34]=(n>>>16)&255;ad[35]=(n>>>8)&255;ad[36]=n&255;
  const clientData=encoder.encode(JSON.stringify({
    type:'webauthn.get',origin:ORIGIN,crossOrigin:false,
    challenge:b64(publicKey.challenge)
  }));
  const sha=require('node:crypto').createHash('sha256').update(clientData).digest();
  const signed=sign('sha256',Buffer.concat([ad,sha]),signingKey);
  if(tamperSignature)signed[signed.length-1]^=0x01;
  const prf=createHmac('sha256',localPrfSecret)
    .update(publicKey.extensions.prf.eval.first).digest();
  return Promise.resolve({
    id:CID,type:'public-key',
    rawId:Uint8Array.from(Buffer.from(CID,'base64url')).buffer,
    response:{
      authenticatorData:Uint8Array.from(ad).buffer,
      clientDataJSON:Uint8Array.from(clientData).buffer,
      signature:Uint8Array.from(signed).buffer,
      userHandle:null
    },
    getClientExtensionResults:()=>({
      prf:{results:{first:Uint8Array.from(prf).buffer}}
    })
  });
}
async function transport(path,options){
  assert.ok(path.startsWith('/api/v1/d1-research/passkey/'));
  assert.equal(options.credentials,'same-origin');
  assert.equal(options.redirect,'error');
  assert.equal(options.method,'POST');
  const auth=fixtures[cookieSession];
  const headers={...options.headers,Cookie:auth.cookie};
  const url=BASE+path;
  const body=JSON.parse(options.body);
  recorded.push({path,body,status:null});
  const response=await fetch(url,{method:'POST',headers,
    body:options.body,redirect:'manual',signal:options.signal});
  recorded[recorded.length-1].status=response.status;
  return response;
}
function bridge(){
  return createSignedPrfBridge({
    fetchImpl:transport,credentialsGet,cryptoImpl:webcrypto,
    csrfToken:()=>fixtures[cookieSession].csrf,origin:ORIGIN
  });
}
function checkWire(){
  for(const req of recorded){
    const body=JSON.stringify(req.body);
    for(const restricted of ['prfInput','wrappedDEK','"prf"','"kek"','"dek"','privateKey'])
      assert.equal(body.includes(restricted),false,'secret on live Django wire');
  }
}

test('LIVE HTTP: Django cookie+CSRF+challenge ↔ real ES256 verify ↔ PRF fixture AES-GCM vault',async()=>{
  cookieSession='a';
  let envelope,account;
  const client=bridge();
  const input=rand(32),salt=rand(16);
  await client.withVerifiedPrf({credentialId:CID,prfInput:input,salt,
    callback:async({kek,scope})=>{
      account=scope.accountId;
      envelope=await sealSyntheticFixture({cryptoImpl:webcrypto,kek,scope,
        prfInput:input,salt});
    }});
  let opened;
  await client.withVerifiedPrf({credentialId:CID,
    prfInput:Uint8Array.from(Buffer.from(envelope.prfInput,'base64url')),
    salt:Uint8Array.from(Buffer.from(envelope.salt,'base64url')),
    callback:async({kek,scope})=>{
      opened=await openSyntheticFixture({cryptoImpl:webcrypto,kek,scope,envelope});
    }});
  assert.equal(opened.status,'SYNTHETIC_VAULT_OPENED');
  assert.equal(account,'1');
  assert.equal(prompts,2);
  checkWire();
  assert.ok(recorded.some(x=>x.path.endsWith('/verify/finish')&&x.status===200));
});

test('LIVE HTTP: forged ES256 signature denied by real Django verifier',async()=>{
  cookieSession='a';tamperSignature=true;
  const input=rand(32),salt=rand(16);let callback=false;
  try{
    await assert.rejects(bridge().withVerifiedPrf({credentialId:CID,prfInput:input,salt,
      callback:async()=>{callback=true}}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
    assert.equal(callback,false);
  }finally{tamperSignature=false}
  checkWire();
});

test('LIVE HTTP: replay of a valid signed payload is rejected',async()=>{
  cookieSession='a';
  const record=[...recorded].reverse().find(x=>
    x.path.endsWith('/verify/finish')&&x.status===200);
  assert.ok(record);
  const auth=fixtures.a;
  const replay=await fetch(BASE+record.path,{
    method:'POST',
    headers:{'Content-Type':'application/json',[CSRF_NAME]:auth.csrf,Cookie:auth.cookie},
    body:JSON.stringify(record.body)
  });
  assert.equal(replay.status,403);
});

test('LIVE HTTP: account B cannot use A credential; new A session demands fresh ceremony',async()=>{
  cookieSession='b';
  const before=prompts;
  await assert.rejects(bridge().withVerifiedPrf({credentialId:CID,
    prfInput:rand(32),salt:rand(16),callback:async()=>{
      throw Error('FOREIGN_OWNER_MUST_NOT_OPEN');
    }}),/D1_SIGNED_PRF_RESEARCH_DENIED/);
  assert.equal(prompts,before);
  cookieSession='a_again';
  const returned=bridge();
  let success=false;
  await returned.withVerifiedPrf({credentialId:CID,
    prfInput:rand(32),salt:rand(16),
    callback:async()=>{success=true}});
  assert.equal(success,true);
  assert.equal(prompts,before+1);
  checkWire();
});

test('LIVE HTTP: no CSRF / contradictory bearer / no cookie fail before signature',async()=>{
  cookieSession='a';
  const endpoint=BASE+'/api/v1/d1-research/passkey/session-context';
  const body=JSON.stringify({credential_id:CID});
  const auth=fixtures.a;
  const cases=[
    {'Content-Type':'application/json',Cookie:auth.cookie},
    {'Content-Type':'application/json',Cookie:auth.cookie,
      [CSRF_NAME]:auth.csrf,Authorization:'Bearer fabricated'},
    {'Content-Type':'application/json',[CSRF_NAME]:auth.csrf}
  ];
  for(const headers of cases){
    const r=await fetch(endpoint,{method:'POST',headers,body});
    assert.ok([401,403].includes(r.status),'expected HTTP rejection: '+r.status);
  }
});

test('LIVE HTTP: simulated Face ID cancellation sends no verify/finish',async()=>{
  cookieSession='a';forceCancel=true;
  const before=recorded.filter(x=>x.path.endsWith('/verify/finish')).length;
  let callback=false;
  try{
    await assert.rejects(bridge().withVerifiedPrf({credentialId:CID,
      prfInput:rand(32),salt:rand(16),callback:async()=>{callback=true}}),
      /NotAllowedError/);
    assert.equal(callback,false);
    assert.equal(recorded.filter(x=>x.path.endsWith('/verify/finish')).length,before);
  }finally{forceCancel=false}
});
