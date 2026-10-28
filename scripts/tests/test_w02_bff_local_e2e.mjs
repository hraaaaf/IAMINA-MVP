import test from 'node:test';
import assert from 'node:assert/strict';
import { Readable, Writable } from 'node:stream';
import { proxy } from '../../frontend/api/preview-proxy.js';

const WEB = 'iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app';
const API = 'https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app';
const SQL_ID = {
  database_name: 'iamina925_empty',
  role_name: 'iamina_preview_app',
  neon_project_id: 'noisy-truth-00115950',
  neon_branch_id: 'br-sweet-frog-b9ok6ptp',
};
function json(code, value) {
  return new Response(JSON.stringify(value), {
    status: code, headers: {'content-type': 'application/json'},
  });
}
function output() {
  const chunks = [];
  const res = new Writable({write(x, _, cb) {chunks.push(Buffer.from(x));cb();}});
  res.statusCode = 200;
  res.headers = {};
  res.status = n => {res.statusCode=n;return res;};
  res.setHeader = (k,v) => {res.headers[k.toLowerCase()]=v;return res;};
  res.text = () => Buffer.concat(chunks).toString('utf8');
  return res;
}
test('W02 BFF local synthetic A-B-A with fail-closed SQL preflight and erasure', async () => {
  const keys=['VERCEL_ENV','VERCEL_PROJECT_ID','IAMINA_REVIEW_PREVIEW_API_BASE_URL',
    'IAMINA_W02_REMOTE_E2E_ENABLED'];
  const saved=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
  const oldFetch=globalThis.fetch;
  const users=new Map(), bearer=new Map();
  let id=1, generation=1, attest=0;
  async function send(path,method='GET',payload=null,token=null) {
    const request=Readable.from(payload===null?[]:[Buffer.from(JSON.stringify(payload))]);
    request.method=method;
    request.url='/api/v1/'+path;
    request.query={path};
    request.headers={
      host:WEB,
      ...(method==='GET'?{}:{origin:'https://'+WEB,'content-type':'application/json'}),
      ...(token?{authorization:'Bearer '+token}:{}),
      cookie:'_vercel_jwt=never-forward',
    };
    const res=output();
    await proxy(request,res,async()=> 'synthetic-oidc');
    const text=res.text();
    return {status:res.statusCode,body:text?JSON.parse(text):null};
  }
  function api(url,init) {
    assert.ok(url.startsWith(API+'/api/v1/'),'immutable API Preview');
    const h=new Headers(init.headers);
    assert.equal(h.get('x-vercel-trusted-oidc-idp-token'),'synthetic-oidc');
    assert.equal(h.get('cookie'),null);
    assert.equal(h.get('origin'),null);
    const path=url.slice((API+'/api/v1/').length);
    const data=init.body?JSON.parse(Buffer.from(init.body).toString()):{};
    if(path==='ops/preview-db-identity') {attest++;return json(200,SQL_ID);}
    if(path==='auth/register'&&init.method==='POST') {
      assert.ok(attest>=id,'actual identity attestation before registration');
      const user={id:id++,email:data.email,password:data.password,record:null};
      users.set(user.id,user);
      const token='iamina.mock'+generation++ +':fixture:token';
      bearer.set(token,user.id);
      return json(200,{user:{id:user.id,email:user.email},access_token:token});
    }
    if(path==='auth/login'&&init.method==='POST') {
      const user=[...users.values()].find(u=>u.email===data.email&&u.password===data.password);
      if(!user)return json(401,{detail:'invalid'});
      const token='iamina.mock'+generation++ +':fixture:token';
      bearer.set(token,user.id);
      return json(200,{user:{id:user.id},access_token:token});
    }
    const user=users.get(bearer.get((h.get('authorization')??'').replace(/^Bearer /,'')));
    if(!user)return json(401,{detail:'Unauthorized'});
    if(path==='auth/me')return json(200,{id:user.id,email:user.email});
    if(path==='profile'&&init.method==='PATCH') {user.record=data.record;return json(200,{record:user.record});}
    if(path==='profile'&&init.method==='GET')return json(200,{record:user.record});
    if(path==='auth/logout'&&init.method==='POST') {
      for(const [token,uid] of bearer)if(uid===user.id)bearer.delete(token);
      return json(200,{detail:'Signed out'});
    }
    if(path==='account'&&init.method==='DELETE') {
      if(data.confirm!=='DELETE MY ACCOUNT')return json(400,{detail:'confirm'});
      users.delete(user.id);
      for(const [token,uid] of bearer)if(uid===user.id)bearer.delete(token);
      return json(200,{detail:'deleted'});
    }
    return json(404,{detail:'not found'});
  }
  try {
    process.env.VERCEL_ENV='preview';
    process.env.VERCEL_PROJECT_ID='prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
    process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL=API;
    delete process.env.IAMINA_W02_REMOTE_E2E_ENABLED;
    globalThis.fetch=async(url,init)=>api(url,init);
    assert.equal((await send('auth/register','POST',{email:'A'})).status,403);
    assert.equal(users.size,0);
    process.env.IAMINA_W02_REMOTE_E2E_ENABLED='true';
    const A=await send('auth/register','POST',{email:'a@fixture.test',password:'A'});
    const B=await send('auth/register','POST',{email:'b@fixture.test',password:'B'});
    assert.equal(A.status,200);assert.equal(B.status,200);
    assert.notEqual(A.body.user.id,B.body.user.id);
    assert.equal(attest,2);
    const ta=A.body.access_token,tb=B.body.access_token;
    assert.equal((await send('auth/me','GET',null,'invalid')).status,401);
    assert.equal((await send('profile','PATCH',{record:'A_PRIVATE'},ta)).status,200);
    assert.equal((await send('profile','PATCH',{record:'B_PRIVATE'},tb)).status,200);
    assert.equal((await send('profile','GET',null,ta)).body.record,'A_PRIVATE');
    assert.equal((await send('profile','GET',null,tb)).body.record,'B_PRIVATE');
    assert.equal((await send('auth/logout','POST',{},ta)).status,200);
    assert.equal((await send('auth/me','GET',null,ta)).status,401);
    const A2=await send('auth/login','POST',{email:'a@fixture.test',password:'A'});
    assert.equal(A2.status,200);assert.notEqual(A2.body.access_token,ta);
    assert.equal((await send('profile','GET',null,A2.body.access_token)).body.record,'A_PRIVATE');
    assert.equal((await send('profile','GET',null,tb)).body.record,'B_PRIVATE');
    assert.equal((await send('account','DELETE',{confirm:'DELETE MY ACCOUNT'},A2.body.access_token)).status,200);
    assert.equal((await send('account','DELETE',{confirm:'DELETE MY ACCOUNT'},tb)).status,200);
    assert.equal(users.size,0,'simulated user table only');
    assert.equal(bearer.size,0,'simulated revocation only');
  } finally {
    globalThis.fetch=oldFetch;
    for(const [k,v] of Object.entries(saved)) {
      if(v===undefined)delete process.env[k];else process.env[k]=v;
    }
  }
});
