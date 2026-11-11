{{flutter_js}}
{{flutter_build_config}}

// D1.8 P0: fail closed before starting ANY Flutter/Drift runtime in another
// tab of the same origin. This does not stop previously cached historical v5
// bundles, which remain a separate NO-CUTOVER gate.
(function iaminaSingleWebRuntime() {
  const key = 'iamina-web-patient-runtime-single-writer-v1';

  function block(reason) {
    document.documentElement.dataset.iaminaTabLease = reason;
    const fr = navigator.language.toLowerCase().startsWith('fr');
    const ar = navigator.language.toLowerCase().startsWith('ar');
    const title = reason === 'occupied'
      ? (ar ? 'صندوق IAMINA مفتوح في تبويب آخر'
        : fr ? 'Le coffre IAMINA est déjà ouvert'
        : 'IAMINA vault is open in another tab')
      : (ar ? 'الحماية متعددة التبويبات غير متاحة'
        : fr ? 'Protection du navigateur indisponible'
        : 'Browser protection unavailable');
    const message = reason === 'occupied'
      ? (ar ? 'أغلق تبويب IAMINA الآخر ثم حدّث هذه الصفحة.'
        : fr ? 'Fermez l’autre onglet IAMINA puis actualisez cette page.'
        : 'Close the other IAMINA tab, then reload this page.')
      : (ar ? 'لا يمكن فتح البيانات المحلية في هذا المتصفح بأمان.'
        : fr ? 'Ce navigateur ne peut pas ouvrir les données locales en sécurité.'
        : 'This browser cannot safely open local data.');
    document.title = title;
    const show = () => {
      if (!document.body) return;
      const main = document.createElement('main');
      main.setAttribute('role', 'alert');
      main.setAttribute('aria-live', 'assertive');
      main.style.cssText = 'max-width:32rem;margin:15vh auto;padding:1.5rem;font:16px system-ui;line-height:1.5';
      if (ar) main.dir = 'rtl';
      const heading = document.createElement('h1');
      heading.textContent = title;
      const description = document.createElement('p');
      description.textContent = message;
      main.append(heading, description);
      document.body.replaceChildren(main);
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', show, {once: true});
    } else {
      show();
    }
  }

  if (!window.isSecureContext ||
      typeof navigator.locks?.request !== 'function') {
    block('unavailable');
    return;
  }
  navigator.locks.request(key, {mode: 'exclusive', ifAvailable: true},
    async (lease) => {
      if (!lease) {
        block('occupied');
        return;
      }
      document.documentElement.dataset.iaminaTabLease = 'holding';
      window.addEventListener('pageshow', event => {
        // A back-forward-cache restore must never revive a runtime whose lease
        // was released on pagehide. A reload reacquires before Flutter starts.
        if (event.persisted) window.location.reload();
      });

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
          const IAMINA_FALLBACK_RELEASE = '0.1.1+2';
      
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
                // A browser policy or headless test may resolve registration with no
                // usable service worker. Never schedule an update on undefined.
                if (!registration || typeof registration.update !== 'function') {
                  console.warn('IAMINA service worker update skipped: no registration');
                  return;
                }
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
      
      // Keep the exclusive Web Lock for the entire lifetime of this page,
      // including background/hidden tabs. Browser destruction releases it.
      await new Promise(resolve => {
        window.addEventListener('pagehide', resolve, {once: true});
      });
    }).catch(() => block('unavailable'));
})();
