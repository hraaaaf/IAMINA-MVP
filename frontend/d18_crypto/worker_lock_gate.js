// D18 candidate: exclusive origin-wide encrypted namespace lock.
// Not a cutover lock for historical plaintext writers; clinical activation forbidden.
(() => {
  'use strict';
  const valid = /^amina_vault_v1_(?:native_[1-9][0-9]*|device_[0-9a-f]{32})_d18_cipher_v1$/;
  globalThis.__d18AcquireUnpublishedLock = async name => {
    if (typeof name !== 'string' || !valid.test(name) ||
        !navigator.locks || typeof navigator.locks.request !== 'function') return {ok:false};
    let grant, release;
    const granted = new Promise(resolve => {grant=resolve});
    const held = new Promise(resolve => {release=resolve});
    const task = navigator.locks.request('iamina:d18:encrypted:v1:'+name,
      {mode:'exclusive',ifAvailable:true}, async lock => {
        if (!lock) {grant(false);return;}
        grant(true);
        await held;
      }).catch(()=>{grant(false)});
    if (!await granted) {await task;return {ok:false};}
    let closed=false;
    return {ok:true, release:async()=>{
      if(closed)return;
      closed=true;release();await task;
    }};
  };
})();
