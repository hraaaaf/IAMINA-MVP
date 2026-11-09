/* D19 controlled presentation source BEFORE vs AFTER screenshot evidence.
 * Historical BEFORE uses a pinned presentation file atop the same synthetic
 * Flutter App/API harness, NOT an invented screenshot of deployed production.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const before = path.resolve('d19-before-browser');
const after = path.resolve('d19-after-browser');
const load = dir => JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8'));
const a = load(before), b = load(after);
const gateA = b.gateA === true;
const pairs = [];
let invalid = 0;
for (const t of b.tests.filter(t=>t.scenario!=='recover')) {
  const prior = a.tests.find(q => q.filename === t.filename);
  if (!prior) { invalid++;continue; }
  const old = PNG.sync.read(fs.readFileSync(path.join(before,t.filename)));
  const cur = PNG.sync.read(fs.readFileSync(path.join(after,t.filename)));
  if (old.width!==cur.width||old.height!==cur.height) { invalid++; continue; }
  let delta=0;
  for(let idx=0;idx<old.data.length;idx+=4){
    const changes=Math.abs(old.data[idx]-cur.data[idx])
      +Math.abs(old.data[idx+1]-cur.data[idx+1])
      +Math.abs(old.data[idx+2]-cur.data[idx+2]);
    if(changes>=24)delta++;
  }
  pairs.push({locale:t.locale,viewport:t.viewport,scenario:t.scenario,
    width:cur.width,height:cur.height,
    changedPixels:delta,changedPercent:Math.round(delta/(cur.width*cur.height)*10000)/100,
    baselinePageErrors:prior.errors.length,afterPageErrors:t.errors.length,
    baselineExternalRequests:prior.outbound.length,afterExternalRequests:t.outbound.length,
    beforeSha256:prior.sha256,afterSha256:t.sha256});
}
const result={
  methodology:'Pinned historical presentation source on same synthetic D19 Flutter Web harness',
  beforePresentationGitSha:'a80bf8042c8d47d5bc1812f21b067989388b75a8',
  afterGitSha:process.env.GITHUB_SHA||'GitHub PR merge ref; see PR exact head',
  limitation:gateA?'D22 fail-closed comparison: historical presentation source can be unmounted and is not proof of historical production':'A controlled component source comparison, not the full historical hosted/production app',
  gateA,
  gateAWebSafetyProof:gateA?'24 real Flutter Web scenarios, no unauthorized AI requests, 2 distinct synthetic journal states per viewport':'not applicable',
  expectedPairs:18,pairs,invalid,afterFailures:b.failed.length,
  visuallyChangedPairs:pairs.filter(x=>x.changedPixels>2000).length,
  keyboardPositiveAfter:b.tests.filter(t=>t.keyboardPeriod7===true).length,
  keyboardNegativeBefore:a.tests.filter(t=>t.keyboardPeriod7===false).length,
  recoveryCasesAfter:b.tests.filter(t=>t.scenario==='recover').length,
  recoveryPassAfter:b.tests.filter(t=>t.scenario==='recover'&&t.recoveryPass===true).length,
};
fs.writeFileSync('d19-visual-comparison.json',JSON.stringify(result,null,2));
console.log('D19_BEFORE_AFTER='+JSON.stringify({pairs:pairs.length,invalid,afterFailures:b.failed.length,visuallyChangedPairs:result.visuallyChangedPairs}));
if(gateA){
  // Keep paired images, strict page errors, outbound network and no-AI checks.
  // D22 must NOT make calls simply to satisfy D19 retry/period API assertions.
  const guarded=b.tests.filter(t=>t.guardState==='targets-unverified');
  const leaked=b.tests.filter(t=>t.requestedDays?.length||t.recoveryDays?.length);
  const states=['fr','ar'].flatMap(loc=>['mobile','tablet','desktop'].map(viewport=>{
    const samples=b.tests.filter(t=>t.locale===loc&&t.viewport===viewport);
    return new Set(samples.map(t=>t.sha256)).size;
  }));
  if(pairs.length!==18||invalid||b.failed.length||guarded.length!==18||leaked.length||states.some(n=>n<2))process.exitCode=1;
}else if(pairs.length!==18||invalid||b.failed.length||result.visuallyChangedPairs<6||result.keyboardPositiveAfter!==2||result.recoveryPassAfter!==6)process.exitCode=1;
