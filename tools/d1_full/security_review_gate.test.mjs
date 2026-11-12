import test from 'node:test';
import assert from 'node:assert/strict';
import {inspect} from './security_review_gate.mjs';
test('D1 security review preserves known critical patient-release NO-GO',()=>{
 const r=inspect();
 assert.equal(r.patientRelease,'NO_GO');
 assert.equal(r.type,'INTERNAL_READ_ONLY_GATE');
 assert.equal(r.blockers.patientOpensPlainSqlite,true);
 assert.equal(r.blockers.patientBackupReturnsPlainJson,true);
 assert.equal(r.blockers.productionControllerUsesUnkeyedFactory,true);
 assert.equal(r.blockers.mainDoesNotGateDbAdmissionOnUnlock,true);
 assert.ok(r.blockingCount>=4);
});
test('D1 security review cannot claim independent reviewer or physical Safari',()=>{
 const r=inspect();
 assert.equal(r.blockers.physicalSafariNotProvided,true);
 assert.equal(r.blockers.independentReviewerNotAssigned,true);
});
