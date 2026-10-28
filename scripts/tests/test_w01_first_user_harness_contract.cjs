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


test('synthetic QA remote auth requires exact branch and SHA', () => {
  const build = fs.readFileSync(path.join(root, 'frontend/vercel_build.sh'), 'utf8');
  const proxy = fs.readFileSync(path.join(root, 'frontend/api/preview-proxy.js'), 'utf8');
  assert.match(build, /IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false/);
  assert.match(build, /D2_WEB_SYNTHETIC_ONLY_V1/);
  assert.match(build, /VERCEL_GIT_COMMIT_REF/);
  assert.match(build, /IAMINA_PREVIEW_SYNTHETIC_REMOTE_LOGIN_SHA/);
  assert.match(build, /VERCEL_GIT_COMMIT_SHA/);
  assert.match(proxy, /function syntheticLoginScopeValid\(\)/);
  assert.match(proxy, /pinnedSha === process\.env\.VERCEL_GIT_COMMIT_SHA/);
  assert.match(proxy, /VERCEL_ENV === 'preview'/);
});

test('synthetic QA proxy blocks non-synthetic login and cross-DB access', () => {
  const proxy = fs.readFileSync(path.join(root, 'frontend/api/preview-proxy.js'), 'utf8');
  assert.match(proxy, /@example\\\.invalid/);
  assert.match(proxy, /route\.path === 'auth\/firebase'/);
  assert.match(proxy, /route\.path === 'auth\/password'/);
  assert.match(proxy, /syntheticLoginPayloadAllowed\(route\.path, payload\)/);
  assert.match(proxy, /!await syntheticIdentityVerified\(apiOrigin, oidcToken\)/);
  for (const name of ['database_name', 'role_name', 'neon_project_id', 'neon_branch_id']) {
    assert.ok(proxy.includes(name), 'missing independent DB identity field ' + name);
  }
});

test('patient Web encrypted vault remains denied by default', () => {
  const auth = fs.readFileSync(path.join(root, 'frontend/lib/services/auth_service.dart'), 'utf8');
  const login = fs.readFileSync(path.join(root, 'frontend/lib/features/auth/login_screen.dart'), 'utf8');
  assert.match(auth, /defaultValue: false/);
  assert.match(login, /if \(!kRemoteAccountEnrollmentEnabled\)/);
  assert.match(login, /LocalDeviceEnrollmentScreen/);
});
