const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.IAMINA_PROD_URL || 'https://iamina-review.vercel.app';
const OUT = process.env.E2E_OUT || 'first-user-prod-e2e';
fs.mkdirSync(OUT, { recursive: true });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();
let browser;
const runtimeEvents = [];
let chatResponse = null;

function routeOf(page) {
  const url = new URL(page.url());
  return `${url.pathname}${url.hash}`;
}

async function enableFlutterSemantics(page) {
  const placeholder = page.locator('flt-semantics-placeholder');
  if (await placeholder.count()) {
    await placeholder.first().focus();
    await page.keyboard.press('Enter');
    await sleep(500);
  }
}

async function observableText(page) {
  const semantics = await page.locator('flt-semantics').evaluateAll(els =>
    els.flatMap(e => [
      e.getAttribute('aria-label'),
      e.getAttribute('aria-valuetext'),
      e.getAttribute('value'),
      e.textContent,
    ]).filter(Boolean)
  ).catch(() => []);
  const body = await page.locator('body').innerText().catch(() => '');
  return normalize([...semantics, body].join(' '));
}

async function capture(page, name) {
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false });
  const semantics = await page.locator('flt-semantics').evaluateAll(els =>
    els.map(e => {
      const role = e.getAttribute('role');
      const label = e.getAttribute('aria-label');
      const valueText = e.getAttribute('aria-valuetext');
      const disabled = e.getAttribute('aria-disabled');
      const text = normalize(e.textContent);
      return [
        role ? `role=${role}` : '',
        label ? `label=${label}` : '',
        valueText ? `value=${valueText}` : '',
        disabled ? `disabled=${disabled}` : '',
        text ? `text=${text}` : '',
      ].filter(Boolean).join(' | ');
    }).filter(Boolean)
  ).catch(() => []);
  fs.writeFileSync(`${OUT}/${name}.txt`, [`URL: ${page.url()}`, ...semantics].join('\n'));
}

async function waitPath(page, part, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (routeOf(page).includes(part)) return;
    await sleep(250);
  }
  throw new Error(`Expected path containing ${part}, got ${page.url()}`);
}

async function waitAnyPath(page, parts, timeout = 25000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const route = routeOf(page);
    const match = parts.find(part => route.includes(part));
    if (match) return match;
    await sleep(250);
  }
  throw new Error(`Expected one of paths ${parts.join(', ')}, got ${page.url()}`);
}

async function expectText(page, text, timeout = 15000) {
  const needle = normalize(text);
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if ((await observableText(page)).includes(needle)) return;
    await sleep(250);
  }
  throw new Error(`Expected observable text: ${text}`);
}

async function clickText(page, texts, timeout = 12000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    for (const text of texts) {
      const candidates = [
        page.getByRole('button', { name: text, exact: false }),
        page.getByRole('radio', { name: text, exact: false }),
        page.getByRole('checkbox', { name: text, exact: false }),
        page.getByText(text, { exact: false }),
      ];
      for (const loc of candidates) {
        const count = await loc.count();
        for (let i = 0; i < count; i++) {
          const el = loc.nth(i);
          if (!(await el.isVisible().catch(() => false))) continue;
          if (!(await el.isEnabled().catch(() => true))) continue;
          await el.scrollIntoViewIfNeeded().catch(() => {});
          await el.click({ timeout: 3000 });
          return text;
        }
      }
    }
    await sleep(250);
  }
  throw new Error(`None of controls clickable: ${texts.join(' | ')}`);
}

async function activateButton(page, name, timeout = 15000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const buttons = page.getByRole('button', { name, exact: true });
    const count = await buttons.count();
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      if (!(await button.isVisible().catch(() => false))) continue;
      if (!(await button.isEnabled().catch(() => false))) continue;
      await button.scrollIntoViewIfNeeded().catch(() => {});
      await button.focus();
      await page.keyboard.press('Enter');
      return;
    }
    await sleep(250);
  }
  throw new Error(`Enabled button not found: ${name}`);
}

async function waitButtonEnabled(page, name, timeout = 10000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const buttons = page.getByRole('button', { name, exact: true });
    const count = await buttons.count();
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      if (await button.isVisible().catch(() => false) && await button.isEnabled().catch(() => false)) {
        return button;
      }
    }
    await sleep(250);
  }
  throw new Error(`Button stayed disabled: ${name}`);
}

async function visibleTextbox(page, index = 0, timeout = 10000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const boxes = page.getByRole('textbox');
    const visible = [];
    const count = await boxes.count();
    for (let i = 0; i < count; i++) {
      const box = boxes.nth(i);
      if (await box.isVisible().catch(() => false) && await box.isEnabled().catch(() => true)) visible.push(box);
    }
    if (visible.length > index) return visible[index];
    await sleep(250);
  }
  throw new Error(`Visible textbox ${index} not found`);
}

