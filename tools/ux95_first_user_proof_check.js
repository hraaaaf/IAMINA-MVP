const fs = require('fs');
const path = require('path');

const dir = process.env.E2E_OUT || 'first-user-prod-e2e';
const load = name => fs.readFileSync(path.join(dir, name), 'utf8');
const result = JSON.parse(load('result.json'));
const demo = JSON.parse(load('ux95-demo-chat-checks.json'));
const photo = fs.statSync(path.join(dir, '10-first-chat.png'));
const checks = {
  firstReadingPersisted: result.readingPersisted === true,
  firstReading128: result.firstReading === '128 mg/dL',
  firstInsightVisible: result.firstContextualInsight === 'Dans votre cible',
  realChatBackend200: result.chatStatus === 200,
  firstChatScreenshotCaptured: photo.size > 30000,
  liveDemoDeviceFact: demo.checks.deviceReading && demo.checks.deviceSourceLabel,
  liveDemoSyncDisclosure: demo.checks.syncDisclosure,
  liveDemoNoInferredTrend: demo.checks.noUnsupportedTrend,
  governedFallbackTruthfullyLabeled: demo.checks.governedFallbackLabeled,
};
const output = {
  releaseUrl: result.base,
  viewport: result.viewport,
  scope: 'first-user actual E2E plus independent real demo chat continuity',
  checks,
  passed: Object.values(checks).every(Boolean),
};
fs.writeFileSync(path.join(dir, 'ux95-postdeploy-checks.json'), JSON.stringify(output, null, 2));
if (!output.passed) {
  console.error('Failed checks:', Object.keys(checks).filter(x => !checks[x]).join(', '));
  process.exit(1);
}
console.log('Real first-use flow plus demo local continuity checks passed.');
