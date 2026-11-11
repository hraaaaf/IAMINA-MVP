import test from 'node:test';
import assert from 'node:assert/strict';
import {inspect} from './gate_inventory.mjs';
test('D1-D: known patient encryption and backup blockers remain visible',()=>{
 const r=inspect('.');
 assert.equal(r.patientRelease,'NO_GO');
 assert.equal(r.findings.patientRuntimeUnkeyedDrift,true);
 assert.equal(r.findings.patientBackupPlainJson,true);
 assert.equal(r.findings.sessionControllerUsesUnkeyedConstructor,true);
});
test('D1-D: never infer clinical release from synthetic 2/2 browser probe',()=>{
 const r=inspect('.');
 assert.equal(r.patientRelease,'NO_GO');
 assert.ok(r.description.includes('NOT a release approval'));
});
