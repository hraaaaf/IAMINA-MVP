{{flutter_js}}
{{flutter_build_config}}

const iaminaServiceWorkerVersion = "{{flutter_service_worker_version}}";

async function waitForWorkerActivation(worker) {
  if (!worker || worker.state === 'activated') return;
  await new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error('IAMINA service worker activation timed out')),
      10000,
    );
    worker.addEventListener('statechange', () => {
      if (worker.state === 'activated') {
        clearTimeout(timer);
        resolve();
      } else if (worker.state === 'redundant') {
        clearTimeout(timer);
        reject(new Error('IAMINA service worker became redundant'));
      }
    });
  });
}

async function registerIaminaServiceWorker() {
  if (!('serviceWorker' in navigator)) return;

  try {
    const script = `iamina_service_worker.js?v=${encodeURIComponent(iaminaServiceWorkerVersion)}`;
    const registration = await navigator.serviceWorker.register(script, {
      scope: './',
      updateViaCache: 'none',
    });

    const candidate = registration.installing || registration.waiting;
    if (candidate) await waitForWorkerActivation(candidate);
    await navigator.serviceWorker.ready;

    if (!navigator.serviceWorker.controller) {
      await new Promise((resolve) => {
        const timer = setTimeout(resolve, 5000);
        navigator.serviceWorker.addEventListener(
          'controllerchange',
          () => {
            clearTimeout(timer);
            resolve();
          },
          { once: true },
        );
      });
    }
  } catch (error) {
    // Online startup remains available if service-worker registration itself fails.
    // The retained P5-4A browser proof separately fails closed on offline readiness.
    console.warn('IAMINA service worker registration failed', error);
  }
}

(async () => {
  await registerIaminaServiceWorker();
  _flutter.loader.load();
})();
