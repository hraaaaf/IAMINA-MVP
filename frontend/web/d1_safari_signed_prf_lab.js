/* D1-6 Safari lab: same-origin Django, real platform authenticator, fixture only.
 * Explicit prepare (network) then tap (no awaiting before navigator.credentials).
 * Nothing persistent; no patient routes. NEVER log credential/PRF/key/cookies.
 */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const enc = new TextEncoder();
  const b64 = bytes => {
    let s = '';
    for (const b of bytes) s += String.fromCharCode(b);
    return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  };
  const raw = value => {
    if (!/^[A-Za-z0-9_-]+$/.test(value)) throw Error('INVALID_CREDENTIAL');
    return Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')+
      '='.repeat((4-value.length%4)%4)),c=>c.charCodeAt(0));
  };
  const random = len => crypto.getRandomValues(new Uint8Array(len));
  const status = (id,code) => { $(id).textContent=code; };
  const body = input => JSON.stringify(input);
  let csrf, preparedEnrollment, preparedUnlock, envelope, input, salt, bridge;
  let busy = false;

  async function ensureCsrf() {
    const response = await fetch('/csrf/',{
      credentials:'same-origin',cache:'no-store',redirect:'error'
    });
    if (!response.ok) throw Error('CSRF_NOT_AVAILABLE');
    const data = await response.json();
    if (typeof data.csrf_token !== 'string') throw Error('CSRF_NOT_AVAILABLE');
    csrf = data.csrf_token;
  }
  async function post(name,payload) {
    if (!csrf) throw Error('CSRF_NOT_AVAILABLE');
    const response=await fetch('/api/v1/d1-research/passkey/'+name,{
      method:'POST',credentials:'same-origin',mode:'same-origin',redirect:'error',
      cache:'no-store',headers:{'X-CSRFToken':csrf,'Content-Type':'application/json'},
      body:body(payload)
    });
    if (!response.ok) throw Error('DJANGO_REJECTED_'+response.status);
    return response.json();
  }
  function enrollPublicKey(options) {
    const key = {
      ...options,challenge:raw(options.challenge),
      user:{...options.user,id:raw(options.user.id)},
      authenticatorSelection:{
        ...options.authenticatorSelection,
        authenticatorAttachment:'platform',
        residentKey:'required',userVerification:'required'
      },
      extensions:{prf:{}}
    };
    if (Array.isArray(options.excludeCredentials))
      key.excludeCredentials=options.excludeCredentials.map(x=>({...x,id:raw(x.id)}));
    return key;
  }
  function registrationPayload(credential) {
    if (!credential || credential.type !== 'public-key' || !credential.rawId ||
        credential.authenticatorAttachment !== 'platform') throw Error('NOT_PLATFORM');
    const prf=credential.getClientExtensionResults?.()?.prf;
    if (prf?.enabled !== true) throw Error('PRF_UNAVAILABLE');
    const id=b64(new Uint8Array(credential.rawId));
    const response = credential.response;
    if (!response?.attestationObject || !response?.clientDataJSON)
      throw Error('BAD_REGISTRATION_RESPONSE');
    return {
      id,rawId:id,type:'public-key',authenticatorAttachment:'platform',
      clientExtensionResults:{prf:{enabled:true}},
      response:{
        attestationObject:b64(new Uint8Array(response.attestationObject)),
        clientDataJSON:b64(new Uint8Array(response.clientDataJSON)),
        transports:response.getTransports?.()||[]
      }
    };
  }
  function exposeError(id,error) {
    const message=String(error?.name||error?.message||'DENIED');
    status(id,'FAIL_'+message.replace(/[^A-Za-z0-9_]/g,'_').slice(0,80));
  }
  function controls() {
    $('enroll').disabled=!preparedEnrollment||busy;
    $('unlock').disabled=!preparedUnlock||busy;
    $('prepareEnroll').disabled=busy;
    $('prepareUnlock').disabled=busy;
  }
  async function guard(fn,id) {
    if (busy) return;
    busy=true;controls();
    try { await fn(); } catch(e) { exposeError(id,e); }
    finally { busy=false;controls(); }
  }

  // These two calls can happen BEFORE the physical user gesture.
  $('prepareEnroll').addEventListener('click',() => guard(async()=>{
    preparedEnrollment=null; controls();
    await ensureCsrf();
    const password=$('password').value;
    if (!password) throw Error('PASSWORD_REQUIRED');
    const started=await post('enroll/start',{password});
    $('password').value='';
    if (!started.options?.challenge || !started.ceremony_id)
      throw Error('BAD_DJANGO_CHALLENGE');
    preparedEnrollment={id:started.ceremony_id,publicKey:enrollPublicKey(started.options)};
    status('enrollStatus','PRÊT — appuyer sur Créer la passkey');
  },'enrollStatus'));

  $('enroll').addEventListener('click',() => {
    if (!preparedEnrollment||busy) return;
    // Call navigator.credentials.create SYNCHRONOUSLY in trusted gesture.
    const start=preparedEnrollment;preparedEnrollment=null;busy=true;controls();
    let promise;
    try { promise=navigator.credentials.create({publicKey:start.publicKey}); }
    catch(e) { promise=Promise.reject(e); }
    void Promise.resolve(promise).then(async credential=>{
      const registration=registrationPayload(credential);
      const result=await post('enroll/finish',{
        ceremony_id:start.id,credential:registration
      });
      if (result.status!=='BOUND_RESEARCH_ONLY'||result.patient_ready!==false)
        throw Error('DJANGO_NOT_BOUND');
      $('credential').value=registration.id;
      envelope=null;input=null;salt=null;preparedUnlock=null;
      status('enrollStatus','PASS — passkey liée à Django (recherche seulement)');
    }).catch(e=>exposeError('enrollStatus',e)).finally(()=>{
      busy=false;controls();
    });
  });

  $('prepareUnlock').addEventListener('click',()=>guard(async()=>{
    preparedUnlock=null;controls();
    await ensureCsrf();
    const credentialId=$('credential').value.trim();
    if (!credentialId) throw Error('CREDENTIAL_REQUIRED');
    if (!envelope) {input=random(32);salt=random(16);}
    else {input=raw(envelope.prfInput);salt=raw(envelope.salt);}
    preparedUnlock=await bridge.prepareVerification({credentialId});
    status('unlockStatus','PRÊT — appuyer sur Déverrouiller avec Face ID');
  },'unlockStatus'));

  $('unlock').addEventListener('click',()=>{
    if (!preparedUnlock||busy) return;
    const prepared=preparedUnlock;preparedUnlock=null;busy=true;controls();
    // Must synchronously enter finishPrepared which starts navigator.credentials.get.
    let promise;
    let candidateEnvelope=null;
    let opened=false;
    try {
      promise=bridge.finishPrepared({prepared,prfInput:input,salt,
        callback:async({kek,scope})=>{
          if (!envelope) {
            candidateEnvelope=await window.iaminaD1SignedPrfResearch.sealSyntheticFixture({
              cryptoImpl:crypto,kek,scope,prfInput:input,salt
            });
          } else {
            const opened=await window.iaminaD1SignedPrfResearch.openSyntheticFixture({
              cryptoImpl:crypto,kek,scope,envelope
            });
            if (opened.status!=='SYNTHETIC_VAULT_OPENED')
              throw Error('INVALID_SYNTHETIC_VAULT');
            opened=true;
          }
        }});
    } catch(e) {promise=Promise.reject(e);}
    void Promise.resolve(promise).then(result=>{
      if (result.patientReady!==false) throw Error('CLINICAL_NOT_ALLOWED');
      if (candidateEnvelope) envelope=candidateEnvelope;
      status('result',opened?'PASS_UNLOCK_SYNTHETIC_VAULT':'PASS_SEALED_SYNTHETIC');
      status('unlockStatus','PASS_DJANGO_SIGNATURE_VERIFIED');
    }).catch(e=>exposeError('unlockStatus',e)).finally(()=>{
      busy=false;controls();
    });
  });

  if (!window.isSecureContext || !navigator.credentials?.get ||
      !navigator.credentials?.create || !crypto.subtle) {
    status('result','BLOCAGE — HTTPS / Safari WebAuthn requis');
    $('prepareEnroll').disabled=true;
    $('prepareUnlock').disabled=true;
    return;
  }
  bridge=window.iaminaD1SignedPrfResearch.createSignedPrfBridge({
    fetchImpl:window.fetch.bind(window),origin:window.location.origin,
    credentialsGet:options=>navigator.credentials.get(options),
    cryptoImpl:crypto,csrfToken:()=>csrf
  });
  controls();
})();
