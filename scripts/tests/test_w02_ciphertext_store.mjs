import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createRecoverySecret, importRecoverySecret } from '../../frontend/web/iamina_vault_envelope.mjs';
import {
  openCiphertextStore, createRandomVaultSlot, CiphertextStoreError,
} from '../../frontend/web/iamina_vault_ciphertext_store.mjs';

const ownerA = 'amina_vault_v1_native_734';
const ownerB = 'amina_vault_v1_native_812';
const plainA = new TextEncoder().encode('SQLite format 3\0PATIENT_ALPHA_SECRET_SYNTHETIC');
const plainB = new TextEncoder().encode('SQLite format 3\0PATIENT_BRAVO_SECRET_SYNTHETIC');
const clone = (value) => value === undefined ? undefined : structuredClone(value);
const event = (fn) => setImmediate(fn);

// Minimal independent in-memory IndexedDB TRANSACTION TEST DOUBLE, not a browser.
// Readwrite transactions queue per database; put() stages a write; commit happens
// only at oncomplete and abort discards all staged writes.
class TestDatabase {
  constructor() {
    this.records = new Map();
    this.stores = new Set();
    this.objectStoreNames = { contains: name => this.stores.has(name) };
    this.queue = Promise.resolve();
    this.failWrite = false;
    this.abortAfterWrite = false;
    this.closed = false;
    this.strictDurability = true;
  }
  createObjectStore(name) { this.stores.add(name); return {}; }
  close() { this.closed = true; }
  transaction(name, mode, options) {
    if (this.closed || !this.stores.has(name)) throw Error('db closed or missing store');
    const tx = new TestTransaction(this, mode);
    tx.durability = options?.durability === 'strict' && this.strictDurability ? 'strict' : 'default';
    const active = this.queue.then(() => tx.start());
    this.queue = active.catch(() => {});
    return tx;
  }
}
class TestTransaction {
  constructor(db, mode) {
    this.db = db;
    this.mode = mode;
    this.operations = [];
    this.pending = 0;
    this.active = false;
    this.finalized = false;
    this.rows = null;
    this.oncomplete = null;
    this.onabort = null;
    this.onerror = null;
  }
  objectStore() { return {
    get: slot => this.request('get', slot),
    put: row => this.request('put', row),
  }; }
  request(op, value) {
    if (this.finalized) throw Error('transaction finalized');
    const request = { onsuccess: null, onerror: null, result: undefined };
    this.pending++;
    this.operations.push({ op, value, request });
    if (this.active) this.pump();
    return request;
  }
  async start() {
    this.active = true;
    this.rows = new Map([...this.db.records].map(([k,v])=>[k, clone(v)]));
    this.pump();
    await new Promise(resolve => { this.release = resolve; });
  }
  pump() {
    if (!this.active || this.finalized) return;
    if (this.operations.length === 0) {
      if (this.pending === 0) event(() => {
        if (this.finalized || this.operations.length || this.pending) return;
        this.finalized = true;
        if (this.mode === 'readwrite') this.db.records = this.rows;
        this.oncomplete?.();
        this.release();
      });
      return;
    }
    const {op,value,request} = this.operations.shift();
    event(() => {
      if (this.finalized) return;
      try {
        if (op === 'get') request.result = clone(this.rows.get(value));
        else {
          if (this.mode !== 'readwrite' || this.db.failWrite) throw Error('simulated quota failure');
          this.rows.set(value.slot, clone(value));
        }
        request.onsuccess?.();
        this.pending--;
        if (this.db.abortAfterWrite && op === 'put') this.abort();
        else this.pump();
      } catch (_) {
        request.onerror?.();
        this.abort();
      }
    });
  }
  abort() {
    if (this.finalized) return;
    this.finalized = true;
    event(() => {
      this.onabort?.();
      this.release?.();
    });
  }
}
class TestIndexedDB {
  constructor() { this.db = new TestDatabase(); }
  open(_name, _version) {
    const request = { result: this.db, onupgradeneeded: null, onsuccess: null, onerror: null };
    event(() => {
      if (!this.db.stores.size) request.onupgradeneeded?.();
      request.onsuccess?.();
    });
    return request;
  }
}
async function key() {
  return importRecoverySecret(createRecoverySecret());
}
async function context() {
  const idb = new TestIndexedDB();
  const store = await openCiphertextStore({ indexedDb:idb });
  return { idb, store, slot: createRandomVaultSlot(), key: await key() };
}
const code = (expected) => err => err instanceof CiphertextStoreError && err.code === expected;

