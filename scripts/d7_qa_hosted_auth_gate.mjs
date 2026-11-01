// D7 hosted QA AUTH-ONLY gate: temporary, deployment-scoped Vercel Share Link.
// Never log/share QA credentials, the share token, session cookie or bearer.
const EXPECTED_ORIGIN =
  'https://iamina-review-3boz2bqz6-achraf-benmoussa-s-projects.vercel.app';
const PREVIEW_SHA = '55fa500f56d86d7fa014b5b1849d7e7cdad3ea59';

function fail(code) { throw new Error('D7_QA_' + code); }
function assertCredentials(creds) {
  for (const key of ['aEmail', 'aPassword', 'bEmail', 'bPassword', 'accessBypass']) {
    if (typeof creds[key] !== 'string' || !creds[key]) fail('REQUIRED_SECRET_MISSING');
  }
  // Refuse real or unclassified identities before any outbound request.
  for (const email of [creds.aEmail, creds.bEmail]) {
    if (!/^[^@\s]+@example\.(invalid|test)$/.test(email.trim().toLowerCase()))
      fail('NON_SYNTHETIC_IDENTITY');
  }
  if (creds.aEmail.trim().toLowerCase() === creds.bEmail.trim().toLowerCase())
    fail('SAME_QA_IDENTITY');
}
async function shareLinkSession(fetcher, origin, shareToken) {
  let response;
  try {
    response = await fetcher(origin + '/?_vercel_share=' + encodeURIComponent(shareToken), {
      method: 'GET',
      redirect: 'manual',
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    });
  } catch { fail('SHARE_NETWORK_ERROR'); }
  // A Vercel Share Link is NOT the project-wide automation bypass secret.
  // It establishes an HttpOnly _vercel_jwt cookie via an initial redirect.
  const setCookies = typeof response.headers.getSetCookie === 'function'
    ? response.headers.getSetCookie()
    : [response.headers.get('set-cookie')].filter(Boolean);
  const cookie = setCookies.map(line => /(?:^|[,\s])_vercel_jwt=([^;,\s]+)/.exec(line))
    .find(Boolean);
  await response.body?.cancel();
  if (!cookie || response.status < 200 || response.status >= 400)
    fail('SHARE_COOKIE_UNAVAILABLE');
  return '_vercel_jwt=' + cookie[1];
}
async function verifyQaApp(fetcher, origin, cookie) {
  let response;
  try {
    response = await fetcher(origin + '/', {
      method: 'GET',
      headers: {cookie},
      redirect: 'manual',
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    });
  } catch { fail('QA_APP_NETWORK_ERROR'); }
  if (response.status !== 200 ||
      !(response.headers.get('content-type') || '').includes('text/html')) {
    await response.body?.cancel();
    fail('QA_APP_UNAVAILABLE');
  }
  const html = await response.text().catch(() => '');
  if (!html.includes('<title>IAMINA</title>') ||
      !html.includes('flutter_bootstrap.js')) fail('QA_APP_NOT_IAMINA');
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
  // This is the verified immutable Vercel Preview, not a mutable branch alias.
  if (process.env.D7_PREVIEW_SHA && process.env.D7_PREVIEW_SHA !== PREVIEW_SHA)
    fail('PREVIEW_SHA_MISMATCH');
  assertCredentials(creds);
  // Fail closed before sending any A/B password if the temporary link expired.
  const cookie = await shareLinkSession(fetcher, origin, creds.accessBypass);
  await verifyQaApp(fetcher, origin, cookie);
  const headers = {
    'content-type': 'application/json', accept: 'application/json',
    origin, cookie,
  };
  // A Vercel-generated 401 is not proof that Django received the request:
  // require the native Django error contract before sending QA passwords.
  const negative = await requestJson(fetcher, origin, '/api/v1/auth/login', {
    method: 'POST', headers,
    body: JSON.stringify({email: 'nonexistent-d7-probe@example.invalid', password: 'synthetic-wrong'}),
  }, 'NEGATIVE');
  if (negative.status !== 401 ||
      negative.data?.detail !== 'Invalid authentication credential')
    fail('NEGATIVE_NOT_DJANGO_AUTH');
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
        !data.access_token.startsWith('iamina.'))
      fail(step + '_BAD_RESPONSE_CONTRACT');
    // Compare IDs in memory only; do not emit owner IDs or tokens.
    identities[step] = data.user.id;
  }
  if (identities.A1 === identities.B || identities.A1 !== identities.A2)
    fail('OWNER_A_B_A_MISMATCH');
  return {
    verdict: 'AUTH_ONLY_PASS',
    preview_sha_pinned: PREVIEW_SHA,
    negative_login: 'DJANGO_401_JSON',
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
    // Short-lived Share Link's _vercel_share value, not an automation bypass.
    accessBypass: process.env.D7_QA_SSO_ACCESS,
  };
  runHostedAuthGate({creds}).then(
    result => {console.log(JSON.stringify(result));},
    error => {
      // Stable error code only: no request URLs, cookies, PHI, credentials.
      console.error(/^D7_QA_[A-Z0-9_]+$/.test(error.message)
        ? error.message : 'D7_QA_UNKNOWN_FAILURE');
      process.exitCode = 1;
    },
  );
}
