{{flutter_js}}
{{flutter_build_config}}

_flutter.loader.load();

if ('serviceWorker' in navigator) {
  const IAMINA_FALLBACK_RELEASE = '0.1.0+2';

  const readCurrentIaminaRelease = async () => {
    try {
      const releaseResponse = await fetch(
        `iamina_release.txt?release_probe=${Date.now()}`,
        {
          cache: 'no-store',
          credentials: 'same-origin',
        },
      );
      if (releaseResponse.ok) {
        const release = (await releaseResponse.text()).trim();
        if (/^[A-Za-z0-9._+-]{7,80}$/.test(release)) return release;
      }

      // Transition fallback for clients that still run a bootstrap cached by an
      // older app-shell release. The service-worker marker is intentionally
      // retained so one deploy can migrate those clients to commit-based keys.
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
        // Hosted review builds publish their Git SHA in iamina_release.txt,
        // which changes scriptUrl and deterministically starts the update.
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
