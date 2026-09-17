const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const targetUrl = process.env.TD014_URL || 'http://localhost:7360/';
const outDir = process.env.TD014_OUT || 'td014-app-lock-proof';
fs.mkdirSync(outDir, { recursive: true });

const fail = (message, details = {}) => {
  fs.writeFileSync(
    path.join(outDir, 'browser-cert.json'),
    JSON.stringify({ ok: false, message, ...details }, null, 2),
  );
  throw new Error(message);
};

const tamperBase64UrlBytes = (value) => {
  const bytes = Buffer.from(value, 'base64url');
  if (bytes.length === 0) throw new Error('Cannot tamper an empty public key');
  bytes[Math.floor(bytes.length / 2)] ^= 0x01;
  return bytes.toString('base64url');
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrors.push(error.message));

  const cdp = await context.newCDPSession(page);
  await cdp.send('WebAuthn.enable', { enableUI: false });
  const { authenticatorId } = await cdp.send('WebAuthn.addVirtualAuthenticator', {
    options: {
      protocol: 'ctap2',
      transport: 'internal',
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true,
    },
  });

  try {
    await page.goto(targetUrl, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => Boolean(window.iaminaAppLock), null, {
      timeout: 30000,
    });

    const capability = await page.evaluate(async () =>
      JSON.parse(await window.iaminaAppLock.capability()),
    );
    if (!capability.ok || capability.capability !== 'supported') {
      fail('Virtual platform authenticator was not reported as supported', {
        capability,
        consoleErrors,
      });
    }

    const enrollment = await page.evaluate(async () =>
      JSON.parse(await window.iaminaAppLock.enroll()),
    );
    if (!enrollment.ok || !enrollment.credential) {
      fail('WebAuthn enrollment failed', { enrollment, consoleErrors });
    }

    const credential = enrollment.credential;
    if (
      credential.origin !== new URL(targetUrl).origin ||
      credential.rpId !== new URL(targetUrl).hostname ||
      !credential.credentialId ||
      !credential.publicKeySpki
    ) {
      fail('Enrollment did not bind the expected origin/RP/public key', {
        credential,
      });
    }

    // The page and app-lock bridge are already loaded. Cutting all browser
    // network proves unlock itself does not depend on Vercel/Django/any server.
    await context.setOffline(true);
    const offlineUnlock = await page.evaluate(async (stored) =>
      JSON.parse(await window.iaminaAppLock.unlock(JSON.stringify(stored))),
      credential,
    );
    if (!offlineUnlock.ok) {
      fail('Offline WebAuthn unlock failed', { offlineUnlock });
    }

    await cdp.send('WebAuthn.setUserVerified', {
      authenticatorId,
      isUserVerified: false,
    });
    const noUvUnlock = await page.evaluate(async (stored) =>
      JSON.parse(await window.iaminaAppLock.unlock(JSON.stringify(stored))),
      { ...credential, signCount: offlineUnlock.signCount },
    );
    if (noUvUnlock.ok) {
      fail('Unlock incorrectly succeeded without user verification', {
        noUvUnlock,
      });
    }

    await cdp.send('WebAuthn.setUserVerified', {
      authenticatorId,
      isUserVerified: true,
    });
    const tampered = {
      ...credential,
      publicKeySpki: tamperBase64UrlBytes(credential.publicKeySpki),
    };
    if (tampered.publicKeySpki === credential.publicKeySpki) {
      fail('Public-key tamper helper did not alter encoded key bytes');
    }
    const tamperedUnlock = await page.evaluate(async (stored) =>
      JSON.parse(await window.iaminaAppLock.unlock(JSON.stringify(stored))),
      tampered,
    );
    if (tamperedUnlock.ok) {
      fail('Unlock incorrectly accepted a tampered public key', {
        tamperedUnlock,
      });
    }

    const report = {
      ok: true,
      targetOrigin: credential.origin,
      rpId: credential.rpId,
      credentialIdBytesApprox: Math.floor(credential.credentialId.length * 0.75),
      publicKeyStoredLocally: true,
      offlineUnlock: true,
      userVerificationFailClosed: true,
      tamperedPublicKeyFailClosed: true,
      applicationNetworkRequiredForUnlock: false,
      consoleErrors,
    };
    fs.writeFileSync(
      path.join(outDir, 'browser-cert.json'),
      JSON.stringify(report, null, 2),
    );
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await context.setOffline(false).catch(() => {});
    await cdp
      .send('WebAuthn.removeVirtualAuthenticator', { authenticatorId })
      .catch(() => {});
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
