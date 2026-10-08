const fs = require('fs');
const path = require('path');

const dir = process.env.E2E_OUT || 'audit-prod-transversal';
const report = JSON.parse(fs.readFileSync(path.join(dir, 'result.json'), 'utf8'));
const byName = Object.fromEntries(report.routes.map(r => [r.name, r]));
const expected = [
  '03-accueil', '04-mesures', '05-rapports', '06-iamina',
  '07-iamina-chat', '08-import', '09-cgm', '10-profil',
  '11-rappels', '12-traitements',
];
const checks = {};
for (const route of expected) {
  const result = byName[route];
  checks[route + ': reachable'] = Boolean(result && !result.blocked && !result.error);
}
const text = route => String(byName[route]?.visibleText || '');
checks['Journal: importer shortcut'] = text('04-mesures').includes('Importer un document');
checks['Journal: CGM shortcut'] = text('04-mesures').includes('Connecter un CGM');
checks['Reports: descriptive title'] = text('05-rapports').includes('Rapport de vos mesures');
checks['Chat: governed role'] = text('07-iamina-chat').includes('Conversation gouvernée');
const result = {
  site: report.base,
  viewport: report.viewport,
  checkedRoutes: expected.length,
  checks,
  passed: Object.values(checks).every(Boolean),
};
fs.writeFileSync(path.join(dir, 'ux95-transversal-checks.json'), JSON.stringify(result, null, 2));
if (!result.passed) {
  console.error('Actual browser issues:', Object.keys(checks).filter(k => !checks[k]).join('; '));
  process.exit(1);
}
console.log('Live transversal route + Journal Import/CGM + Reports checks passed');
