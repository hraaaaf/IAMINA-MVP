const fs = require('fs');
const path = require('path');

const dir = process.env.E2E_OUT || 'first-user-prod-e2e';
const read = name => fs.readFileSync(path.join(dir, name), 'utf8');
const result = JSON.parse(read('result.json'));
const chat = read('10-first-chat.txt').replace(/\s+/g, ' ');
const requiredReading = '128 mg/dL';
const deviceSource = 'sur cet appareil';
const statuses = [
  'en attente de synchronisation',
  'marquée comme synchronisée',
  'dernière tentative de synchronisation a échoué',
];
const reportedStatus = statuses.find(x => chat.includes(x));
const checks = {
  recordedReadingObserved: chat.includes(requiredReading),
  deviceProvenanceVisible: chat.includes(deviceSource),
  syncProvenanceVisible: Boolean(reportedStatus),
  chatBackend200: result.chatStatus === 200,
  firstReadingPersisted: result.readingPersisted === true,
  firstInsightVisible: result.firstContextualInsight === 'Dans votre cible',
};
const output = {
  releaseUrl: result.base,
  viewport: result.viewport,
  checks,
  observedSyncState: reportedStatus || null,
  passed: Object.values(checks).every(Boolean),
};
fs.writeFileSync(path.join(dir, 'ux95-postdeploy-checks.json'), JSON.stringify(output, null, 2));
if (!output.passed) {
  console.error('UX95 failed checks:', Object.keys(checks).filter(x => !checks[x]).join(', '));
  process.exit(1);
}
console.log('UX95 real first-use provenance checks passed.');
