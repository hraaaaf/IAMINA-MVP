// IAMINA D18 P0-D — Node reference harness, NOT a Flutter/browser implementation.
// Synthetic already-encrypted-like bytes only. NOT proof of sqlite3mc correctness.
// The destination is NEVER an IAMINA patient database. No clinical activation.
'use strict';
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {once}=require('node:events');
const {finished}=require('node:stream/promises');
const SIZE=17*1024*1024+107;
const BLOCK=64*1024;
const ITER=600000;
const scope='amina_vault_v1_native_734';
const pass='D18-CI-SYNTHETIC-ONLY-ARCHIVE-SECRET-2026';
const results=[];
function assert(ok,code){if(!ok)throw Error('D18_P0D_'+code);}
function keyFrom(password,salt){return crypto.pbkdf2Sync(password,salt,ITER,32,'sha256');}
function nonce(prefix,seq){
  const n=Buffer.alloc(12);prefix.copy(n,0);n.writeUInt32BE(seq,8);return n;
}
function aad(kind,seq,expectedScope){
  return Buffer.from(['IAMINA-D18-STREAM-V1',kind,seq,expectedScope].join('|'));
}
function protect(key,prefix,kind,seq,bytes,expectedScope){
  const cipher=crypto.createCipheriv('aes-256-gcm',key,nonce(prefix,seq));
  cipher.setAAD(aad(kind,seq,expectedScope));
  return Buffer.concat([cipher.update(bytes),cipher.final(),cipher.getAuthTag()])
    .toString('base64');
}
function unprotect(key,prefix,kind,seq,encoded,expectedScope){
  const bytes=Buffer.from(encoded,'base64');
  assert(bytes.length>=16&&bytes.length<=BLOCK+4096,'INVALID_FRAME');
  const decipher=crypto.createDecipheriv('aes-256-gcm',key,nonce(prefix,seq));
  decipher.setAAD(aad(kind,seq,expectedScope));
  decipher.setAuthTag(bytes.subarray(-16));
  return Buffer.concat([decipher.update(bytes.subarray(0,-16)),decipher.final()]);
}
// Bounded parser: readline's unbounded line buffering would allow an
// attacker to exhaust memory with a single malformed multi-GB record.
async function* boundedLines(file){
  let pending=Buffer.alloc(0);
  for await(const chunk of fs.createReadStream(file,{highWaterMark:BLOCK})){
    let start=0;
    while(true){
      const end=chunk.indexOf(10,start);
      if(end<0)break;
      const fragment=chunk.subarray(start,end);
      assert(pending.length+fragment.length<=150000,'OVERSIZED_RECORD');
      yield Buffer.concat([pending,fragment]).toString('utf8');
      pending=Buffer.alloc(0);start=end+1;
    }
    const remaining=chunk.subarray(start);
    assert(pending.length+remaining.length<=150000,'OVERSIZED_RECORD');
    pending=Buffer.concat([pending,remaining]);
  }
  assert(pending.length===0,'UNTERMINATED_LAST_FRAME');
}
async function writeLine(stream,obj){
  if(!stream.write(JSON.stringify(obj)+'\n'))await once(stream,'drain');
}
async function createSyntheticCiphertext(file){
  const out=fs.createWriteStream(file,{flags:'wx',mode:0o600});
  let remaining=SIZE;
  while(remaining>0){
    const bytes=crypto.randomBytes(Math.min(BLOCK,remaining));
    if(!out.write(bytes))await once(out,'drain');
    remaining-=bytes.length;
  }
  out.end();await finished(out);
}
async function seal(source,archive){
  const salt=crypto.randomBytes(16),prefix=crypto.randomBytes(8);
  const key=keyFrom(pass,salt);
  const out=fs.createWriteStream(archive,{flags:'wx',mode:0o600});
  const hash=crypto.createHash('sha256');
  let count=0,total=0;
  try{
    await writeLine(out,{format:'iamina-d18-stream-v1',version:1,
      kdf:'pbkdf2-sha256',iterations:ITER,chunkSize:BLOCK,
      salt:salt.toString('base64'),noncePrefix:prefix.toString('base64')});
    for await(const chunk of fs.createReadStream(source,{highWaterMark:BLOCK})){
      assert(count<0xffffffff,'TOO_MANY_CHUNKS');
      hash.update(chunk);total+=chunk.length;
      await writeLine(out,{kind:'chunk',seq:count,
        sealed:protect(key,prefix,'chunk',count,chunk,scope)});
      count++;
    }
    assert(total>16*1024*1024,'SIZE_NOT_ABOVE_16_MIB');
    await writeLine(out,{kind:'final',seq:count,
      sealed:protect(key,prefix,'final',count,Buffer.from(JSON.stringify({
        scope,bytes:total,chunks:count,sha256:hash.digest('hex'),
        envelope:'synthetic-envelope-placeholder-not-real-key-policy',
      })),scope)});
  }finally{key.fill(0);out.end();await finished(out);}
  return {total,count};
}
async function restore(archive,stage,destination,expectedScope,password,
                       {interruptAfter=Infinity}={}){
  // 'wx' quarantines all partial/unverified content. No prior file overwrite.
  const fd=fs.openSync(stage,'wx',0o600);
  let key,hash=crypto.createHash('sha256'),prefix;
  let total=0,count=0,foundFinal=false,header=false;
  try{
    for await(const line of boundedLines(archive)){
      assert(line.length<150000,'OVERSIZED_RECORD');
      const record=JSON.parse(line);
      if(!header){
        header=true;
        assert(record.format==='iamina-d18-stream-v1'&&record.version===1 &&
          record.kdf==='pbkdf2-sha256'&&record.iterations===ITER &&
          record.chunkSize===BLOCK,'BAD_HEADER');
        const salt=Buffer.from(record.salt,'base64');
        prefix=Buffer.from(record.noncePrefix,'base64');
        assert(salt.length===16&&prefix.length===8,'BAD_SALT_NONCE');
        key=keyFrom(password,salt);
        continue;
      }
      assert(!foundFinal,'TRAILING_RECORD');
      assert(record.seq===count && typeof record.sealed==='string',
        'OUT_OF_ORDER');
      if(record.kind==='chunk'){
        const bytes=unprotect(key,prefix,'chunk',count,record.sealed,
          expectedScope);
        assert(bytes.length>0&&bytes.length<=BLOCK,'BAD_CHUNK_SIZE');
        for(let offset=0;offset<bytes.length;){
          const n=fs.writeSync(fd,bytes,offset,bytes.length-offset);
          assert(n>0,'STALLED_PARTIAL_WRITE');
          offset+=n;
        }
        hash.update(bytes);total+=bytes.length;count++;
        assert(total<=512*1024*1024,'MAX_STREAM_CAP_EXCEEDED');
        if(count===interruptAfter)throw Error('D18_P0D_SIMULATED_CRASH');
      }else if(record.kind==='final'){
        const manifest=JSON.parse(unprotect(key,prefix,'final',count,
          record.sealed,expectedScope).toString('utf8'));
        assert(manifest.scope===expectedScope &&
          manifest.bytes===total&&manifest.chunks===count &&
          manifest.sha256===hash.digest('hex'),'BAD_FINAL_MANIFEST');
        foundFinal=true;
      }else throw Error('D18_P0D_UNKNOWN_RECORD');
    }
    assert(header&&foundFinal,'INCOMPLETE_ARCHIVE');
    fs.fsyncSync(fd);
  }finally{
    if(key)key.fill(0);
    fs.closeSync(fd);
  }
  // Hard-link creation is atomic and fails EEXIST: rename could overwrite.
  fs.linkSync(stage,destination);
  fs.unlinkSync(stage);
  return {total,count};
}
async function digest(file){
  const hash=crypto.createHash('sha256');
  for await(const b of fs.createReadStream(file))hash.update(b);
  return hash.digest('hex');
}
async function mustReject(name,work){
  let rejected=false;
  try{await work();}catch(_){rejected=true;}
  assert(rejected,name+'_WAS_ACCEPTED');
  results.push({phase:name,pass:true});
}
(async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'d18-p0d-stream-'));
  try{
    const source=path.join(dir,'synthetic-cipher.bin');
    const archive=path.join(dir,'whole-cipher-v2.stream');
    const stage=path.join(dir,'restore.partial');
    const dest=path.join(dir,'restore.cipher');
    await createSyntheticCiphertext(source);
    const exported=await seal(source,archive);
    assert(exported.total===SIZE && exported.count>256,'EXPORT_SHORT');
    results.push({phase:'seal_above_16_mib_streamed',pass:true,
      bytes:exported.total,chunks:exported.count});
    await mustReject('wrong_passphrase',()=>restore(archive,
      path.join(dir,'badpass.partial'),path.join(dir,'badpass.cipher'),
      scope,'D18-CI-WRONG-PASSPHRASE-2026'));
    await mustReject('wrong_scope',()=>restore(archive,
      path.join(dir,'badscope.partial'),path.join(dir,'badscope.cipher'),
      'amina_vault_v1_native_812',pass));
    await mustReject('crash_quarantined',()=>restore(archive,
      path.join(dir,'crash.partial'),path.join(dir,'crash.cipher'),
      scope,pass,{interruptAfter:2}));
    assert(fs.statSync(path.join(dir,'crash.partial')).size===2*BLOCK &&
      !fs.existsSync(path.join(dir,'crash.cipher')),'QUARANTINE_NOT_PRESERVED');
    results.push({phase:'partial_archive_never_promoted',pass:true});
    await mustReject('refuse_partial_overwrite',()=>restore(archive,
      path.join(dir,'crash.partial'),path.join(dir,'crash.cipher'),
      scope,pass));
    const recovered=await restore(archive,stage,dest,scope,pass);
    assert(recovered.total===SIZE &&
      await digest(source)===await digest(dest),'ROUNDTRIP_MISMATCH');
    assert(!fs.existsSync(stage),'STAGE_NOT_REMOVED_AFTER_VERIFIED_COMMIT');
    results.push({phase:'verified_fresh_restore_exact_digest',pass:true});
    await mustReject('refuse_destination_overwrite',()=>restore(archive,
      path.join(dir,'duplicate.partial'),dest,scope,pass));
    assert(await digest(source)===await digest(dest),'DUPLICATE_CORRUPTED');
    results.push({phase:'destination_still_intact',pass:true});
  }catch(e){
    results.push({phase:'harness',pass:false,
      error:String(e.message||e.name).replace(/[^A-Za-z0-9_]/g,'_').slice(0,110)});
    process.exitCode=1;
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
  console.log(JSON.stringify({kind:'D18_P0D_SYNTHETIC_STREAM_REFERENCE',
    head:process.env.GITHUB_SHA||null,results,
    limitations:'Node disk-file model ONLY, not Web/Drift/sqlite3mc proof'}));
})().catch(e=>{console.error('D18_P0D_FATAL',e.name);process.exitCode=1;});
