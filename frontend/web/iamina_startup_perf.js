/* IAMINA PERF-WEB: optional local diagnostic, no patient data or network. */
(function () {
  'use strict';
  if (new URLSearchParams(location.search).get('startup_perf') !== '1') return;
  var prefix = 'iamina.startup.';
  var allowed = [
    'main_enter', 'binding_ready', 'firebase_stage_ready', 'auth_ready',
    'legacy_probe_ready', 'scoped_probe_ready', 'lock_ready',
    'locale_refresh_started', 'vault_reconcile_ready', 'runapp_begin',
    'runapp_return', 'vault_binding_begin', 'vault_binding_ready',
    'guest_shell_post_frame', 'patient_shell_post_frame',
    'pending_shell_post_frame', 'unlock_event', 'user_marked_usable'
  ];
  var firstFrame = null;
  addEventListener('flutter-first-frame', function () {
    if (firstFrame === null) firstFrame = Math.round(performance.now());
  }, {once: true});
  function report() {
    var marks = performance.getEntriesByType('mark');
    var seen = {};
    allowed.forEach(function (phase) {
      var match = marks.find(function (m) { return m.name === prefix + phase; });
      if (match) seen[phase] = Math.round(match.startTime);
    });
    var nav = performance.getEntriesByType('navigation')[0];
    return {
      schema: 'iamina-startup-perf-1',
      scope: 'local_only_no_patient_data',
      ttfb_ms: nav ? Math.round(nav.responseStart) : null,
      first_flutter_frame_ms: firstFrame,
      milestone_ms_since_navigation: seen,
      manual_usable_mark_is_upper_bound: true
    };
  }
  function mount() {
    if (document.getElementById('iamina-startup-perf-tool')) return;
    var holder = document.createElement('div');
    holder.id = 'iamina-startup-perf-tool';
    holder.style.cssText = 'position:fixed;right:12px;bottom:max(12px,env(safe-area-inset-bottom));z-index:2147483647;font-family:Arial,sans-serif;';
    var sh = holder.attachShadow({mode:'open'});
    sh.innerHTML = [
      '<style>:host{all:initial;font-family:Arial,sans-serif;color:#102735;}',
      'button{font:600 13px Arial,sans-serif;cursor:pointer;min-height:44px;border:1px solid #246f7e;border-radius:11px;padding:10px 12px;background:white;color:#12323c;}',
      'button:focus-visible{outline:3px solid #e2a42e;outline-offset:2px;}',
      '#toggle{background:#123b48;color:white;border-color:#123b48;box-shadow:0 2px 9px #0003;}',
      '#panel{display:none;background:white;border:1px solid #8aa6ad;border-radius:14px;width:min(342px,calc(100vw - 24px));max-height:60vh;overflow:auto;box-shadow:0 8px 28px #0003;padding:12px;box-sizing:border-box;margin-bottom:8px;}',
      '#panel[open]{display:block;}h2{font:700 16px Arial,sans-serif;margin:0 0 6px;}',
      'p{font:12px/1.4 Arial,sans-serif;margin:0 0 8px;}',
      '#actions{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;}',
      '#quick{display:flex;gap:6px;justify-content:flex-end;}#readyQuick{background:#e6f7f2;color:#0e5746;border-color:#19866c;}',
      'pre{font:11px/1.45 monospace;background:#f3f6f7;border-radius:8px;padding:9px;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;user-select:text;-webkit-user-select:text;}',
      '#status{font:12px Arial,sans-serif;margin-top:6px;min-height:16px;}</style>',
      '<section id="panel" role="dialog" aria-label="Mesure du démarrage IAMINA">',
      '<h2>IAMINA — Démarrage Web</h2>',
      '<p>Horodatages locaux seulement, sans données patient. Le repère « Écran prêt » est manuel.</p>',
      '<div id="actions"><button id="ready">Écran prêt</button><button id="copy">Copier</button>',
      '<button id="refresh">Actualiser</button><button id="close">Fermer</button></div>',
      '<pre id="result" tabindex="0"></pre><p id="status" role="status" aria-live="polite"></p></section>',
      '<div id="quick"><button id="readyQuick" aria-label="Marquer le moment où l’écran est utilisable">✓ Écran prêt</button>',
      '<button id="toggle" aria-label="Ouvrir les chronos IAMINA" aria-expanded="false">⏱ Chrono</button></div>'
    ].join('');
    document.body.appendChild(holder);
    var panel = sh.getElementById('panel');
    var toggle = sh.getElementById('toggle');
    var output = sh.getElementById('result');
    var status = sh.getElementById('status');
    var timer = null;
    function refresh() { output.textContent = JSON.stringify(report(), null, 2); }
    function close() {
      panel.removeAttribute('open');
      toggle.setAttribute('aria-expanded', 'false');
      if (timer !== null) { clearInterval(timer); timer = null; }
      toggle.focus();
    }
    toggle.addEventListener('click', function () {
      if (panel.hasAttribute('open')) { close(); return; }
      panel.setAttribute('open', '');
      toggle.setAttribute('aria-expanded', 'true');
      refresh();
      timer = setInterval(refresh, 900);
    });
    sh.getElementById('close').addEventListener('click', close);
    sh.getElementById('refresh').addEventListener('click', refresh);
    function markUsable() {
      if (!performance.getEntriesByName(prefix + 'user_marked_usable', 'mark').length) {
        performance.mark(prefix + 'user_marked_usable');
      }
      if (panel.hasAttribute('open')) refresh();
      status.textContent = 'Écran prêt : repère manuel enregistré.';
    }
    sh.getElementById('readyQuick').addEventListener('click', markUsable);
    sh.getElementById('ready').addEventListener('click', markUsable);
    sh.getElementById('copy').addEventListener('click', function () {
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        status.textContent = 'Sélectionnez les chiffres pour les copier.';
        output.focus();
        return;
      }
      navigator.clipboard.writeText(JSON.stringify(report(), null, 2)).then(
        function () { status.textContent = 'Chronos copiés.'; },
        function () { status.textContent = 'Sélectionnez les chiffres pour les copier.'; output.focus(); }
      );
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount, {once: true});
  } else {
    mount();
  }
})();