test('random opaque storage slot does not reveal either patient id', () => {
  const ids = new Set(Array.from({ length: 100 }, createRandomVaultSlot));
  assert.equal(ids.size, 100);
  for (const slot of ids) {
    assert.match(slot, /^[a-zA-Z0-9_-]{43}$/);
    assert.notEqual(slot, ownerA);
  }
});
test('new empty slot is absent and does not materialize plaintext', async () => {
  const {store,slot} = await context();
  assert.equal(await store.readEnvelope(slot), null);
  store.close();
});
test('atomic commit saves AES-GCM envelope only and restores with key', async () => {
  const { idb,store,slot,key:k } = await context();
  const envelope = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  assert.equal(envelope.revision,1);
  const disk = JSON.stringify([...idb.db.records]);
  assert.ok(!disk.includes('PATIENT_ALPHA'));
  assert.ok(!disk.includes(ownerA));
  assert.equal(await store.readEnvelope(slot).then(x=>x.revision),1);
  assert.deepEqual((await store.restore({slot,vaultId:ownerA,minimumRevision:1,key:k})).bytes,plainA);
});
test('cold re-open recovers sealed bytes with same recovery capability', async () => {
  const idb = new TestIndexedDB();
  const slot = createRandomVaultSlot();
  const secret = createRecoverySecret();
  const first = await openCiphertextStore({indexedDb:idb});
  await first.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:await importRecoverySecret(secret)});
  first.close();
  idb.db.closed = false; // Test double models a new browser IDB connection
  const second = await openCiphertextStore({indexedDb:idb});
  const restored = await second.restore({slot,vaultId:ownerA,minimumRevision:1,key:await importRecoverySecret(secret)});
  assert.deepEqual(restored.bytes,plainA);
});
test('A ciphertext is not decryptable with B scope, even with same key', async () => {
  const {store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.restore({slot,vaultId:ownerB,minimumRevision:1,key:k}));
});
test('wrong key fails and ciphertext remains unchanged', async () => {
  const {idb,store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const prior = JSON.stringify([...idb.db.records]);
  await assert.rejects(store.restore({slot,vaultId:ownerA,minimumRevision:1,key:await key()}));
  assert.equal(JSON.stringify([...idb.db.records]),prior);
});
test('two tabs race on identical expected revision: exactly one commits', async () => {
  const {idb,store,slot,key:k} = await context();
  const first = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const competing = await openCiphertextStore({indexedDb:idb});
  const results = await Promise.allSettled([
    store.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:1,bytes:plainA,key:k}),
    competing.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:1,bytes:plainB,key:k}),
  ]);
  assert.deepEqual(results.map(x=>x.status).sort(),['fulfilled','rejected']);
  assert.equal(results.find(x=>x.status==='rejected').reason.code,'concurrent_update');
  assert.equal((await store.readEnvelope(slot)).revision,2);
});
test('fresh writer cannot clobber existing slot', async () => {
  const {store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.commit({slot,vaultId:ownerB,expectedEnvelope:null,minimumRevision:0,bytes:plainB,key:k}),code('concurrent_update'));
});
test('failed quota write leaves previous sealed state untouched', async () => {
  const {idb,store,slot,key:k} = await context();
  const first = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const disk = JSON.stringify([...idb.db.records]);
  idb.db.failWrite = true;
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:1,bytes:plainB,key:k}),code('indexeddb_commit_failed'));
  assert.equal(JSON.stringify([...idb.db.records]),disk);
});
test('transaction abort after staged write never commits a partial record', async () => {
  const {idb,store,slot,key:k} = await context();
  const first = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const disk = JSON.stringify([...idb.db.records]);
  idb.db.abortAfterWrite = true;
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:1,bytes:plainB,key:k}),code('indexeddb_commit_failed'));
  assert.equal(JSON.stringify([...idb.db.records]),disk);
});
test('corrupted record structure never silently becomes a new empty database', async () => {
  const {idb,store,slot} = await context();
  idb.db.records.set(slot,{slot,bytes:plainA});
  await assert.rejects(store.readEnvelope(slot),code('invalid_record'));
});
test('tampered ciphertext fails authentication on restore', async () => {
  const {idb,store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const corrupted = clone(idb.db.records.get(slot));
  corrupted.envelope.ciphertext = corrupted.envelope.ciphertext.slice(0,-1)+(corrupted.envelope.ciphertext.endsWith('A')?'B':'A');
  idb.db.records.set(slot,corrupted);
  await assert.rejects(store.restore({slot,vaultId:ownerA,minimumRevision:1,key:k}));
});
test('old revision rejects independent trusted revision floor', async () => {
  const {store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.restore({slot,vaultId:ownerA,minimumRevision:2,key:k}));
});
test('closed store fails closed; no implicit plaintext fallback', async () => {
  const {store,slot} = await context();
  store.close();
  await assert.rejects(store.readEnvelope(slot),code('store_closed'));
});
test('IDB unavailable fails closed', async () => {
  await assert.rejects(openCiphertextStore({indexedDb:null}),code('indexeddb_unavailable'));
  await assert.rejects(openCiphertextStore({indexedDb:{open(){throw Error('denied')}}}),code('indexeddb_open_failed'));
});
test('malformed slot rejected before any database access', async () => {
  const {store} = await context();
  await assert.rejects(store.readEnvelope(ownerA),code('invalid_slot'));
});

test('known existing vault deleted from disk fails closed, not a new account', async () => {
  const {store,slot,key:k} = await context();
  await assert.rejects(store.restore({slot,vaultId:ownerA,minimumRevision:1,key:k}),code('missing_known_snapshot'));
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:1,bytes:plainA,key:k}),code('rollback_detected'));
});
test('forged expected envelope cannot authorize replacing an existing patient', async () => {
  const {store,slot,key:k,idb} = await context();
  const previous = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  const original = JSON.stringify([...idb.db.records]);
  const forged = {...previous,ciphertext:previous.ciphertext.slice(0,-1)+(previous.ciphertext.endsWith('A')?'B':'A')};
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:forged,minimumRevision:1,bytes:plainB,key:k}));
  assert.equal(JSON.stringify([...idb.db.records]),original);
});
test('prior ciphertext from a different patient may not authorize overwriting', async () => {
  const {store,slot,key:k} = await context();
  const prior = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.commit({slot,vaultId:ownerB,expectedEnvelope:prior,minimumRevision:1,bytes:plainB,key:k}));
});

