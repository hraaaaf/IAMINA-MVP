import test from 'node:test';
import assert from 'node:assert/strict';
import { createRecoverySecret, importRecoverySecret, sealVaultSnapshot, openVaultSnapshot } from '../../frontend/web/iamina_vault_envelope.mjs';
import { envelopeSha256, openOptionASyntheticSession, finalizePendingSynthetic, makePreviewRevisionApi } from '../fixtures/iamina_w02_option_a_client.mjs';

const slot = 'R'.repeat(43);
const ownerA = 'amina_vault_v1_native_734';
const ownerB = 'amina_vault_v1_native_812';
const bytes = new TextEncoder().encode('W02_OPTION_A_SQLITE_SYNTHETIC');
const fails = code => err => err?.code === code;
class MemoryCipherStore {
  constructor() {this.envelope=null;this.fail=false;}
  async readEnvelope() {return this.envelope ? structuredClone(this.envelope) : null;}
  async restore({vaultId,minimumRevision,key}) {
    if(!this.envelope) return null;
    return {envelope:structuredClone(this.envelope),bytes:await openVaultSnapshot({
      envelope:this.envelope,vaultId,minimumRevision,key,
    })};
  }
  async commit({expectedEnvelope,minimumRevision,vaultId,bytes,key}) {
    if(this.fail) throw Error('synthetic_quota_failure');
    if(JSON.stringify(expectedEnvelope)!==JSON.stringify(this.envelope)) throw Error('concurrent_update');
    if(this.envelope && this.envelope.revision<minimumRevision) throw Error('rollback');
    const next=await sealVaultSnapshot({bytes,vaultId,revision:(this.envelope?.revision??0)+1,key});
    this.envelope=structuredClone(next);
    return next;
  }
}
class FakePg {
  constructor() {this.vaultId=ownerA;this.slot=null;this.rev=0;this.digest='';this.pending=null;this.failsFinalize=false;}
  async state() {return {vault_id:this.vaultId,status:this.pending?'pending':this.slot===null?'uninitialized':'ready',
    slot:this.slot,committed_revision:this.rev,committed_envelope_sha256:this.digest,
    pending_revision:this.pending?.rev??null,pending_ticket:this.pending?.ticket??null};}
  async reserve({slot,expected_revision}) {
    if(this.pending) throw Error('pending_recovery_required');
    if(this.slot!==null&&this.slot!==slot || expected_revision!==this.rev) throw Error('stale');
    if(this.slot===null) this.slot=slot;
    this.pending={rev:this.rev+1,ticket:'T'.repeat(43)};
    return {vault_id:this.vaultId,revision:this.pending.rev,ticket:this.pending.ticket};
  }
  async finalize({slot,revision,ticket,envelope_sha256}) {
    if(this.failsFinalize) throw Error('synthetic_server_timeout');
    if(this.pending?.rev!==revision || this.pending?.ticket!==ticket || this.slot!==slot) throw Error('forged');
    this.rev=revision;this.digest=envelope_sha256;this.pending=null;
    return this.state();
  }
}
async function ctx() {
  const pg=new FakePg(), store=new MemoryCipherStore();
  const key=await importRecoverySecret(createRecoverySecret());
  const owner={active:true,assertCurrent(){return this.active;}};
  return {pg,store,key,owner,args:{api:pg,store,vaultId:ownerA,slot,key,ownerSession:owner,allowSyntheticEmpty:true}};
}
test('real AES-GCM fixture + synthetic PG state: creation, CAS, digested read',async()=>{
  const c=await ctx();
  let first=await openOptionASyntheticSession(c.args);
  assert.equal(first.revision,0);
  assert.equal(first.takeSnapshot(),null);
  const r=await first.commit(bytes);
  assert.equal(r.revision,1);
  assert.equal(r.envelope_sha256,await envelopeSha256(c.store.envelope));
  first.close();
  const again=await openOptionASyntheticSession({...c.args,allowSyntheticEmpty:false});
  assert.deepEqual(again.takeSnapshot(),bytes);
  again.close();
  assert.ok(!JSON.stringify(c.store.envelope).includes('OPTION_A_SQLITE'));
});
test('stale IndexedDB rollback denied by independent server digest/revision',async()=>{
  const c=await ctx();
  const s=await openOptionASyntheticSession(c.args);
  await s.commit(bytes); const old=structuredClone(c.store.envelope);
  await s.commit(new TextEncoder().encode('NEW_CONTENT'));
  s.close();
  c.store.envelope=old;
  await assert.rejects(openOptionASyntheticSession(c.args),fails('rollback_or_ciphertext_mismatch'));
});
test('same-revision valid ciphertext substituted is detected using server digest',async()=>{
  const c=await ctx();
  const s=await openOptionASyntheticSession(c.args);await s.commit(bytes);s.close();
  c.store.envelope=await sealVaultSnapshot({
    bytes:new TextEncoder().encode('OTHER'),vaultId:ownerA,revision:1,key:c.key,
  });
  await assert.rejects(openOptionASyntheticSession(c.args),fails('rollback_or_ciphertext_mismatch'));
});
test('quota failure after reserve locks ordinary restore and requires explicit recovery',async()=>{
  const c=await ctx();
  const s=await openOptionASyntheticSession(c.args);
  c.store.fail=true;
  await assert.rejects(s.commit(bytes),/synthetic_quota_failure/);
  assert.equal((await c.pg.state()).status,'pending');
  await assert.rejects(s.commit(bytes),fails('session_not_available'));
  await assert.rejects(openOptionASyntheticSession(c.args),fails('pending_recovery_required'));
  await assert.rejects(finalizePendingSynthetic(c.args),fails('pending_ciphertext_missing'));
  s.close();
});
test('network failure after IDB commit is recoverable with authenticated local blob',async()=>{
  const c=await ctx();
  const s=await openOptionASyntheticSession(c.args);
  c.pg.failsFinalize=true;
  await assert.rejects(s.commit(bytes),/synthetic_server_timeout/);
  assert.equal((await c.pg.state()).status,'pending');
  s.close();
  c.pg.failsFinalize=false;
  const receipt=await finalizePendingSynthetic(c.args);
  assert.equal(receipt.revision,1);
  const reopened=await openOptionASyntheticSession(c.args);
  assert.deepEqual(reopened.takeSnapshot(),bytes);
  reopened.close();
});
test('other owner, wrong key and revoked session denied',async()=>{
  const c=await ctx();const s=await openOptionASyntheticSession(c.args);await s.commit(bytes);s.close();
  await assert.rejects(openOptionASyntheticSession({...c.args,vaultId:ownerB}),fails('verified_owner_scope_mismatch'));
  await assert.rejects(openOptionASyntheticSession({...c.args,key:await importRecoverySecret(createRecoverySecret())}));
  c.owner.active=false;
  await assert.rejects(openOptionASyntheticSession(c.args),fails('owner_session_changed'));
});
test('no BFF cookies, explicit same-origin, invalid bearer denied',async()=>{
  assert.throws(()=>makePreviewRevisionApi({origin:'https://review.example',token:'firebase-token'}),fails('invalid_native_preview_context'));
  const calls=[];
  const a=makePreviewRevisionApi({origin:'https://review.example',
    token:'iamina.test:2:ABCD',
    fetchImpl:async(url,options)=>{calls.push({url:url.toString(),options});return{ok:true,json:async()=>({status:'uninitialized'})};}});
  await a.state();
  assert.equal(calls[0].url,'https://review.example/api/v1/w02/vault-revision/state');
  assert.equal(calls[0].options.credentials,'omit');
  assert.equal(calls[0].options.cache,'no-store');
  assert.equal(calls[0].options.redirect,'error');
  assert.ok(!('Cookie' in calls[0].options.headers));
});

test('server-verified native account namespace is mandatory',async()=>{
  const c=await ctx();
  c.pg.vaultId=ownerB;
  await assert.rejects(openOptionASyntheticSession(c.args),fails('verified_owner_scope_mismatch'));
  assert.equal(c.store.envelope,null);
});
