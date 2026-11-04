// TEST-ONLY browser backend. Never serve in IAMINA application production.
'use strict';
(() => {
  const DB='iamina_d18_dart_marker_TEST_ONLY_v1',STORE='markers';
  const pattern=/^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$/;
  const allowed=scope=>{if(typeof scope!=='string'||!pattern.test(scope))
    throw Error('D18_TEST_SCOPE_DENIED');};
  const open=()=>new Promise((resolve,reject)=>{
    const req=indexedDB.open(DB,1);
    req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))
      req.result.createObjectStore(STORE);};
    req.onsuccess=()=>{req.result.onversionchange=()=>req.result.close();
      resolve(req.result);};
    req.onerror=()=>reject(Error('D18_TEST_OPEN_FAILED'));
    req.onblocked=()=>reject(Error('D18_TEST_DB_BLOCKED'));
  });
  const read=async scope=>{
    allowed(scope);const db=await open();
    try{return await new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readonly');
      const req=tx.objectStore(STORE).get(scope);let value=null;
      req.onsuccess=()=>{value=req.result??null;};
      tx.oncomplete=()=>resolve(JSON.stringify(value));
      tx.onabort=()=>reject(Error('D18_TEST_READ_ABORT'));
      tx.onerror=()=>reject(Error('D18_TEST_READ_ERROR'));
    });}finally{db.close();}
  };
  const compareAndSwap=async(scope,expectedJson,nextJson)=>{
    allowed(scope);
    const expected=JSON.parse(expectedJson),next=JSON.parse(nextJson);
    if(next===null||typeof next!=='object'||Array.isArray(next)||
       next.sourceName!==scope||next.targetName!==scope+'_d18_cipher_v1')
       throw Error('D18_TEST_BAD_NEXT');
    const db=await open();
    try{return await new Promise((resolve,reject)=>{
      // One serialized IDB transaction: never await between get and put.
      const tx=db.transaction(STORE,'readwrite',{durability:'strict'});
      let wrote=false;
      const store=tx.objectStore(STORE),req=store.get(scope);
      req.onsuccess=()=>{
        if(JSON.stringify(req.result??null)!==JSON.stringify(expected))return;
        store.put(next,scope);
        wrote=true;
      };
      tx.oncomplete=()=>resolve(wrote?'true':'false');
      tx.onabort=()=>reject(Error('D18_TEST_CAS_ABORT'));
      tx.onerror=()=>reject(Error('D18_TEST_CAS_ERROR'));
    });}finally{db.close();}
  };
  Object.defineProperty(globalThis,'D18_CI_MARKER_STORE',{
    value:Object.freeze({read,compareAndSwap}),configurable:false,
    writable:false,
  });
})();
