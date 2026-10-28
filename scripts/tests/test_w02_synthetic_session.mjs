import test from 'node:test';
import assert from 'node:assert/strict';
import { createRecoverySecret, importRecoverySecret, openVaultSnapshot, sealVaultSnapshot } from '../../frontend/web/iamina_vault_envelope.mjs';
import { openSyntheticVaultSession, W02SessionError } from '../../frontend/web/iamina_w02_synthetic_session.mjs';

const vaultId = 'amina_vault_v1_native_734';
const otherId = 'amina_vault_v1_native_812';
const slot = 'c'.repeat(43);
const payload = new TextEncoder().encode('W02_VOLATILE_SQLITE_SYNTHETIC_734');
const code = c => err => err?.code === c;

class TrustedTestFloor {
  constructor() { this.floors = new Map(); this.denyAdvance = false; }
  id({ vaultId, slot }) { return vaultId + ':' + slot; }
  async getFloor(scope) { return this.floors.get(this.id(scope)) ?? 0; }
  async compareAndAdvance(scope) {
    if (this.denyAdvance) return false;
    const id = this.id(scope);
    if ((this.floors.get(id) ?? 0) !== scope.expectedFloor) return false;
    this.floors.set(id, scope.nextFloor);
    return true;
  }
}
class TestCiphertextStore {
  constructor() { this.row = null; this.failCommit = false; }
  async readEnvelope() { return structuredClone(this.row); }
  async restore({ vaultId, minimumRevision, key }) {
    if (!this.row) return null;
    const envelope = structuredClone(this.row);
    return { envelope, bytes: await openVaultSnapshot({ envelope, vaultId, minimumRevision, key }) };
  }
  async commit({ expectedEnvelope, vaultId, minimumRevision, bytes, key }) {
    if (this.failCommit) throw Error('simulated quota/transaction failure');
    if (JSON.stringify(this.row) !== JSON.stringify(expectedEnvelope)) throw Error('concurrent_update');
    const next = await sealVaultSnapshot({ bytes, vaultId, revision: (this.row?.revision ?? 0) + 1, key });
    this.row = structuredClone(next);
    return next;
  }
}
class TestVolatileSqlite {
  constructor(bytes) { this.data = bytes ? Uint8Array.from(bytes) : Uint8Array.from(payload); this.closed = false; this.exported = []; }
  exportSnapshot() {
    if (this.closed) throw Error('memory_closed');
    const snapshot = Uint8Array.from(this.data);
    this.exported.push(snapshot);
    return snapshot;
  }
  async close() { this.closed = true; this.data.fill(0); }
}
async function setup() {
  const store = new TestCiphertextStore();
  const floor = new TrustedTestFloor();
  const key = await importRecoverySecret(createRecoverySecret());
  const owner = { active:true, assertCurrent() { return this.active; } };
  const opened = [];
  const memoryFactory = { async open({authenticatedSnapshot}) {
    const db = new TestVolatileSqlite(authenticatedSnapshot);
    opened.push(db);
    return db;
  } };
  const args = { store, slot, vaultId, key, ownerSession:owner, revisionAuthority:floor, memoryFactory, allowSyntheticEmpty:true };
  return { args, store, floor, owner, opened };
}

