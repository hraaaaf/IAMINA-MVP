'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('playwright');

const output = process.env.AUDIT_OUT;
const phase = process.env.AUDIT_PHASE;
if (!output || !['before', 'after'].includes(phase)) {
  throw new Error('AUDIT_OUT and AUDIT_PHASE=before|after are required');
}
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    for (const mode of ['cards', 'hero', 'agp']) {
      const page = await browser.newPage({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 1,
        locale: 'fr-FR',
        colorScheme: 'light',
      });
      try {
        await page.goto(
          `http://127.0.0.1:7367/?surface=summary-kpi-cert&mode=${mode}`,
          { waitUntil: 'domcontentloaded', timeout: 45000 },
        );
        await page.waitForTimeout(6000);
        const pane = await page.locator('flt-glass-pane').count();
        if (!pane) throw new Error(`Flutter renderer absent in ${phase}/${mode}`);
        const target = path.join(output, `${phase}-${mode}-390x844.png`);
        await page.screenshot({ path: target });
        const data = fs.readFileSync(target);
        if (data.length < 7000) throw new Error(`Empty UI capture ${target}`);
        console.log(`${phase} ${mode}: ${data.length} bytes, sha256=${crypto.createHash('sha256').update(data).digest('hex')}`);
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  if (phase === 'after') {
    for (const mode of ['cards', 'hero', 'agp']) {
      const before = fs.readFileSync(path.join(output, `before-${mode}-390x844.png`));
      const after = fs.readFileSync(path.join(output, `after-${mode}-390x844.png`));
      if (before.equals(after)) throw new Error(`Missing visual difference for ${mode}`);
      console.log(`Visual difference detected for ${mode}; screenshots archived for review`);
    }
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
