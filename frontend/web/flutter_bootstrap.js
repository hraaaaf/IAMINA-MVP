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
        registration.update().catch((error) => {
          console.warn('IAMINA service worker update check failed', error);
        });
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