async function keyboardType(page, locator, text) {
  await locator.scrollIntoViewIfNeeded().catch(() => {});
  await locator.focus();
  await page.keyboard.press('Control+A').catch(() => {});
  await page.keyboard.press('Backspace').catch(() => {});
  await page.keyboard.type(text, { delay: 35 });
  await sleep(500);
}

async function unlockIfNeeded(page, expectedPath) {
  await sleep(1200);
  await enableFlutterSemantics(page);
  if (routeOf(page).includes('/app-lock/unlock')) {
    await capture(page, 'app-lock-unlock');
    await activateButton(page, 'Déverrouiller IAmina', 20000);
    await waitPath(page, expectedPath, 20000);
    await sleep(1000);
    await enableFlutterSemantics(page);
  } else {
    await waitPath(page, expectedPath, 20000);
  }
}

async function waitForChatResponse(page, timeout = 60000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (chatResponse) return chatResponse;
    const text = await observableText(page);
    if (/temporairement indisponible|limite temporaire|session n’est plus valide|réponse n’a pas pu être chargée/i.test(text)) {
      throw new Error(`Chat UI reported failure before a successful backend response`);
    }
    await sleep(300);
  }
  throw new Error('No /api/v1/ai/chat response observed');
}

(async () => {
  browser = await chromium.launch({ headless: true, args: ['--force-renderer-accessibility'] });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    locale: 'fr-FR',
    colorScheme: 'light',
    serviceWorkers: 'block',
  });
  const page = await context.newPage();

  page.on('console', msg => runtimeEvents.push(`console:${msg.type()}:${msg.text()}`));
  page.on('pageerror', err => runtimeEvents.push(`pageerror:${err.message}`));
  page.on('requestfailed', req => runtimeEvents.push(`requestfailed:${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`));
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/v1/')) {
      runtimeEvents.push(`response:${response.status()} ${response.request().method()} ${url}`);
    }
    if (url.includes('/api/v1/ai/chat') && response.request().method() === 'POST') {
      let payload = null;
      try { payload = await response.json(); } catch (_) {}
      chatResponse = { status: response.status(), payload };
    }
  });

  const cdp = await context.newCDPSession(page);
  await cdp.send('WebAuthn.enable');
  await cdp.send('WebAuthn.addVirtualAuthenticator', { options: {
    protocol: 'ctap2',
    transport: 'internal',
    hasResidentKey: true,
    hasUserVerification: true,
    isUserVerified: true,
    automaticPresenceSimulation: true,
  }});

  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(8000);
  await enableFlutterSemantics(page);
  await capture(page, '01-arrival');

  if (routeOf(page).includes('/login')) {
    await clickText(page, ['Créer un compte']);
    await expectText(page, 'Confirmer le mot de passe', 10000);
    const fields = page.getByRole('textbox');
    const count = await fields.count();
    if (count < 3) throw new Error(`Signup modal exposed only ${count} textboxes`);
    const unique = `e2e-first-user-${process.env.GITHUB_RUN_ID || Date.now()}-${process.env.GITHUB_RUN_ATTEMPT || 1}@example.invalid`;
    const password = 'IAmina-E2E-2026!Strong#42';
    await fields.nth(count - 3).fill(unique);
    await fields.nth(count - 2).fill(password);
    await fields.nth(count - 1).fill(password);
    await activateButton(page, 'Créer', 10000);
    await waitAnyPath(page, ['/app-lock/setup', '/onboarding'], 25000);
    await sleep(1000);
    await enableFlutterSemantics(page);
    await capture(page, '02-signup-result');
  }

  if (routeOf(page).includes('/app-lock/setup')) {
    await capture(page, '02-device-security');
    await activateButton(page, 'Activer le verrou sécurisé', 20000);
    await waitPath(page, '/onboarding', 20000);
    await sleep(1200);
    await enableFlutterSemantics(page);
  }

  await waitPath(page, '/onboarding', 20000);
  await expectText(page, 'Bonjour ! Je suis IAmina', 20000);
  await capture(page, '02-onboarding-arrival');
  await clickText(page, ['Français']);
  await clickText(page, ['Maroc']);
  await clickText(page, ['Simple et chaleureux', 'Neutre et professionnel']);
  await clickText(page, ['Diabète Type 2']);
  await clickText(page, ['Comprimés']);
  await clickText(page, ['mg/dL']);
  await capture(page, '03-onboarding-ready');

  await activateButton(page, 'Commencer', 10000);
  await waitPath(page, '/consent', 20000);
  await sleep(1200);
  await enableFlutterSemantics(page);
  await expectText(page, 'Continuer sans IA');
  await expectText(page, 'Accepter et continuer');
  await capture(page, '04-consent');

  await page.reload({ waitUntil: 'domcontentloaded' });
  await sleep(5000);
  await unlockIfNeeded(page, '/consent');
  const persistedOnboardingText = await observableText(page);
  if (routeOf(page).includes('/onboarding') || persistedOnboardingText.includes('Bonjour ! Je suis IAmina')) {
    throw new Error('Onboarding resurfaced after reload: persistence regression');
  }
  await capture(page, '05-consent-after-reload');

  await activateButton(page, 'Accepter et continuer', 15000);
  await waitPath(page, '/dashboard', 30000);
  await sleep(5000);
  await enableFlutterSemantics(page);
  await expectText(page, 'Ajouter ma première mesure', 20000);
  await capture(page, '06-empty-dashboard');

  await activateButton(page, 'Ajouter ma première mesure', 15000);
  await waitPath(page, '/ajouter', 15000);
  await sleep(1200);
  await enableFlutterSemantics(page);
  await capture(page, '07-new-reading');

  const glucoseBox = await visibleTextbox(page, 0, 10000);
  await keyboardType(page, glucoseBox, '128');
  await waitButtonEnabled(page, 'Enregistrer la mesure', 10000);
  const enteredGlucose = await glucoseBox.inputValue();
  if (enteredGlucose !== '128') throw new Error(`Glucose input mismatch: expected 128, got ${enteredGlucose}`);
  await capture(page, '07b-reading-entered');
  await activateButton(page, 'Enregistrer la mesure', 10000);
  await expectText(page, 'Mesure enregistrée.', 20000);
  await expectText(page, '128 mg/dL', 10000);
  await capture(page, '08-post-save-receipt');

  await activateButton(page, 'Terminer', 10000);
  await waitPath(page, '/dashboard', 20000);
  await sleep(4000);
  await enableFlutterSemantics(page);
  await expectText(page, '128', 15000);
  await expectText(page, 'Dans votre cible', 15000);
  await capture(page, '09-first-contextual-insight');

  await page.reload({ waitUntil: 'domcontentloaded' });
  await sleep(5000);
  await unlockIfNeeded(page, '/dashboard');
  await expectText(page, '128', 15000);
  await expectText(page, 'Dans votre cible', 15000);
  const afterReadingReload = await observableText(page);
  if (afterReadingReload.includes('Ajouter ma première mesure')) {
    throw new Error('Saved reading disappeared after reload');
  }
  await capture(page, '09b-reading-persisted-after-reload');

  await activateButton(page, 'Parler avec IAmina', 15000);
  await waitPath(page, '/companion/chat', 15000);
  await sleep(1500);
  await enableFlutterSemantics(page);
  await expectText(page, 'Conversation gouvernée', 10000);

  const prompt = 'Que peux-tu me dire de ma première mesure ?';
  const chatBox = await visibleTextbox(page, 0, 10000);
  await keyboardType(page, chatBox, prompt);
  await activateButton(page, 'Envoyer le message', 10000);
  await expectText(page, prompt, 15000);

  const response = await waitForChatResponse(page, 60000);
  if (response.status !== 200) {
    const code = response.payload && response.payload.code ? response.payload.code : 'unknown';
    throw new Error(`AI chat backend failed: HTTP ${response.status} code=${code}`);
  }
  const reply = response.payload && typeof response.payload.reply === 'string' ? response.payload.reply.trim() : '';
  if (!reply) throw new Error('AI chat backend returned no reply text');
  const replyProbe = normalize(reply).slice(0, 80);
  await expectText(page, replyProbe, 20000);
  await capture(page, '10-first-chat');

  fs.writeFileSync(`${OUT}/runtime.log`, runtimeEvents.join('\n'));
  fs.writeFileSync(`${OUT}/result.json`, JSON.stringify({
    ok: true,
    finalUrl: page.url(),
    base: BASE,
    viewport: '390x844',
    onboardingPersisted: true,
    readingPersisted: true,
    firstReading: '128 mg/dL',
    firstContextualInsight: 'Dans votre cible',
    chatStatus: response.status,
    assistantReplyObserved: true,
  }, null, 2));
  await browser.close();
})().catch(async err => {
  fs.writeFileSync(`${OUT}/failure.txt`, String(err && err.stack || err));
  fs.writeFileSync(`${OUT}/runtime.log`, runtimeEvents.join('\n'));
  console.error(err);
  if (browser) await browser.close().catch(() => {});
  process.exit(1);
});