test('real SQLite snapshot: serialize -> encrypted IndexedDB envelope -> deserialize', async () => {
  const create = spawnSync('python3', ['-c', [
    'import base64, sqlite3',
    "c=sqlite3.connect(':memory:')",
    "c.execute('CREATE TABLE logs (id INTEGER PRIMARY KEY, note TEXT NOT NULL)')",
    "c.execute('INSERT INTO logs(note) VALUES (?)', ('SYNTHETIC-SQLITE-ENCRYPTED-RESTORE-734',))",
    'print(base64.b64encode(c.serialize()).decode())',
  ].join('\n')], { encoding:'utf8' });
  assert.equal(create.status,0,create.stderr);
  const genuineSQLite = new Uint8Array(Buffer.from(create.stdout.trim(),'base64'));
  assert.equal(new TextDecoder().decode(genuineSQLite.slice(0,15)),'SQLite format 3');
  const {idb,store,slot,key:k} = await context();
  await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:genuineSQLite,key:k});
  const serializedStorage = JSON.stringify([...idb.db.records]);
  assert.ok(!serializedStorage.includes('SYNTHETIC-SQLITE-ENCRYPTED-RESTORE'));
  assert.ok(!serializedStorage.includes('SQLite format 3'));
  const recovered = (await store.restore({slot,vaultId:ownerA,minimumRevision:1,key:k})).bytes;
  const check = spawnSync('python3', ['-c', [
    'import base64, sqlite3, sys',
    "c=sqlite3.connect(':memory:')",
    'c.deserialize(base64.b64decode(sys.stdin.read()))',
    "print(c.execute('SELECT note FROM logs WHERE id=1').fetchone()[0])",
  ].join('\n')], {input:Buffer.from(recovered).toString('base64'),encoding:'utf8'});
  assert.equal(check.status,0,check.stderr);
  assert.equal(check.stdout.trim(),'SYNTHETIC-SQLITE-ENCRYPTED-RESTORE-734');
  recovered.fill(0);
});

test('commit authenticates previous ciphertext against declared owner and key', async () => {
  const {store,slot,key:k} = await context();
  const first = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.commit({slot,vaultId:ownerB,expectedEnvelope:first,minimumRevision:1,bytes:plainB,key:k}),
    (err) => err.code === 'authentication_failed');
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:1,bytes:plainB,key:await key()}),
    (err) => err.code === 'authentication_failed');
  assert.equal((await store.readEnvelope(slot)).revision, 1);
});
test('external rollback floor also governs commits, not just restores', async () => {
  const {store,slot,key:k} = await context();
  const first = await store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k});
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:first,minimumRevision:2,bytes:plainB,key:k}), code('rollback_detected'));
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:first,bytes:plainB,key:k}), code('invalid_revision'));
  assert.equal((await store.readEnvelope(slot)).revision, 1);
});
test('browser that cannot honor strict durability denies writes', async () => {
  const {idb,store,slot,key:k} = await context();
  idb.db.strictDurability = false;
  await assert.rejects(store.commit({slot,vaultId:ownerA,expectedEnvelope:null,minimumRevision:0,bytes:plainA,key:k}),code('strict_durability_unavailable'));
  assert.equal(idb.db.records.size, 0);
});
