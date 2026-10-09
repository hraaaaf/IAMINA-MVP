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
          let resolveReady;
          let rejectReady;
          const ready = new Promise((resolve, reject) => {
            resolveReady = resolve;
            rejectReady = reject;
          });
          page.on('console', (event) => {
            const line = event.text();
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
            const placeholder = page.locator('flt-semantics-placeholder');
            if (await placeholder.count()) {
              await placeholder.first().focus();
              await page.keyboard.press('Enter');
              await page.waitForTimeout(750);
            }
            // The synthetic saved profile is complete: the medical header
            // has "Suivi médical" but no first-use prompt.
            const medical = page.getByText('Suivi médical', { exact: true });
            await medical.last().click({ timeout: 10000 });
            await page.waitForTimeout(1000);
            const semantics = await page.locator('flt-semantics').evaluateAll(els =>
              els.map(el => el.getAttribute('aria-label') || el.textContent || '').join(' '));
            const expectedTitle = phase === 'before'
              ? 'Cible glycémique (mg/dL)'
              : 'Cible glycémique (mmol/L)';
            if (!semantics.includes(expectedTitle)) {
              throw new Error('Profile targets not visible: expected '+expectedTitle+
                ', observed '+semantics.slice(0,1800));
            }
            await page.mouse.wheel(0, 350);
            await page.waitForTimeout(400);
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
