#!/usr/bin/env node
/* Synthetic-only tests for D18 WASM gate; NOT an encryption proof. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const gate=path.join(__dirname,'d18_sqlite_cipher_preflight.cjs');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'d18-wasm-gate-'));
const run=(...args)=>spawnSync(process.execPath,[gate,...args],{encoding:'utf8'});
try {
 let r=run();
 assert.equal(r.status,2,'missing candidate must fail closed');
 const fake=path.join(temp,'fake.wasm');
 fs.writeFileSync(fake,Buffer.alloc(2048,65));
 r=run(fake);
 assert.equal(r.status,1,'non-WASM candidate must be rejected');
 const malformed=path.join(temp,'malformed.wasm');
 fs.writeFileSync(malformed,Buffer.concat([Buffer.from('0061736d01000000','hex'),Buffer.alloc(2048,255)]));
 r=run(malformed);
 assert.equal(r.status,1,'malformed WASM must be rejected');
 // Valid minimal WASM with a custom section is NOT an encrypted SQLite engine.
 const valid=path.join(temp,'minimal.wasm');
 const custom=Buffer.concat([Buffer.from([0,0x80,0x08,0]),Buffer.alloc(1023)]);
 fs.writeFileSync(valid,Buffer.concat([Buffer.from('0061736d01000000','hex'),custom]));
 assert.doesNotThrow(()=>new WebAssembly.Module(fs.readFileSync(valid)));
 r=run(valid);
 assert.equal(r.status,1,'valid non-SQLite WASM must be rejected');
 assert.match(r.stderr,/not identifiable as a SQLite engine/);
 console.log('D18 WASM preflight: 4 synthetic checks PASS; encryption NOT tested');
} finally {fs.rmSync(temp,{recursive:true,force:true});}
