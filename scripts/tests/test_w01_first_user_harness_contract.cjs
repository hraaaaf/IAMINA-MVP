const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');

test('first-user script selects actual searchable country suggestion', () => {
  const suite = fs.readFileSync(path.join(root, 'tools/first_user_prod_e2e.js'), 'utf8');
  const screen = fs.readFileSync(path.join(root, 'frontend/lib/features/auth/onboarding_chat_screen.dart'), 'utf8');
  const fr = JSON.parse(fs.readFileSync(path.join(root, 'frontend/lib/l10n/app_fr.arb'), 'utf8'));
  assert.match(suite, /await selectCountrySearch\(page, 'Maroc'\)/);
  assert.doesNotMatch(suite, /await clickText\(page, \['Maroc'\]\)/);
  assert.match(suite, /await page.keyboard.type\(country,/);
  assert.match(suite, /await clickText\(page, \[country\],/);
  assert.match(screen, /DropdownMenu<CountryChoice>/);
  assert.match(screen, /Key\('onboarding-country-search'\)/);
  assert.match(screen, /if \(_country != null\)/);
  assert.ok(suite.includes("await expectText(page, '" + fr.onboardingTypeQuestion + "', 6000)"));
});

test('D6 tone selector removed from first-user script', () => {
  const suite = fs.readFileSync(path.join(root, 'tools/first_user_prod_e2e.js'), 'utf8');
  assert.doesNotMatch(suite, /Simple et chaleureux|Neutre et professionnel/);
  assert.match(suite, /await clickText\(page, \['Diabète Type 2'\]\)/);
});

test('static contract never launches browser or performs signup', () => {
  const source = fs.readFileSync(__filename, 'utf8');
  assert.doesNotMatch(source, /chromium\.launch|require\(['"]playwright['"]\)|https:\/\/iamina-review/);
});