test('synthetic create -> seal -> revision 1 -> cold recover, ciphertext only', async () => {
  const ctx = await setup();
  const first = await openSyntheticVaultSession(ctx.args);
  assert.equal(first.revision,0);
  assert.equal((await first.commit()).revision,1);
  assert.equal(ctx.opened[0].exported[0].every(b => b === 0),true);
  assert.ok(!JSON.stringify(ctx.store.row).includes('VOLATILE_SQLITE_SYNTHETIC'));
  await first.close();
  const second = await openSyntheticVaultSession({ ...ctx.args, allowSyntheticEmpty:false });
  assert.equal(second.revision,1);
  assert.deepEqual(second.executor.data,payload);
  await second.close();
});
test('new account cannot read ciphertext from another account', async () => {
  const ctx = await setup();
  const first = await openSyntheticVaultSession(ctx.args);
  await first.commit(); await first.close();
  await assert.rejects(openSyntheticVaultSession({ ...ctx.args, vaultId:otherId }), code('authentication_failed'));
  assert.equal(ctx.opened.length,1);
});
test('unknown empty vault never initializes unless explicitly synthetic', async () => {
  const ctx = await setup();
  await assert.rejects(openSyntheticVaultSession({ ...ctx.args, allowSyntheticEmpty:false }), code('synthetic_creation_not_permitted'));
  assert.equal(ctx.opened.length,0);
});
test('existing encrypted blob without independently trusted floor fails closed', async () => {
  const ctx = await setup();
  ctx.store.row = await sealVaultSnapshot({ bytes:payload, vaultId, revision:1, key:ctx.args.key });
  await assert.rejects(openSyntheticVaultSession(ctx.args), code('trusted_revision_floor_missing'));
  assert.equal(ctx.opened.length,0);
});
test('prior revision or lost disk with trusted floor cannot be silently restored', async () => {
  const ctx = await setup();
  let session = await openSyntheticVaultSession(ctx.args);
  await session.commit(); await session.close();
  ctx.floor.floors.set(ctx.floor.id(ctx.args),2);
  await assert.rejects(openSyntheticVaultSession(ctx.args), code('rollback_detected'));
  ctx.store.row=null;
  await assert.rejects(openSyntheticVaultSession(ctx.args), code('missing_known_snapshot'));
});
test('owner switch blocks volatile DB access and commit before trusted revision changes', async () => {
  const ctx = await setup();
  const session = await openSyntheticVaultSession(ctx.args);
  ctx.owner.active=false;
  assert.throws(() => session.executor, code('owner_session_changed'));
  await assert.rejects(session.commit(), code('owner_session_changed'));
  assert.equal(await ctx.floor.getFloor(ctx.args),0);
  await session.close();
});
test('quota/crash after trusted floor advance poisons session and denies restart', async () => {
  const ctx = await setup();
  const session = await openSyntheticVaultSession(ctx.args);
  ctx.store.failCommit=true;
  await assert.rejects(session.commit(), /quota\/transaction/);
  assert.equal(ctx.opened[0].exported[0].every(b => b === 0),true);
  assert.equal(await ctx.floor.getFloor(ctx.args),1);
  await assert.rejects(session.commit(), code('session_poisoned'));
  await session.close();
  await assert.rejects(openSyntheticVaultSession(ctx.args), code('missing_known_snapshot'));
});
test('trusted revision CAS rejects a stale simultaneous writer without ciphertext overwrite', async () => {
  const ctx = await setup();
  const first = await openSyntheticVaultSession(ctx.args);
  await first.commit(); await first.close();
  const a = await openSyntheticVaultSession(ctx.args);
  const b = await openSyntheticVaultSession(ctx.args);
  const outcomes = await Promise.allSettled([a.commit(),b.commit()]);
  assert.deepEqual(outcomes.map(x=>x.status).sort(), ['fulfilled','rejected']);
  assert.equal(outcomes.find(x=>x.status==='rejected').reason.code,'trusted_revision_conflict');
  assert.equal(ctx.store.row.revision,2);
  await a.close(); await b.close();
});
test('missing trusted authority is rejected before accessing disk', async () => {
  const ctx = await setup();
  await assert.rejects(openSyntheticVaultSession({ ...ctx.args, revisionAuthority:null }), code('missing_trusted_dependency'));
  await assert.rejects(openSyntheticVaultSession({ ...ctx.args, ownerSession:{assertCurrent:()=>Promise.resolve(true)} }), code('owner_session_changed'));
  assert.equal(ctx.opened.length,0);
});
test('close is idempotent; never silently allows a post-close commit', async () => {
  const ctx = await setup();
  const session = await openSyntheticVaultSession(ctx.args);
  await session.close(); await session.close();
  await assert.rejects(session.commit(), code('session_closed'));
  assert.equal(ctx.opened[0].closed,true);
});
