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
    for (const mode of ['edit', 'add', 'profile']) {
      for (const [width, height] of [[390, 844], [768, 1024]]) {
        const page = await browser.newPage({
          viewport: { width, height },
          deviceScaleFactor: 1,
          locale: 'fr-FR',
          colorScheme: 'light',
        });
        try {
          let profileProof = null;
          let resolveReady;
          let rejectReady;
          const ready = new Promise((resolve, reject) => {
            resolveReady = resolve;
            rejectReady = reject;
          });
          page.on('console', (event) => {
            const line = event.text();
            if (line.includes('V101_PROFILE_TARGETS ')) profileProof = line;
            if (line.includes('V101_UNIT_SWITCH_READY')) resolveReady();
            if (line.includes('V101_UNIT_SWITCH_ERROR')) rejectReady(new Error(line));
          });
          page.on('pageerror', rejectReady);
          await page.goto('http://127.0.0.1:7367/?mode=' + mode, {
            waitUntil: 'domcontentloaded', timeout: 45000,
          });
          await Promise.race([
            ready,
            page.waitForTimeout(45000).then(() => {
              throw new Error('Flutter synthetic input change not rendered: ' + mode);
            }),
          ]);
          await page.waitForTimeout(1000);
          if (mode === 'profile') {
            // The synthetic harness has opened the REAL medical accordion
            // through Flutter's ListTile.onTap. CanvasKit is not HTML text.
            // Verify values read back from the actual ProfileScreen fields.
            const expected = phase === 'before'
              ? 'low=70 high=180 title=Cible glycémique (mg/dL)'
              : 'low=3.9 high=10.0 title=Cible glycémique (mmol/L)';
            if (!profileProof || !profileProof.includes(expected)) {
              throw new Error('Profile widget mismatch: expected '+expected+
                ', observed '+String(profileProof).slice(0,700));
            }
            console.log('VERIFIED_PROFILE_WIDGET '+phase+' '+width+'x'+height+
              ': '+profileProof);
            await page.mouse.wheel(0, 350);
            await page.waitForTimeout(500);
          }
          if (!(await page.locator('flt-glass-pane').count())) {
            throw new Error('No real Flutter renderer: ' + mode);
          }
          const file = path.join(output, phase + '-' + mode +
            '-unit-switch-' + width + 'x' + height + '.png');
          await page.screenshot({ path: file });
          const bytes = fs.readFileSync(file);
          if (bytes.length < 7000) throw new Error('Blank real Flutter screenshot');
          console.log(file + ' ' + bytes.length + ' bytes, sha256=' +
            crypto.createHash('sha256').update(bytes).digest('hex'));
        } finally {
          await page.close();
        }
      }
    }
  } finally {
    await browser.close();
  }
})().catch(err => { console.error(err); process.exitCode = 1; });
