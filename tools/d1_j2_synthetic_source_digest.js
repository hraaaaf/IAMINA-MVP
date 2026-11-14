// D1 J1/J2 — test-only, read-only source-digest oracle.
// The output is equivalent to the J1 logical IndexedDB manifest for exactly
// one owned source. It never writes, migrates or deletes patient records.
// Unsupported types/APIs/unknown missing DB must FAIL CLOSED.
(() => {
  'use strict';
  async function digest(name) {
    if (typeof name !== 'string' ||
        !/^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$/.test(name)) {
      throw Error('J2_SOURCE_SCOPE_INVALID');
    }
    if (typeof indexedDB.databases !== 'function' ||
        !globalThis.crypto?.subtle) {
      throw Error('J2_SOURCE_DIGEST_UNSUPPORTED');
    }
    const dbNames=(await indexedDB.databases()).map(x=>x.name);
    if (!dbNames.includes(name)) throw Error('J2_SOURCE_DISAPPEARED');
    const request = r=>new Promise((resolve,reject)=>{
      r.onsuccess=()=>resolve(r.result);
      r.onerror=()=>reject(r.error);
    });
    async function encode(value) {
      if (value===null) return {t:'null'};
      if (value===undefined) return {t:'undefined'};
      const type=typeof value;
      if (type==='string'||type==='boolean') return {t:type,v:value};
      if (type==='number') {
        if(!Number.isFinite(value)) throw Error('J2_SOURCE_NON_FINITE');
        return {t:'number',v:value};
      }
      if(type==='bigint') return {t:'bigint',v:String(value)};
      if(value instanceof Date){
        if(!Number.isFinite(value.getTime())) throw Error('J2_SOURCE_DATE_INVALID');
        return {t:'date',v:value.toISOString()};
      }
      if(value instanceof ArrayBuffer||ArrayBuffer.isView(value)){
        const bytes=value instanceof ArrayBuffer?new Uint8Array(value):
          new Uint8Array(value.buffer,value.byteOffset,value.byteLength);
        let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
        return {t:'bytes',ctor:value.constructor.name,v:btoa(binary)};
      }
      if(value instanceof Blob){
        const bytes=new Uint8Array(await value.arrayBuffer());
        let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
        return {t:'blob',mime:value.type,v:btoa(binary)};
      }
      if(Array.isArray(value))return {t:'array',v:await Promise.all(value.map(encode))};
      if(Object.getPrototypeOf(value)===Object.prototype){
        const v={};for(const k of Object.keys(value).sort())v[k]=await encode(value[k]);
        return {t:'object',v};
      }
      throw Error('J2_UNSUPPORTED_SOURCE_CLONE_TYPE');
    }
    const db=await request(indexedDB.open(name));
    const stores=[];
    try{
      for(const storeName of [...db.objectStoreNames].sort()){
        const tx=db.transaction(storeName,'readonly');
        const store=tx.objectStore(storeName);
        const indexes=[...store.indexNames].sort().map(indexName=>{
          const idx=store.index(indexName);
          return {name:indexName,keyPath:idx.keyPath,unique:idx.unique,
            multiEntry:idx.multiEntry};
        });
        const [keys,values]=await Promise.all([
          request(store.getAllKeys()),request(store.getAll())
        ]);
        if(keys.length!==values.length)throw Error('J2_SOURCE_MUTATED_DURING_SCAN');
        const records=[];
        for(let k=0;k<keys.length;k++){
          records.push({key:await encode(keys[k]),value:await encode(values[k])});
        }
        stores.push({name:storeName,keyPath:store.keyPath,
          autoIncrement:store.autoIncrement,indexes,records});
      }
    } finally {db.close();}
    const payload={version:1,kind:'iamina-d1-j1-logical-synthetic',
      databases:[{name,version:db.version,stores}]};
    const bytes=new TextEncoder().encode(JSON.stringify(payload));
    const hash=await crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');
  }
  Object.defineProperty(globalThis,'IaminaD1J2SyntheticSourceDigest',{
    value:Object.freeze({digest}),configurable:false,writable:false
  });
})();