// D18 CI ONLY: demonstrate cross-tab/worker Web Locks coordination.
self.onmessage = async event => {
  const name = event.data && event.data.name;
  if (typeof name !== 'string' ||
      !/^amina_vault_v1_device_[0-9a-f]{32}_d18_ci_dynamic$/.test(name)) {
    self.postMessage('INVALID_SCOPE');
    return;
  }
  if (!navigator.locks || typeof navigator.locks.request !== 'function') {
    self.postMessage('UNSUPPORTED');
    return;
  }
  try {
    const acquired = await navigator.locks.request(
      'iamina:d18:ci:v1:' + name,
      {mode:'exclusive',ifAvailable:true},
      lock => Boolean(lock),
    );
    self.postMessage(acquired ? 'ACQUIRED' : 'LOCK_UNAVAILABLE');
  } catch (_) {
    self.postMessage('ERROR');
  }
};
