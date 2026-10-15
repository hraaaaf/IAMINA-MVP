import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeDigits,numericTokens,unitTokens,scoreTranscription} from '../src/metrics.mjs';
const c={id:'unit',expectedNumbers:['108','6.7'],expectedUnits:['mg/dl','%'],expectedLines:['GLYCEMIE 108 mg/dL','HbA1c 6.7 %']};
test('exact facts pass',()=>assert.equal(scoreTranscription(c,'GLYCEMIE 108 mg/dL\nHbA1c 6.7 %').safeForReview,true));
test('OCR 1O8 cannot silently become 108',()=>assert.equal(scoreTranscription(c,'GLYCEMIE 1O8 mg/dL\nHbA1c 6.7 %').safeForReview,false));
test('extra number fails',()=>assert.equal(scoreTranscription(c,'GLYCEMIE 108 mg/dL\nHbA1c 6.7 %\n108').safeForReview,false));
test('unit mismatch fails',()=>assert.equal(scoreTranscription(c,'GLYCEMIE 108 mmol/L\nHbA1c 6.7 %').safeForReview,false));
test('HbA1c label does not create phantom 1',()=>assert.deepEqual(numericTokens('HbA1c 6.7 %'),['6.7']));
test('Arabic digits preserve numeric value',()=>{assert.equal(normalizeDigits('١٢٦ ۷.۴'),'126 7.4'); assert.deepEqual(numericTokens('سكر الدم ١٢٦ mg/dL'),['126']);});
test('units are not inferred',()=>assert.deepEqual(unitTokens('108 mg / dL; 7,4 mmol/L; 80 µmol / L; 6.7 %'),['mg/dl','mmol/l','µmol/l','%']));
test('repeated counts require exact multiplicity',()=>assert.equal(scoreTranscription({id:'dup',expectedNumbers:['54','54'],expectedUnits:[]},'54').safeForReview,false));
test('HbA1c corruption fails despite correct numbers',()=>assert.equal(scoreTranscription({...c,expectedLabels:['HbA1c']},'GLYCEMIE 108 mg/dL\nHbAlc 6.7 %').safeForReview,false));
test('Arabic label must survive',()=>assert.equal(scoreTranscription({id:'ar',expectedNumbers:['54'],expectedUnits:['mg/dl'],expectedLabels:['سكر الدم']},'54 mg/dL').safeForReview,false));

test('critical values swapped across labels must fail despite exact token sets',()=>{
  assert.equal(scoreTranscription({...c,expectedLabels:['GLYCEMIE','HbA1c']},
    'GLYCEMIE 6.7 mg/dL\nHbA1c 108 %').safeForReview,false);
});
test('missing expected source rows must fail closed',()=>{
  assert.equal(scoreTranscription({id:'missing',expectedNumbers:['54'],expectedUnits:['mg/dl']},
    '54 mg/dL').safeForReview,false);
});
test('row order may change while critical values stay bound',()=>{
  assert.equal(scoreTranscription({...c,expectedLabels:['GLYCEMIE','HbA1c']},
    'HbA1c 6.7 %\nGLYCEMIE 108 mg/dL').safeForReview,true);
});
