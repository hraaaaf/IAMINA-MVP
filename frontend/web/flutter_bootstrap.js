{{flutter_js}}
{{flutter_build_config}}

_flutter.loader.load();

const IAMINA_REVIEW_STABLE_HOST = 'iamina-review.vercel.app';
const IAMINA_REVIEW_DEPLOYMENT_HOST_RE =
  /^iamina-review-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app$/i;
const isHostedIaminaReview =
  window.location.hostname === IAMINA_REVIEW_STABLE_HOST ||
  IAMINA_REVIEW_DEPLOYMENT_HOST_RE.test(window.location.hostname);

if ('serviceWorker' in navigator) {
  const runWhenLoaded = (callback) => {
    if (document.readyState === 'complete') {
      callback();
    } else {
      window.addEventListener('load', callback, { once: true });
    }
  };

  if (isHostedIaminaReview) {
    // Vercel is IAMINA's rapid dev/test surface. A cache-first PWA worker can
    // pin an older main.dart.js across deployments, so hosted review must use
    // the network artifact directly. The worker itself also performs one-time
    // cleanup so already-controlled clients can recover automatically.
    runWhenLoaded(() => {
      navigator.serviceWorker
        .getRegistrations()
        .then((registrations) =>
          Promise.all(registrations.map((registration) => registration.unregister())),
        )
        .catch((error) => {
          console.warn('IAMINA hosted-review service worker cleanup failed', error);
        });

      if ('caches' in window) {
        caches
          .keys()
          .then((names) =>
            Promise.all(
              names
                .filter((name) => name.startsWith('iamina-app-shell-'))
                .map((name) => caches.delete(name)),
            ),
          )
          .catch((error) => {
            console.warn('IAMINA hosted-review cache cleanup failed', error);
          });
      }
    });
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

    runWhenLoaded(registerIaminaServiceWorker);
  }
}
