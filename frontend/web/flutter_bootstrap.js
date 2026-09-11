{{flutter_js}}
{{flutter_build_config}}

_flutter.loader.load();

if ('serviceWorker' in navigator) {
  const registerIaminaServiceWorker = () => {
    navigator.serviceWorker
      .register('iamina_service_worker.js', {
        scope: './',
        updateViaCache: 'none',
      })
      .then((registration) => {
        // A navigation may already trigger a service-worker update check.
        // Defer our explicit check so it is not coalesced with registration/navigation.
        // This never blocks Flutter startup and never forces activation.
        window.setTimeout(() => {
          registration.update().catch((error) => {
            console.warn('IAMINA service worker update check failed', error);
          });
        }, 3000);
      })
      .catch((error) => {
        console.warn('IAMINA service worker registration failed', error);
      });
  };

  if (document.readyState === 'complete') {
    registerIaminaServiceWorker();
  } else {
    window.addEventListener('load', registerIaminaServiceWorker, { once: true });
  }
}
