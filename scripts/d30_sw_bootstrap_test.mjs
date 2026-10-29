// D30: verify release bootstrap tolerates an unavailable Service Worker.
// No browser/network/backend account, no clinical data.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(
  new URL('../frontend/web/flutter_bootstrap.js', import.meta.url),
  'utf8',
).replaceAll('{{flutter_js}}', '').replaceAll('{{flutter_build_config}}', '');

async function runCase(registration) {
  const warnings = [];
  const scheduled = [];
  let updateCalls = 0;
  let registrations = 0;
  const context = {
    _flutter: { loader: { load() {} } },
    window: {
      location: { hostname: 'localhost', origin: 'http://localhost' },
      setTimeout(callback) { scheduled.push(callback); },
      addEventListener() {},
    },
    document: { readyState: 'complete' },
    navigator: {
      serviceWorker: {
        register() {
          registrations += 1;
          return Promise.resolve(registration === null ? undefined : {
            update() { updateCalls += 1; return Promise.resolve(); },
          });
        },
      },
    },
    fetch: async () => ({
      ok: true,
      text: async () => "const IAMINA_CACHE_SCHEMA = 'd30-test';",
    }),
    console: { warn(...args) { warnings.push(args.join(' ')); } },
    caches: { keys: async () => [] },
    Promise,
    Date,
    encodeURIComponent,
  };
  vm.runInNewContext(source, context, { filename: 'flutter_bootstrap.js' });
  // Flush the async release probe and registration callbacks.
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(registrations, 1);
  for (const callback of scheduled) callback();
  await new Promise((resolve) => setImmediate(resolve));
  if (registration === null) {
    assert.equal(scheduled.length, 0, 'Cannot schedule update on undefined');
    assert.equal(updateCalls, 0);
    assert(warnings.some((line) => line.includes('no registration')));
  } else {
    assert.equal(scheduled.length, 1, 'Valid registration must still update');
    assert.equal(updateCalls, 1);
    assert(!warnings.some((line) => line.includes('no registration')));
  }
}

await runCase(null);
await runCase('valid');
console.log('D30 Web bootstrap PASS: missing SW registration is safe; valid registration updates');
