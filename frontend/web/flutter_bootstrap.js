{{flutter_js}}
{{flutter_build_config}}

_flutter.loader.load();

const IAMINA_HOSTED_REVIEW =
  window.location.hostname === 'iamina-review.vercel.app' ||
  (window.location.hostname.startsWith('iamina-review-') &&
    window.location.hostname.endsWith('.vercel.app'));

const cleanupHostedReviewCaches = async () => {
  try {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(
      registrations
        .filter((registration) =>
          registration.scope.startsWith(window.location.origin),
        )
        .map((registration) => registration.unregister()),
    );
  } catch (error) {
    console.warn('IAMINA hosted-review service worker cleanup failed', error);
  }

  try {
    const names = await caches.keys();
    await Promise.all(
      names
        .filter((name) => name.startsWith('iamina-app-shell-'))
        .map((name) => caches.delete(name)),
    );
  } catch (error) {
    console.warn('IAMINA hosted-review cache cleanup failed', error);
  }
};

if ('serviceWorker' in navigator) {
  if (IAMINA_HOSTED_REVIEW) {
    // Hosted Vercel is the dev/test surface. Do not preserve an offline shell
    // between deployments because it can hide the current candidate.
    cleanupHostedReviewCaches();
  } else {
    const IAMINA_FALLBACK_RELEASE = '0.1.0+1';

    const readCurrentIaminaRelease = async () => {
      try {
        const response = await fetch(
          `iamina_service_worker.js?release_probe=${Date.now()}`,
          {
            cache: 'no-store',
            credentials: 'same-origin',
          },
        );
        if (!response.ok) {
          throw new Error(`release probe HTTP ${response.status}`);
        }
        const text = await response.text();
        const match = text.match(/const IAMINA_CACHE_SCHEMA = '([^']+)';/);
        if (!match || !match[1]) {
          throw new Error('release marker missing from service worker');
        }
        return match[1];
      } catch (error) {
        console.warn(
          'IAMINA service worker release discovery failed; keeping installed release',
          error,
        );
        return IAMINA_FALLBACK_RELEASE;
      }
    };

    const registerIaminaServiceWorker = async () => {
      const release = await readCurrentIaminaRelease();
      const scriptUrl =
        `iamina_service_worker.js?release=${encodeURIComponent(release)}`;

      navigator.serviceWorker
        .register(scriptUrl, {
          scope: './',
          updateViaCache: 'none',
        })
        .then((registration) => {
          // Same-release changes are still checked without blocking startup.
          // Normal releases change IAMINA_CACHE_SCHEMA, which changes scriptUrl
          // and deterministically starts the browser update algorithm.
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
}
