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
    const modes = ['cards', 'hero', 'agp'].map(mode => [mode, 390, 844]);
    if (phase === 'after') {
      // Separate positive CGM rendering evidence, not fake paired baselines.
      modes.push(['agp-verified', 390, 844], ['agp-verified', 768, 1024]);
    }
    for (const [mode, width, height] of modes) {
      const page = await browser.newPage({
        viewport: { width, height },
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
        const target = path.join(output, `${phase}-${mode}-${width}x${height}.png`);
        await page.screenshot({ path: target });
        const data = fs.readFileSync(target);
        if (data.length < 7000) throw new Error(`Empty UI capture ${target}`);
        if (phase === 'after' && mode === 'agp-verified') {
          // An AGP with legends but a zero-width painter previously passed CI.
          // Inspect the actual screenshot pixels inside the chart, not just the
          // presence/size of CustomPaint or a nonempty screenshot.
          const stats = await page.evaluate(async (base64) => {
            const img = document.createElement('img');
            img.src = 'data:image/png;base64,' + base64;
            await img.decode();
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            if (!ctx) throw new Error('PNG pixel canvas unavailable');
            ctx.drawImage(img, 0, 0);
            const box = img.width === 390
              ? { x: 50, y: 160, w: 300, h: 110 }
              : { x: 65, y: 170, w: 660, h: 120 };
            const pixels = ctx.getImageData(box.x, box.y, box.w, box.h).data;
            let greenPixels = 0;
            for (let i = 0; i < pixels.length; i += 4) {
              const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
              if (g > r + 12 && g > b + 9) greenPixels += 1;
            }
            return { greenPixels, width: img.width, height: img.height };
          }, data.toString('base64'));
          if (stats.greenPixels < 100) {
            throw new Error(`AGP canvas appears blank in ${target}: ${JSON.stringify(stats)}`);
          }
          console.log(`Verified CGM chart painted: ${JSON.stringify(stats)}`);
        }
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
