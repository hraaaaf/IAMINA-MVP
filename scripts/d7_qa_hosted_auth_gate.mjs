// D7 hosted QA AUTH-ONLY gate. No clinical writes, no secrets in logs/artifacts.
const EXPECTED_ORIGIN =
  'https://iamina-review-ggdtqis0g-achraf-benmoussa-s-projects.vercel.app';

function fail(code) { throw new Error('D7_QA_' + code); }
function assertCredentials(creds) {
  for (const key of ['aEmail', 'aPassword', 'bEmail', 'bPassword', 'accessBypass']) {
    if (typeof creds[key] !== 'string' || !creds[key]) fail('REQUIRED_SECRET_MISSING');
  }
  if (creds.aEmail === creds.bEmail) fail('SAME_QA_IDENTITY');
}
async function requestJson(fetcher, origin, path, options, stage) {
  let response;
  try {
    response = await fetcher(origin + path, {
      redirect: 'manual',
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
      ...options,
    });
  } catch { fail(stage + '_NETWORK_ERROR'); }
  const status = response.status;
  const type = response.headers.get('content-type') || '';
  if (status >= 300 && status < 400) {
    await response.body?.cancel();
    fail(stage + '_SSO_REDIRECT');
  }
  if (!type.toLowerCase().includes('application/json')) {
    await response.body?.cancel();
    fail(stage + '_NON_JSON_' + status);
  }
  let data;
  try { data = await response.json(); } catch { fail(stage + '_JSON_INVALID'); }
  return { status, data };
}
export async function runHostedAuthGate({
  fetcher = globalThis.fetch, origin = EXPECTED_ORIGIN, creds,
}) {
  if (origin !== EXPECTED_ORIGIN) fail('UNEXPECTED_TARGET');
  assertCredentials(creds);
  const headers = {
    'content-type': 'application/json', accept: 'application/json',
    origin,
    'x-vercel-protection-bypass': creds.accessBypass,
  };
  // An invalid synthetic credential must reach Django and return its
  // native JSON 401, not the Vercel SSO HTML challenge or Flutter SPA.
  const negative = await requestJson(fetcher, origin, '/api/v1/auth/login', {
    method: 'POST', headers,
    body: JSON.stringify({email: 'nonexistent-d7-probe@example.invalid', password: 'synthetic-wrong'}),
  }, 'NEGATIVE');
  if (negative.status !== 401) fail('NEGATIVE_WRONG_STATUS_' + negative.status);

  const identities = {};
  for (const [step, email, password] of [
    ['A1', creds.aEmail, creds.aPassword],
    ['B', creds.bEmail, creds.bPassword],
    ['A2', creds.aEmail, creds.aPassword],
  ]) {
    const {status, data} = await requestJson(fetcher, origin, '/api/v1/auth/login', {
      method: 'POST', headers,
      body: JSON.stringify({email, password}),
    }, step);
    if (status !== 200) fail(step + '_LOGIN_STATUS_' + status);
    if (!data || !Number.isSafeInteger(data.user?.id) ||
        data.user.id <= 0 || typeof data.user?.email !== 'string' ||
        data.user.email.toLowerCase() !== email.toLowerCase() ||
        data.token_type !== 'Bearer' ||
        typeof data.access_token !== 'string' ||
        !data.access_token.startsWith('iamina.')) {
      fail(step + '_BAD_RESPONSE_CONTRACT');
    }
    // Only IDs in volatile memory for comparing owner binding.
    // Never serialize user identity, email, session or bearer.
    identities[step] = data.user.id;
  }
  if (identities.A1 === identities.B || identities.A1 !== identities.A2)
    fail('OWNER_A_B_A_MISMATCH');

  return {
    verdict: 'AUTH_ONLY_PASS',
    hosted_preview_sha: 'ec5234476618f849c68489adb08dfe7fd00a2c4c',
    negative_login: '401_JSON',
    existing_account_login: 'A_200_B_200_A_200',
    distinct_owners: true,
    stable_a_owner: true,
    browser_profile_and_treatment_fue: 'NOT_RUN',
  };
}
if (process.argv[1]?.endsWith('d7_qa_hosted_auth_gate.mjs')) {
  const creds = {
    aEmail: process.env.D7_QA_A_EMAIL,
    aPassword: process.env.D7_QA_A_PASSWORD,
    bEmail: process.env.D7_QA_B_EMAIL,
    bPassword: process.env.D7_QA_B_PASSWORD,
    accessBypass: process.env.D7_QA_SSO_ACCESS,
  };
  runHostedAuthGate({creds}).then(
    result => {console.log(JSON.stringify(result));},
    error => {
      // Errors carry only stable codes/status; never print raw exception stacks.
      console.error(/^D7_QA_[A-Z0-9_]+$/.test(error.message)
        ? error.message : 'D7_QA_UNKNOWN_FAILURE');
      process.exitCode = 1;
    },
  );
}
