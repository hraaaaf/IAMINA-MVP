// D1 actual IAMINA schema/WebCrypto candidate only. Never a clinical GO.
const {chromium, webkit} = require('playwright');
const webkitOnly = process.env.D1_BROWSER_ENGINE === 'webkit';
const browserEngine = webkitOnly ? webkit : chromium;
const fs = require('fs');
const folder = webkitOnly
  ? 'd1-webkit-encrypted-schema-proof'
  : 'd1-clinical-cipher-candidate-proof';
const sentinel = 'D1_SYNTHETIC_GLUCOSE_ONLY_735_XY';
const names = [
  'iamina_d1_encrypted_vault_v1_amina_vault_v1_native_735',
  'iamina_d1_encrypted_vault_v1_amina_vault_v1_native_736',
];

async function rawStoreBytes(page, name) {
  return page.evaluate(async name => {
    const databases=await indexedDB.databases();
    if (!databases.some(d=>d.name===name)) throw Error('Missing ciphered store: '+name);
    const req=indexedDB.open(name);
    const db=await new Promise((resolve,reject)=>{
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error);
    });
    const chunks=[];
    async function readAny(v,depth=0) {
      if (v==null||depth>10)return;
      if(v instanceof ArrayBuffer){chunks.push(new Uint8Array(v));return;}
      if(ArrayBuffer.isView(v)){chunks.push(new Uint8Array(v.buffer,v.byteOffset,v.byteLength));return;}
      if(v instanceof Blob){chunks.push(new Uint8Array(await v.arrayBuffer()));return;}
      if(typeof v==='string'){chunks.push(new TextEncoder().encode(v));return;}
      if(Array.isArray(v)){for(const x of v)await readAny(x,depth+1);return;}
      if(typeof v==='object'){for(const x of Object.values(v))await readAny(x,depth+1);}
    }
    try {
      for(const name of db.objectStoreNames) {
        const tx=db.transaction(name,'readonly');
        const value=await new Promise((resolve,reject)=>{
          const r=tx.objectStore(name).getAll();
          r.onsuccess=()=>resolve(r.result);
          r.onerror=()=>reject(r.error);
        });
        for(const x of value)await readAny(x);
      }
    }finally{db.close();}
    return chunks.flatMap(x=>[...x]);
  },name);
}

function hasBytes(bytes, text) {
  const needle=new TextEncoder().encode(text);
  outer:for(let i=0;i<=bytes.length-needle.length;i++){
    for(let j=0;j<needle.length;j++)if(bytes[i+j]!==needle[j])continue outer;
    return true;
  }return false;
}
(async()=>{
  fs.mkdirSync(folder,{recursive:true});
  const proof={scope:'real AppDatabase schema + synthetic owner-bound AES-GCM + SQLite3MC',
    head:process.env.D1_CANDIDATE_SHA||'unknown',clinicalGo:false,
    engine:webkitOnly ? 'Playwright WebKit' : 'Playwright Chromium',
    result:'NOT_RUN'};
  const browser=await browserEngine.launch({headless:true});
  try{
    const ctx=await browser.newContext({viewport:{width:1280,height:900},locale:'en-US',serviceWorkers:'block'});
    const page=await ctx.newPage();
    const errors=[];
    const consoleLines=[];
    page.on('pageerror',e=>errors.push(String(e.stack||e).slice(0,1500)));
    page.on('console',msg=>consoleLines.push(msg.type()+': '+msg.text().slice(0,400)));
    await page.goto('http://127.0.0.1:7474/',{waitUntil:'domcontentloaded',timeout:60000});
    try {
      await page.waitForFunction(()=>{
        const s=document.body?.textContent||'';
        return s.includes('"clinicalGo":false') &&
          (s.includes('"ok":')||s.includes('"error":'));
      },null,{timeout:30000});
    }catch(err){
      proof.diagnostics=await page.evaluate(async()=>({
        title:document.title,readyState:document.readyState,
        html:document.documentElement.outerHTML.slice(0,3000),
        bodyText:(document.body?.innerText||'').slice(0,2000),
        flutterSurfaceCount:document.querySelectorAll('flt-glass-pane').length,
        flutterSemanticsCount:document.querySelectorAll('flt-semantics').length,
        scripts:[...document.scripts].map(x=>x.src.slice(-140)),
        lazyCryptoPresent:!!globalThis.IaminaD1CryptoCandidate,
        dbNames:typeof indexedDB.databases==='function'?
           await indexedDB.databases().then(x=>x.map(v=>v.name)):[],
      })).catch(e=>({diagnosticError:String(e)}));
      proof.jsErrors=errors;
      proof.console=consoleLines.slice(-25);
      await page.screenshot({path:folder+'/failed-browser-state.png'}).catch(()=>{});
      throw err;
    }
    const raw=await page.locator('body').innerText();
    const report=JSON.parse(raw.slice(raw.indexOf('{"scope"')));
    proof.jsErrors=errors;
    proof.console=consoleLines.slice(-10);
    proof.candidate=Object.fromEntries(Object.entries(report).filter(([k])=>!['stack'].includes(k)));
    if (!report.ok) {
      throw Error('Encrypted clinical schema candidate failed: ' +
        JSON.stringify(proof.candidate).slice(0,1900));
    }
    proof.persistence=[];
    for(const name of names){
      const bytes=await rawStoreBytes(page,name);
      const rec={name,bytes:bytes.length,
        containsSentinel:hasBytes(bytes,sentinel),
        containsSqliteHeader:hasBytes(bytes,'SQLite format 3'),
        containsPlainSchema:hasBytes(bytes,'log_entries')};
      proof.persistence.push(rec);
    }
    const metadata=await page.evaluate(()=>Object.keys(localStorage)
      .filter(k=>k.startsWith('iamina_d1_wrapped_vault_v1_'))
      .map(k=>({key:k,bytes:localStorage[k].length})));
    proof.metadata=metadata;
    if(!report.ok||errors.length||proof.persistence.some(x=>x.bytes===0||
        x.containsSentinel||x.containsSqliteHeader||x.containsPlainSchema)){
      throw Error('D1 candidate failed: '+JSON.stringify({report,errors,persisted:proof.persistence}).slice(0,2000));
    }
    proof.result='PASS';
    await page.screenshot({path:folder+'/chromium-synthetic-proof.png'});
    await ctx.close();
  }catch(e){proof.result='FAIL';proof.error=String(e.stack||e).slice(0,2500);throw e;}
  finally{
    fs.writeFileSync(folder+'/proof.json',JSON.stringify(proof,null,2));
    console.log('D1_REAL_SCHEMA_ENCRYPTED_CANDIDATE='+JSON.stringify(proof));
    await browser.close();
  }
})().catch(()=>process.exitCode=1);
