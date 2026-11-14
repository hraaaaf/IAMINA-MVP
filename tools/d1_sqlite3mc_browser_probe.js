// Isolated CI feasibility in real Chromium, zero clinical/patient data.
const {chromium} = require('playwright');
const fs = require('fs');
const URL = 'http://127.0.0.1:7473/d1_probe.html';
const PROOF_DIR = 'd1-sqlite3mc-proof';
const SENTINEL = 'D1_SYNTHETIC_GLUCOSE_ONLY_777_XY';
const HEADER = 'SQLite format 3';

async function persistedBytes(page) {
  return page.evaluate(async ({database, sentinel, header}) => {
    const names = (await indexedDB.databases()).map(x => x.name).filter(Boolean);
    if (!names.includes(database)) throw Error('No IndexedDB database for encrypted probe');
    const db = await new Promise((resolve, reject) => {
      const req = indexedDB.open(database);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    const bytes = [];
    async function visit(v, depth=0) {
      if (v == null || depth > 12) return;
      if (v instanceof ArrayBuffer) {bytes.push(...new Uint8Array(v));return;}
      if (ArrayBuffer.isView(v)) {bytes.push(...new Uint8Array(v.buffer, v.byteOffset, v.byteLength));return;}
      if (v instanceof Blob) {bytes.push(...new Uint8Array(await v.arrayBuffer()));return;}
      if (typeof v === 'string') {bytes.push(...new TextEncoder().encode(v));return;}
      if (Array.isArray(v)) {for (const item of v) await visit(item, depth+1);return;}
      if (typeof v === 'object') {for (const value of Object.values(v)) await visit(value, depth+1);}
    }
    try {
      for (const store of db.objectStoreNames) {
        const tx = db.transaction(store, 'readonly');
        const all = await new Promise((resolve, reject) => {
          const req = tx.objectStore(store).getAll();
          req.onsuccess = () => resolve(req.result);
          req.onerror = () => reject(req.error);
        });
        for (const value of all) await visit(value);
      }
    } finally {db.close();}
    const buf = new Uint8Array(bytes);
    const has = text => {
      const pat = new TextEncoder().encode(text);
      outer: for(let i=0;i<=buf.length-pat.length;i++){
        for(let j=0;j<pat.length;j++) if(buf[i+j]!==pat[j]) continue outer;
        return true;
      }
      return false;
    };
    return {indexedDbName: database, physicalByteCount:buf.length,
      sentinelInPhysicalBytes:has(sentinel), sqlitePlainHeaderInPhysicalBytes:has(header)};
  }, {database:'iamina_d1_crypto_probe_20261113',sentinel:SENTINEL,header:HEADER});
}
(async () => {
  fs.mkdirSync(PROOF_DIR, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const proof = {scope:'synthetic SQLite3MultipleCiphers WASM feasibility ONLY',
    clinicalGo:false, head:process.env.D1_CANDIDATE_SHA||'unknown', result:'NOT_RUN'};
  try {
    const context = await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
    const page = await context.newPage();
    const errors = [];page.on('pageerror',err=>errors.push(String(err)));
    await page.goto(URL,{waitUntil:'domcontentloaded',timeout:45000});
    await page.waitForFunction(() => {
      const s=document.body?.textContent||'';
      return s.includes('"clinicalGo":false') && (s.includes('"ok":') || s.includes('"error":'));
    }, null, {timeout:45000});
    const app = JSON.parse(await page.locator('body').innerText());
    proof.engine = Object.fromEntries(Object.entries(app).filter(([k])=>k!=='stack'));
    proof.persisted = await persistedBytes(page);
    if (errors.length || !app.ok || !app.wrongKeyRejected || !app.persistentAfterReopen ||
        !app.cipherAvailable || !app.driftRead || proof.persisted.physicalByteCount===0 ||
        proof.persisted.sentinelInPhysicalBytes ||
        proof.persisted.sqlitePlainHeaderInPhysicalBytes) {
      throw Error('Encrypted SQLite feasibility gate failed: '+JSON.stringify({app:proof.engine,persisted:proof.persisted,errors}));
    }
    proof.result='PASS';
    await page.screenshot({path:PROOF_DIR+'/chromium-proof.png'});
    await context.close();
  } catch(err) {
    proof.result='FAIL';proof.error=String(err.stack||err).slice(0,2500);
    throw err;
  } finally {
    fs.writeFileSync(PROOF_DIR+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_SQLITE3MC_FEASIBILITY='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>process.exitCode=1);
