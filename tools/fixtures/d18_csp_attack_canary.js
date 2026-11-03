// D18 CI-only same-origin external script. It runs in the page's JavaScript
// realm (unlike Playwright page.evaluate) so CSP restricts its eval() call.
(function () {
  'use strict';
  const inline = document.createElement('script');
  inline.textContent = 'window.__d18InlineCanary = true;';
  document.head.appendChild(inline);
  let evalThrows = false;
  let evalErrorName = null;
  try {
    (0, eval)('window.__d18EvalCanary = true;');
  } catch (error) {
    evalThrows = true;
    evalErrorName = error && error.name ? error.name : 'UnknownError';
  }
  window.__d18ExternalCanaryResult = Object.freeze({
    externalScriptLoaded: true,
    inlineExecuted: window.__d18InlineCanary === true,
    evalExecuted: window.__d18EvalCanary === true,
    evalThrows,
    evalErrorName,
  });
})();
