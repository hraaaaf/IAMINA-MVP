{{flutter_js}}
{{flutter_build_config}}

// Never make online application startup depend on service-worker readiness.
_flutter.loader.load();

if ('serviceWorker' in navigator) {
  const registerIaminaServiceWorker = () => {
    navigator.serviceWorker
      .register('iamina_service_worker.js', {
        scope: './',
        updateViaCache: 'none',
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
